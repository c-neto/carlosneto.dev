---
tags: opensearch, logs, ism, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# One Index, Many Environments: Filtered Alias Views Instead of Per-Environment Indexes

Here is a pattern I reach for constantly when organizing OpenSearch index templates, and it has saved me a lot of cluster overhead and query pain. Instead of creating a separate index per environment (`nginx-dev`, `nginx-stage`, `nginx-production`), I keep one unified index (`nginx`) with an `environment` field, and expose each environment as a filtered alias that points at that single index.

This blog post explains the idea, why I prefer it over per-environment indexes, and how to implement it with a real index template. The result is the best of both worlds: the cluster stores one healthy index instead of a sprawl of tiny ones, but anyone querying in OpenSearch Dashboards still gets a clean, per-environment view that feels exactly like a dedicated index.

## The Problem With One Index Per Environment

The instinct is to give every environment its own index:

```
nginx-dev
nginx-stage
nginx-sandbox
nginx-production
nginx-production-dr
...
```

It feels tidy, but it scales badly:

- __Every index has a footprint, even an empty one__. Each index is made of shards, and each shard is a full Lucene instance consuming heap, file handles, and a slot in the cluster state. A tiny `dev` environment that receives a trickle of logs still costs you shards, cluster-state entries, and allocation decisions, the same per-shard overhead as a busy one. Multiply that across many environments and many log types and the cluster is carrying hundreds of nearly-empty shards for no benefit.
- __Granular indexes fragment your data__. The moment someone wants to query across all environments (or any subset), they have to target multiple indexes with wildcards or comma lists, reconcile differing mappings, and reason about which indexes even exist. Cross-index queries are more complex and easier to get wrong.
- __Small environments waste disk and shards disproportionately__. A 50 MB `dev` index still gets the shard count your template specifies. You end up with many under-filled shards, which is exactly the over-sharding anti-pattern that bloats the cluster.

The data is the same shape in every environment. It is NGINX access and error logs, only the origin differs. That is a strong hint: the environment is not a different kind of data, it is just an attribute of each record.

## The Pattern: One Index, an `environment` Field, and Filtered Aliases

So model it that way. Write every environment's logs into one index, and tag each document with an `environment` field (`dev`, `stage`, `pro`, ...). Then create one filtered alias per environment on top of that single index.

A filtered alias is an alias that carries a built-in query filter. When you read through it, OpenSearch transparently applies the filter, so the alias behaves like an index that contains only the documents matching it. Point `nginx-production` at the single `nginx` index with a filter of `environment: pro`, and querying `nginx-production` returns only production documents, even though physically there is just one index underneath.

```
                        ┌─────────────────────────────┐
  nginx-dev   ───────▶  │                             │  filter environment=dev
  nginx-stage ───────▶  │   single index: nginx-*     │  filter environment=stage
  nginx-pro   ───────▶  │   (one set of shards)       │  filter environment=pro
  nginx-pdr   ───────▶  │                             │  filter environment=pdr
                        └─────────────────────────────┘
```

Each alias is a view, not a copy. There is no data duplication and no extra shards, just one physical index and a handful of lightweight alias definitions.

## Implementing It in an Index Template

Here is the pattern as a real index template. The `aliases` block defines one filtered alias per environment, each pinned to a `term` filter on the `environment` field:

```json
PUT _index_template/nginx-edge
{
  "index_patterns": ["nginx-edge*"],
  "template": {
    "settings": {
      "index.number_of_shards": "4",
      "index.number_of_replicas": "1",
      "index.refresh_interval": "10s",
      "index.routing.allocation.require.temp": "hot",
      "plugins.index_state_management.rollover_alias": "nginx-edge"
    },
    "aliases": {
      "nginx-edge-dev": {
        "is_write_index": false,
        "filter": { "term": { "environment": "dev" } }
      },
      "nginx-edge-stage": {
        "is_write_index": false,
        "filter": { "term": { "environment": "stage" } }
      },
      "nginx-edge-sandbox": {
        "is_write_index": false,
        "filter": { "term": { "environment": "sandbox" } }
      },
      "nginx-edge-pro": {
        "is_write_index": false,
        "filter": { "term": { "environment": "pro" } }
      },
      "nginx-edge-pdr": {
        "is_write_index": false,
        "filter": { "term": { "environment": "pdr" } }
      }
    }
  },
  "composed_of": [
    "settings-default",
    "default-mappings",
    "kubernetes-mappings",
    "nginx-edge-access",
    "nginx-edge-error"
  ]
}
```

A few things worth calling out:

- __`is_write_index: false` on every environment alias__. These aliases are read-only views. You do not write through them. Writes go to the single rollover write alias (below). Each environment alias exists only to filter reads.
- __`filter: { term: { environment: "..." } }`__. This is the whole trick. `term` is an exact-match filter on a keyword field, so `nginx-edge-pro` resolves to "documents in the index where `environment` is exactly `pro`".
- __`plugins.index_state_management.rollover_alias: "nginx-edge"`__. The real write target is a single rollover alias, `nginx-edge`, managed by ISM. All environments write into the same rolling index series (`nginx-edge-000001`, `-000002`, ...).
- __`composed_of`__. Shared mappings and settings come from reusable component templates, so every environment automatically gets identical field mappings. That consistency is a bonus of the single-index approach: you cannot have mapping drift between environments when there is only one mapping.

### The write side

Writes all land in one place. Create the first concrete index with the write alias, exactly as you would for any rollover setup:

```json
PUT nginx-edge-000001
{
  "aliases": {
    "nginx-edge": {
      "is_write_index": true
    }
  }
}
```

Your log shipper writes to `nginx-edge` (the write alias), each document carrying its `environment` field. ISM rolls `nginx-edge` over by size/age as usual. The per-environment filtered aliases ride along automatically because they are defined in the template. Every new rollover index is born with all of them attached.

## Using It From OpenSearch Dashboards

This is where the pattern pays off for the people actually looking at logs. In Dashboards you create an index pattern per environment alias:

- Index pattern `nginx-edge-pro` gives you only production NGINX logs.
- Index pattern `nginx-edge-stage` gives you only staging.
- Index pattern `nginx-edge*` (or the write alias) gives you everything, across all environments, in one place.

To an analyst, `nginx-edge-pro` looks and behaves exactly like a dedicated production index: same fields, same search experience, scoped cleanly to production. They never need to know it is a filtered view. And when someone genuinely needs a cross-environment query ("show me this error across stage and prod"), it is trivial, because the data was never fragmented in the first place. It is one index, optionally filtered.

## Why I Prefer This

| Concern | Per-environment indexes | Unified index + filtered aliases |
| --- | --- | --- |
| Shard / cluster-state footprint | One (or more) shards per environment, even for tiny ones | One index's shards, shared by all environments |
| Small environments | Under-filled shards wasting heap and disk | No dedicated footprint at all, just an alias |
| Cross-environment queries | Wildcards / comma lists across many indexes | Native, it is one index |
| Per-environment view | Natural | Preserved via filtered alias, feels identical |
| Mapping consistency | Can drift between indexes | Impossible to drift, single mapping |
| Rollover / ISM | Must manage a policy per index series | One rollover series to manage |

The pattern removes the cost of granular indexes while keeping the one thing granular indexes gave you that was actually valuable: a clean, scoped, per-environment view.

## When a Separate Index Is Still the Right Call

Filtered aliases are a read convenience over shared physical storage, so use real separate indexes when the environments need genuine physical separation, for example:

- __Hard isolation / access control__. If production and dev must live on different storage tiers, or be access-controlled such that a user can never even touch production shards, a filter is not a security boundary. Use separate indexes.
- __Wildly different retention or sizing__. If production needs 180-day retention on big shards and dev needs 2 days on tiny ones, separate index series with their own ISM policies can be cleaner than one-size-fits-all.
- __Vastly different volume that needs independent scaling__. If one environment is 1000x the others and you want to shard it very differently, splitting it out can be justified.

For the common case, the same log type flowing from several environments, all with similar retention and mappings, the unified index with filtered aliases wins easily.

## Conclusion (Author Opinion)

I reach for this pattern almost reflexively now, because it fixes a problem I used to create for myself: dozens of tiny, nearly-empty indexes that each cost shards and cluster state for no payoff. Modeling the environment as a field instead of an index is the kind of decision that looks trivial and quietly saves you a lot of operational grief later.

That said, it is not a security boundary, and I want to be clear about that. If an environment needs hard isolation, different retention, or independent scaling, give it a real index. For everything else, which is most of the time, one index, one mapping, one rollover series, and as many tidy per-environment views as you need is the setup I recommend.

## References

- <https://opensearch.org/docs/latest/im-plugin/index-alias/>
- <https://opensearch.org/docs/latest/im-plugin/index-templates/>
- <https://opensearch.org/docs/latest/query-dsl/term/term/>

---
tags: opensearch, logs, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# When to Create an OpenSearch Index

I decided to write this post after answering the same question over and over: when should I create a new index? It comes up constantly, and the answers people land on tend to swing between two bad extremes. One index for everything, or a new index for every tiny distinction. I have seen both in the wild, and both hurt.

The worst version I keep running into is a single catch-all index literally named `logs` that absorbs output from completely different tools: web server access logs, application logs, database logs, security events, each with a totally different structure, crammed into one namespace. This is bad. The mappings fight each other (the same field name means different things in different tools, or explodes into hundreds of sparse fields), queries cannot be scoped cleanly, and one noisy source's lifecycle needs are imposed on everything else. A name like `logs` describes the category of data, not a coherent shape of data, and an index should be organized around a coherent shape.

So let's answer the question properly.

First of all, it is necessary to understand what an index is and what it is for in OpenSearch. An index is a logical namespace that holds a collection of documents and their characteristics, like field typing, life cycle, and storage layer definition. It is the unit OpenSearch stores, shards, replicates, ages out, and secures. So deciding to create a new one is not just about "where do I put these documents", it is about committing to a new set of rules for a body of data.

The question this post answers is the one that trips up most people running a log or metrics platform: when do I actually need a new index (and a new index template), and when am I just adding needless sprawl?

## It Depends on Your Needs

New index creation depends on your needs. Sometimes it is interesting to create an index template and a lifecycle policy that produces one index each day. Sometimes it is necessary to create an index based on the characteristics of the data itself: a different log type, a different schema, a different retention.

But every new index has a cost. Each index is made of shards, and each shard is a full Lucene instance that consumes heap, file handles, and a slot in the cluster state, even when it holds almost no data. So the goal is not to create an index for every distinction you can think of. The goal is to create a new index only when the data genuinely needs its own rules, and to reuse an existing index template whenever it does not.

That is why I do not start from "should this be a new index?" I start from "does this data behave differently from what I already have?" If it behaves the same, it belongs with the same template.

## The Four Points I Evaluate Before Creating a New Index

In my experience, four points must be considered when planning the creation of a new index. Each one is a question: does this new data differ from an existing index on this dimension?

### `access permission`

Who is allowed to read and write this data?

If the new data must be visible to a different set of users or roles than an existing index, or must be hidden from users who can currently see that index, it needs to be separable at the index level. Security in OpenSearch is enforced on indexes (and index patterns), not on a filter inside a shared index. If production data must be locked down while development data stays open, a shared index with a filtered view is not a security boundary. That alone justifies a separate index.

If the access rules are identical to an existing index, this point does not push you toward a new one.

### `structure`

What is the shape of the documents, their fields and types?

Documents with the same structure (same fields, same mappings) belong together. If the new data has the same schema as an existing index, it can share that index's template and mappings. If it has a meaningfully different structure (different fields, different types, a different analyzer strategy), forcing it into an existing index causes mapping conflicts and wasted fields, and it deserves its own template.

A useful tell: if two streams are the same kind of data differing only by an attribute (environment, region, tenant), that attribute is usually a field, not a reason for a new index. If they are genuinely different kinds of data, that is a structural difference.

This is exactly where the catch-all `logs` index falls apart. Web server logs, application logs, and database logs are different kinds of data with different schemas. Lumping them under one index forces incompatible mappings into the same namespace. Different structures belong in different indexes (and different templates); the same structure from different sources belongs together.

### `lifecycle`

How long does this data live, and how does it age?

Lifecycle covers rollover conditions, retention, and the ISM policy that drives them. If the new data needs a different retention (2 days vs. 180 days), a different rollover size, or a different aging path, it needs its own lifecycle, and typically its own index series so that ISM can manage it independently. If its lifecycle matches an existing index exactly, it can ride along on the same policy.

### `storage layer`

Where should this data physically live as it ages?

This is the hot / warm / cold (searchable) decision. If the new data should sit on a different storage tier, or move between tiers on a different schedule, than an existing index, that is a storage-layer difference. High-value recent data on fast hot nodes and bulky archival data on cheaper tiers have different storage layers even if everything else about them matches.

## The Decision Rule

Putting the four points together gives a simple rule:

> If all four points are satisfied by an existing index template (same access permissions, same structure, same lifecycle, same storage layer), it is not necessary to plan the creation of a new index template. The data belongs with what you already have, often distinguished by a field, not a new index.
>
> If any point is susceptible to change or genuinely differs, then it may be necessary to create another index template that encodes the new rules.

In other words: a new index template is justified by a difference in behavior, not by a difference in name. Same behavior, same template.

| Point | New index template needed when... |
| --- | --- |
| `access permission` | Different users/roles must be able (or forbidden) to read/write it |
| `structure` | The documents have a meaningfully different schema/mappings |
| `lifecycle` | It needs different rollover conditions, retention, or ISM policy |
| `storage layer` | It should live on, or move through, different storage tiers |

If none of these differ, resist the new index. Add a field and reuse the template.

## Two Quick Examples

Same behavior, reuse the template. NGINX access logs arrive from several environments. Same fields, same retention, same storage tier, same readers. All four points match, so this is one index with an `environment` field, not one index per environment. The environments become filtered alias views, not separate indexes.

Different behavior, new template. Application debug logs and application audit logs look superficially similar, but audit logs must be readable only by a compliance role (`access permission` differs) and kept for a year on a cheaper tier (`lifecycle` and `storage layer` differ). Those differences justify a separate index template with its own policy and allocation rules.

## Conclusion (Author Opinion)

I have been running log platforms long enough to see both failure modes play out, and the four-point check is what I keep coming back to because it stops me from guessing. The honest truth is that most of the time the answer is "reuse the template and add a field", and people are surprised by that, because creating a new index feels tidy and organized. It is not. It is sprawl with a nice name.

My recommendation: default to reuse, and let a real difference in behavior earn the new index. Every case is unique, so run your data through the four points before you commit. If none of them push you toward a new index, you already have your answer.

## References

- <https://opensearch.org/docs/latest/im-plugin/index/>
- <https://opensearch.org/docs/latest/security/access-control/index/>
- <https://opensearch.org/docs/latest/im-plugin/ism/index/>

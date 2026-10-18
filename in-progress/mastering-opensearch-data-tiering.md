---
tags: opensearch, ism, aws, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# OpenSearch Data Tiering: A Hands-On Guide to Hot, Warm, and Searchable Tiers

Logs and time-series data share an inconvenient truth: the newest data is queried constantly, and the oldest data is almost never touched, but you still have to keep it. If you store everything on the same fast (and expensive) hardware, you burn money. If you store everything on slow, cheap hardware, your dashboards crawl.

Data tiering solves this. You split your cluster into tiers with different cost and performance profiles and let indexes flow automatically from the fast tier to progressively cheaper ones as they age. This blog post is hands-on: by the end you will have a working hot to warm to searchable architecture driven entirely by an OpenSearch Index State Management (ISM) policy.

## The Three Tiers

Here is the mental model we will implement:

| Tier | Hardware profile | Role | Typical retention |
| --- | --- | --- | --- |
| Hot | Fast local NVMe, high CPU, limited capacity | Active indexing and near-real-time search | First few days |
| Warm | Large network-attached disk (EBS), lower CPU | Long-term retention, slower queries | Weeks to months |
| Searchable (cold) | On-demand nodes backed by object storage (S3) | Rarely-queried data, restored on demand | Months to years |

The data flows one direction: freshly ingested logs land on hot, roll over and migrate to warm after a few days, get snapshotted to object storage, and are eventually either deleted or kept as searchable snapshots that are only pulled back into compute when someone actually queries them.

The whole point is that each tier matches the access pattern of the data it holds. You are provisioning expensive, high-performance resources only for the small slice of data that needs them.

## Prerequisites: Labeling Your Nodes

Tiering is driven by node attributes. You tag each data node with a custom attribute (conventionally `temp`) so that OpenSearch knows which nodes are hot and which are warm.

In each node's `opensearch.yml` (or via the environment, if you run in containers):

```yml
# On every hot data node
node.attr.temp: hot
```

```yml
# On every warm data node
node.attr.temp: warm
```

The attribute name is arbitrary. `temp` is just a convention. What matters is that it is consistent across the cluster. OpenSearch will use it later to pin shards to the right tier.

For the searchable (cold) tier, you will need at least one node configured with the `warm` node role, which is what enables remote-backed searchable snapshots:

```yml
node.roles: [ data, warm ]
```

> <i class="fa-solid fa-circle-info"></i> **About the naming overlap:**
>
> The `warm` node role is specifically the OpenSearch feature that powers searchable snapshots. It is distinct from the custom `node.attr.temp: warm` attribute we use for the EBS warm tier. In many real deployments these are separate node groups.

## Step 1: Set Up Shard Allocation Awareness

Before moving data around, make sure replicas are spread across failure domains (availability zones). This is independent of tiering but essential: you do not want a primary and its replica on the same AZ.

```json
PUT _cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "zone"
  }
}
```

With this in place, OpenSearch keeps copies of a shard in different zones, so losing a zone never loses data.

## Step 2: Pin New Indexes to the Hot Tier

You want every freshly created index to land on hot nodes. The mechanism is a shard allocation filter on the index settings:

```json
PUT my-logs-000001
{
  "settings": {
    "index.routing.allocation.require.temp": "hot"
  }
}
```

The `require` filter means shards may only be placed on nodes whose `temp` attribute equals `hot`. You can verify where the shards actually landed:

```bash
GET _cat/shards/my-logs-000001?v
```

In practice you do not set this per-index by hand. You bake it into an index template so every index matching a pattern inherits it automatically. More on that in Step 4.

## Step 3: Understand the ISM State Machine

The engine behind automatic tiering is Index State Management (ISM). An ISM policy is a small state machine with three building blocks:

- __State__: a status the index can be in (`hot`, `warm`, `delete`). An index is in exactly one state at a time.
- __Action__: an operation run when the index enters a state (`rollover`, `snapshot`, `replica_count`, `allocation`, `delete`). Actions run in the order you declare them.
- __Transition__: the condition that moves the index to the next state (for example, reaching a minimum age).

Once a policy is attached, ISM runs a background job every 5 minutes: it executes the current state's actions, evaluates the transition conditions, and advances the index when they are met.

## Step 4: Write the Tiering Policy

Here is a complete hot to warm to delete policy. We will walk through each state afterward.

```json
PUT _plugins/_ism/policies/logs_tiering_policy
{
  "policy": {
    "description": "Hot -> Warm -> Delete lifecycle for time-series logs",
    "default_state": "hot",
    "states": [
      {
        "name": "hot",
        "actions": [
          {
            "rollover": {
              "min_index_age": "3d",
              "min_primary_shard_size": "50gb"
            }
          }
        ],
        "transitions": [
          {
            "state_name": "warm"
          }
        ]
      },
      {
        "name": "warm",
        "actions": [
          {
            "replica_count": {
              "number_of_replicas": 1
            }
          },
          {
            "allocation": {
              "require": { "temp": "warm" }
            }
          }
        ],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "180d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ]
      }
    ],
    "ism_template": {
      "index_patterns": ["my-logs-*"],
      "priority": 100
    }
  }
}
```

What each state does:

- __`hot`__: the index starts here. The `rollover` action closes the current write index and opens a fresh one once it is 3 days old or its primary shard reaches 50 GB (whichever comes first). After rollover, the index transitions to `warm`.
- __`warm`__: two actions run in order. First, `replica_count` drops replicas to 1 (older data needs less redundancy headroom, saving disk). Second, `allocation` with `require: { temp: warm }` tells OpenSearch to relocate the shards onto warm (EBS) nodes. The index stays here until it is 180 days old.
- __`delete`__: after 180 days, the index is permanently deleted.

The `ism_template` block at the bottom auto-attaches this policy to any index matching `my-logs-*` with priority 100, so you never have to attach it manually.

## Step 5: Wire Up Rollover with an Alias

The `rollover` action needs a write alias to flip between the current and the next index. Define it in an index template, create the first index, and point the alias at it:

```json
PUT _index_template/my-logs-template
{
  "index_patterns": ["my-logs-*"],
  "template": {
    "settings": {
      "index.routing.allocation.require.temp": "hot",
      "plugins.index_state_management.rollover_alias": "my-logs"
    }
  }
}
```

```json
PUT my-logs-000001
{
  "aliases": {
    "my-logs": {
      "is_write_index": true
    }
  }
}
```

Now your application writes to the `my-logs` alias, never to a specific index. When the hot-state rollover fires, OpenSearch creates `my-logs-000002`, moves the write alias to it, and the ISM policy begins managing the old index's journey to warm.

Confirm the policy attached correctly:

```json
GET _plugins/_ism/explain/my-logs-000001?pretty
```

## Step 6: Add the Searchable (Cold) Tier

So far we delete at 180 days. But often you must keep old data for compliance while still freeing up warm nodes. Searchable snapshots are the answer: the index data lives in object storage (S3), and compute is only attached when someone queries it.

First, register a snapshot repository backed by S3 (one-time setup):

```json
PUT _snapshot/logs-s3-repository
{
  "type": "s3",
  "settings": {
    "bucket": "my-opensearch-snapshots",
    "base_path": "logs"
  }
}
```

Have ISM snapshot the index as part of (or just before) the warm state by adding a `snapshot` action:

```json
{
  "name": "warm",
  "actions": [
    { "replica_count": { "number_of_replicas": 1 } },
    { "allocation": { "require": { "temp": "warm" } } },
    {
      "snapshot": {
        "repository": "logs-s3-repository",
        "snapshot": "{{ctx.index}}"
      }
    }
  ],
  "transitions": [ ]
}
```

Once an index is snapshotted and later removed from the cluster, you can bring it back on demand as a searchable snapshot. The metadata is loaded into the cluster, but S3 remains the authoritative data store, and segments are cached locally only as queries need them:

```json
POST /_snapshot/logs-s3-repository/my-logs-000001/_restore
{
  "storage_type": "remote_snapshot",
  "indices": "my-logs-000001"
}
```

The `storage_type: remote_snapshot` is the key difference from a normal restore. Instead of downloading the entire index to local disk, OpenSearch streams and caches data from S3 as queries hit it. This requires at least one node with the `warm` node role (from the prerequisites). These search nodes can be spun up on demand and torn down when the investigation is over, so you only pay for the compute while someone is actually looking at old data.

## How the Pieces Fit Together

Putting the full lifecycle in one picture:

1. Application writes to the `my-logs` alias. Data lands on hot NVMe nodes for fast indexing and near-real-time search.
2. After 3 days (or 50 GB), ISM rolls over the index and transitions it to the warm state.
3. In the warm state, replicas drop to 1, shards relocate to warm EBS nodes, and a snapshot is pushed to S3.
4. The index serves slower queries from warm nodes for up to 180 days.
5. At 180 days, the index is either deleted or, if you need long retention, left as a snapshot in S3 to be restored on demand as a searchable snapshot on temporary search nodes.

Each hop matches hardware cost to how often the data is actually touched.

## Operational Tips

- __Watch the transitions.__ Use `GET _plugins/_ism/explain/<index>` to see which state each managed index is in and why it has not transitioned yet.
- __Monitor shard movement during relocation.__ When indexes migrate from hot to warm, `GET _cat/shards?v&s=state` shows `RELOCATING` shards. Large migrations consume I/O and network, so expect them, and schedule heavy retention changes off-peak.
- __Size your rollover thresholds to your shards, not the calendar alone.__ A 50 GB primary-shard cap keeps shards in a healthy size range regardless of traffic spikes. Combine it with an age condition so quiet indexes still roll over.
- __Keep at least one replica on hot.__ The hot tier is where you can least afford data loss, especially if it runs on ephemeral local NVMe. Only drop to zero replicas on tiers where you can tolerate a re-restore from snapshot.
- __ISM pauses on red.__ ISM does not run jobs while the cluster health is red. If transitions seem stuck, check cluster health first.

## Conclusion (Author Opinion)

Data tiering is one of those setups that feels like a lot of moving parts the first time you wire it, and then pays you back every single month afterward. Once the ISM policy is in place, the cluster manages its own storage economics: new data stays fast, old data gets cheap, and you stop paying premium prices to store logs nobody is reading.

The numbers here (3 days hot, 180 days retention, 50 GB rollover) are not universal. They are a starting point, and every workload is different, so tune them to your own access patterns. What I will recommend without hesitation is the discipline itself: match each tier to how often its data is actually touched, set it up once, and let ISM do the rest.

## References

- <https://opensearch.org/docs/latest/im-plugin/ism/index/>
- <https://opensearch.org/docs/latest/tuning-your-cluster/availability-and-recovery/snapshots/searchable_snapshot/>
- <https://opensearch.org/docs/latest/tuning-your-cluster/cluster/>

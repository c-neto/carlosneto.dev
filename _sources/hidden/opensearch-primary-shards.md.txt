---
tags: opensearch, performance, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# Tuning OpenSearch Shards: Align Primary Shards to Your Data Nodes

There is one configuration decision that quietly caps your OpenSearch cluster's throughput more than almost any other: the number of primary shards per index. Set it too low and most of your nodes sit idle while a handful do all the work. Set it too high and you drown the cluster in overhead.

This blog post explains how shards drive parallelism, why a mismatch between shard count and node count becomes a bottleneck, and the trade-offs of running many shards per index. It ends with a concrete procedure I use for retuning shard counts on a live cluster.

## Shards Are the Unit of Parallelism

An OpenSearch index is split into shards, and each shard is a complete, independent Lucene index: a real running process that consumes its own CPU and memory. OpenSearch distributes shards across data nodes so that:

- Indexing is spread out. Incoming documents are routed to different primary shards living on different nodes, so multiple nodes write in parallel.
- Search is spread out. A query fans out to every shard, each shard searches its slice of the data concurrently, and the results are merged.

This is the key mental model: a shard can only ever live on one node at a time, and work for that shard happens on that one node. The number of primary shards therefore sets a hard ceiling on how many nodes can simultaneously work on a single index.

## The Bottleneck: Fewer Primary Shards Than Nodes

Suppose you have a 12-node hot tier but create an index with only 3 primary shards.

Those 3 primaries can land on at most 3 nodes. The other 9 nodes hold nothing for that index. When you index into it, only 3 nodes do the writing. When you query it, only 3 nodes do the searching. You bought 12 nodes of capacity and you are using a quarter of it.

This is the classic sharding bottleneck:

> If an index has fewer primary shards than you have data nodes, the extra nodes cannot help with that index. Your indexing and search throughput is capped by the handful of nodes that happen to host the primaries, no matter how much hardware you add.

Adding replicas does not fix the write bottleneck. Replicas help search throughput (a search can be served by either a primary or a replica), and they provide redundancy, but all writes still go to the primary first. If writes are your bottleneck, you need more primaries, spread across more nodes.

The fix is to make the primary shard count a multiple of (or at least equal to) your data node count, so every node gets a fair share of the write and search load. With 12 hot nodes, 12 primary shards means every node hosts exactly one primary and participates fully.

## The Other Extreme: Too Many Shards

If more shards means more parallelism, why not create hundreds of them? Because every shard has a cost.

Each shard is a full Lucene instance. It consumes:

- __Heap memory__ for segment metadata, field data, and caches, held on every node hosting the shard.
- __File handles and threads__: each Lucene index maintains open files and background merge threads.
- __Cluster-state overhead__: the cluster manager tracks every shard, so thousands of tiny shards bloat the cluster state and slow down every allocation decision.
- __Per-query fan-out cost__: a search touches every shard. More shards means more sub-requests to coordinate and merge, which adds CPU and latency even when each shard holds very little data.

The OpenSearch guidance is blunt: more shards is not necessarily better. Splitting a 400 GB index into 1,000 shards would needlessly strain the cluster. The widely-used rule of thumb is to keep each shard in the 10 to 50 GB range.

So you are balancing two forces:

| Too few primary shards | Too many primary shards |
| --- | --- |
| Idle nodes, under-utilized hardware | Wasted heap and file handles |
| Write throughput capped by a few nodes | Slow cluster-state updates |
| No parallelism headroom | Expensive query fan-out |
| Huge shards (>50 GB) that merge slowly | Tiny shards with poor compression and overhead |

## Advantages and Disadvantages of a High Primary Shard Count

Advantages of more primary shards:

- Higher write parallelism, more nodes accept writes simultaneously.
- Higher search parallelism, each shard searches a smaller slice concurrently.
- Smaller individual shards that merge, relocate, and recover faster.
- Room to scale: when you add nodes, OpenSearch can rebalance existing shards onto them.

Disadvantages of too many primary shards:

- Memory and thread overhead per shard multiplies across the cluster.
- Cluster-state management slows down as shard count grows into the thousands.
- Query coordination overhead rises, each search must fan out to and merge from every shard.
- Shards that are too small waste resources and hurt compression efficiency.

The sweet spot is enough primaries to use every data node, with each shard sized in the 10 to 50 GB band. Match the parallelism to your hardware, do not exceed it.

## How to Size It

A practical sizing procedure:

1. Estimate the index's steady-state size (per rollover window if you use time-based indexes). Say an index will hold 480 GB.
2. Divide by the target shard size to get a shard count. At 40 GB/shard: `480 / 40 = 12` shards.
3. Reconcile with node count. If you have 12 hot nodes, 12 primaries is perfect, one per node. If the math gave you 5 shards but you have 12 nodes, consider bumping to a multiple of your node count (or at least closer to it) so nodes are not left idle, as long as each shard stays above roughly 10 GB.
4. Decide replicas based on your durability and search needs, keeping in mind replicas also occupy nodes and disk.

The goal is to find the number where shard size stays healthy (10 to 50 GB) and every data node hosts at least one primary.

## Hands-On: Retuning Shard Counts on a Live Cluster

You cannot change the primary shard count of an existing index in place. Primaries are fixed at creation. For time-based indexes, the clean way to apply a new shard count is to update the index template and roll over, so the next index is created with the new settings.

### Approach 1: Right-size with replicas for durability

Set a shard count that matches your nodes, keeping one replica for safety:

```json
PUT _template/pro-log-app
{
  "order": 80,
  "index_patterns": ["pro-log-app*"],
  "settings": {
    "index.number_of_shards": "6",
    "index.number_of_replicas": "1",
    "index.refresh_interval": "10s",
    "index.routing.allocation.require.temp": "hot",
    "plugins.index_state_management.rollover_alias": "pro-log-app"
  }
}
```

Then trigger a rollover so a fresh write index picks up the new template:

```json
POST /pro-log-app/_rollover
```

With 6 shards plus 1 replica, you get 12 total shard copies, a natural fit for a 12-node hot tier, and search requests can be served by either primaries or replicas.

### Approach 2: Maximize ingestion parallelism, drop replicas

When you need to push the highest possible indexing throughput during a peak event (and can briefly tolerate the reduced redundancy), set one primary per node and remove replicas so every node spends all its I/O on primary writes:

```json
PUT _index_template/pro-log-app-trace
{
  "order": 80,
  "index_patterns": ["pro-log-app-trace*"],
  "settings": {
    "index.number_of_shards": "12",
    "index.number_of_replicas": "0",
    "index.refresh_interval": "10s",
    "index.routing.allocation.require.temp": "hot",
    "plugins.index_state_management.rollover_alias": "pro-log-app-trace"
  }
}
```

Roll over each managed index so the new settings take effect:

```json
POST pro-log-app-trace/_rollover
```

With 12 primaries and 0 replicas on a 12-node tier, every node drives one primary at full write speed. This is a deliberate trade: you maximize ingest throughput at the cost of redundancy, so reserve it for well-understood, high-volume bursts, and restore replicas afterward.

> <i class="fa-solid fa-circle-info"></i> **About `refresh_interval`:**
>
> During heavy indexing, raising the refresh interval (here, `10s`) reduces how often shards build new searchable segments, freeing I/O for writes. It is a complementary lever to sharding when tuning for ingestion.

## Verifying Your Work

After rolling over, confirm the shards landed the way you expect: one primary per node, nothing unassigned.

```bash
# Shard layout for the new index: check prirep, state, and node columns
GET _cat/shards/pro-log-app-trace-000002?v&s=node

# Node list: confirm every data node is present
GET _cat/nodes?v&s=name

# Cluster health: must be green (or yellow if you intentionally dropped replicas)
GET _cluster/health
```

You want to see primaries evenly spread with no idle data nodes and no `UNASSIGNED` shards (except intentionally-removed replicas).

## Conclusion (Author Opinion)

Of all the OpenSearch tunings I have applied, aligning primary shards to data nodes is the one with the best effort-to-payoff ratio. It is a single number, and getting it right is often the difference between a cluster that uses the hardware you pay for and one that leaves most of it idle.

The honest caveat is that this is not a one-time decision. Every time you add nodes or your data volume shifts, the math changes, and you cannot reshard in place, so you plan for it at template-and-rollover time. My recommendation: size your shards to land in the 10 to 50 GB band, make the primary count track your node count, and revisit it whenever the cluster grows. A cluster whose shard count tracks its node count is a cluster that actually earns its bill.

## References

- <https://opensearch.org/docs/latest/im-plugin/index-settings/>
- <https://opensearch.org/docs/latest/tuning-your-cluster/>
- <https://opensearch.org/docs/latest/api-reference/cat/cat-shards/>

---
tags: opensearch
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# OpenSearch: How to Speed Up Cluster Allocation

This blog post explains how to make shard allocation faster in OpenSearch when you are decommissioning a node or moving data from one node to another. It covers three dynamic cluster settings that control the speed of that process, what each one does, and the trade-off you accept when you raise them.

## The Problem: Draining a Node Takes Forever

Picture the scenario. You need to remove a data node from the cluster, maybe to replace the instance, scale down, or recover from a problem. In OpenSearch you do that by excluding the node from allocation, which tells the cluster to move every shard off it onto the remaining nodes:

```bash
PUT _cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._name": "node-to-remove"
  }
}
```

The cluster starts relocating shards. Then you wait. On a cluster with a lot of data, draining a single node can take hours, because by default OpenSearch is deliberately conservative about how much it moves at once. That caution protects a busy cluster from choking on recovery traffic, but during a planned maintenance window it is just slow.

The good news is that the throttling is controlled by a handful of dynamic settings. You can turn them up to drain faster, then put them back. If you want a refresher on what shards are before diving in, I wrote about it in [OpenSearch Concepts - Index and Shards](https://carlosneto.dev/blog/2025/2025-01-05-opensearch-concepts-index-and-shards).

## The Three Settings That Control Allocation Speed

Shard relocation has two bottlenecks: how many shards move in parallel, and how fast each one transfers. These three settings address both.

### cluster.routing.allocation.node_concurrent_recoveries

This controls how many concurrent shard recoveries are allowed on a single node, counting both incoming and outgoing. The default is `2`, which means a node that is being drained only pushes two shards out at a time, and a node receiving data only pulls two in at a time.

It is a convenience setting that sets the incoming and outgoing limits to the same value. Raising it lets more shards move in and out of each node simultaneously, which is usually the single biggest lever when draining a node.

### cluster.routing.allocation.cluster_concurrent_rebalance

This controls how many concurrent shard rebalances are allowed across the whole cluster at once. The default is also `2`. Where the previous setting is per node, this one is a global cap on rebalancing moves.

When you drain a node, the cluster rebalances shards to even out the load, and this setting caps how many of those moves happen in parallel cluster-wide. Raising it lets the cluster coordinate more relocations at the same time.

### indices.recovery.max_bytes_per_sec

The two settings above control how many shards move at once. This one controls how fast each transfer is allowed to go. It limits the total inbound and outbound recovery traffic per node, and the default is `40mb` per second.

On modern hardware with fast disks and a fast network, 40 MB/s is often the real bottleneck, not the concurrency. If your nodes and network can handle more, raising this lets each shard transfer saturate the available bandwidth instead of being artificially capped.

## Putting It Together

Before draining a node, bump the three settings so the cluster moves more shards at once and each one moves faster:

```bash
PUT _cluster/settings
{
  "transient": {
    "cluster.routing.allocation.node_concurrent_recoveries": 10,
    "cluster.routing.allocation.cluster_concurrent_rebalance": 10,
    "indices.recovery.max_bytes_per_sec": "200mb"
  }
}
```

I used `transient` on purpose. Transient settings are cleared on a full cluster restart, so they are a good fit for a temporary change during a maintenance window. Use `persistent` if you want the values to survive restarts.

While the relocation runs, watch the progress with the `_cat` APIs:

```bash
# shards currently relocating, and from/to which node
GET _cat/recovery?v&active_only=true

# cluster health, including the number of relocating shards
GET _cluster/health
```

When the node is empty and you are done, put the settings back to their defaults so normal cluster activity is not competing with aggressive recovery traffic:

```bash
PUT _cluster/settings
{
  "transient": {
    "cluster.routing.allocation.node_concurrent_recoveries": null,
    "cluster.routing.allocation.cluster_concurrent_rebalance": null,
    "indices.recovery.max_bytes_per_sec": null
  }
}
```

Setting a value to `null` resets it to the default.

## Mind the Trade-Off

These settings are throttles for a reason, so turning them up is not free. More concurrent recoveries and higher bandwidth mean more CPU, disk I/O, and network pressure on every node involved. If you push too hard on a cluster that is also serving production traffic, you can slow down indexing and searches for your users, which defeats the purpose.

My rule is to be aggressive during a dedicated maintenance window when the cluster is quiet, and conservative when real traffic is on the line. Raise the values gradually and keep an eye on node CPU and disk I/O while the relocation runs. If latency starts climbing, back off. There is no universal magic number, because the right value depends entirely on your hardware and how busy the cluster is.

## Conclusion (Author Opinion)

The first time I had to drain a node on a large cluster, I assumed it was stuck, because the default pace is so slow it looks frozen. Once I understood that OpenSearch is just being cautious, these three settings turned an all-day chore into something that finishes while I grab a coffee.

I treat them as a maintenance toolkit: raise `node_concurrent_recoveries` and `cluster_concurrent_rebalance` to move more shards at once, raise `indices.recovery.max_bytes_per_sec` to move each one faster, do the work, then reset everything. Just respect the trade-off and watch your cluster while it runs. Used carefully, they make node decommissioning and data migration a lot faster.

## References

- <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/>
- <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings-for-indexes/>
- <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/availability-recovery/>

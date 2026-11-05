---
tags: opensearch
date: "2026-11-04"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/11/04*

---

# OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks

This post looks at how OpenSearch distributes shards across data nodes. I'll cover how the default allocation strategy works, why it can lead to uneven disk usage in clusters with many small indices, and how disk watermarks help address that. I'll also discuss other allocation mechanisms and a limitation in the watermark design: it's a cluster-wide setting, even in clusters with different storage tiers.

## Why Shard Balance Matters

Data nodes need enough free disk space to accommodate new shards as indices are created and existing data grows. This is especially relevant in OpenSearch because Lucene shards allow an index to be split across multiple nodes. Each shard handles part of the data, allowing indexing and search operations to run across the cluster.

For this design to work well, data nodes need available capacity for new shard allocations. If most of the free space is concentrated on a few nodes, the cluster may struggle to allocate new shards even when there is plenty of storage available elsewhere.

## How OpenSearch Balances Shards Across Data Nodes

OpenSearch's default shard allocator, [`BalancedShardsAllocator.java`](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java), uses a weighted balancing model. It considers both the total number of shards per node and how shards from each index are distributed across the nodes.

The default weights are controlled by `cluster.routing.allocation.balance.shard` and `cluster.routing.allocation.balance.index`. Their default values are `0.45` and `0.55`, respectively. You can find these settings in the [OpenSearch cluster management documentation](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/).

Shard size, however, is not a direct factor in this balancing model. As a result, two nodes can have a similar number of shards while consuming very different amounts of disk space.

This can lead to unexpected results in production, especially in clusters with many small, granular indices. A node might hold dozens of tiny shards and use very little disk space, while another holds only a few large shards and is almost full. The shard distribution may look balanced, but disk usage tells a different story.

The allocator also works alongside other allocation deciders. These evaluate whether a shard can be allocated to a particular node. For example:

- `disk_threshold`: checks whether the node has enough available disk space, based on the configured watermarks.
- `filter`: enforces allocation rules based on node attributes.
- `awareness`: helps distribute shard copies across failure domains, such as availability zones.
- `same_shard`: prevents multiple copies of the same shard from being allocated to the same node.
- `shards_limit`: enforces configured shard limits per node.

These deciders can prevent an allocation even when it would improve shard balance. The allocator determines where shards should ideally go, while the deciders evaluate whether those allocations are allowed.

> _See <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/> to investigate these decisions. It shows which deciders allowed or rejected an allocation and provides explanations for their decisions._

## Other Shard Allocation Mechanisms

The default allocator is not the only mechanism that influences shard placement. OpenSearch provides additional allocation settings and APIs, although they do not all replace the default balancing strategy.

---

__Load-Aware Allocation__: Limits shard concentration when cluster capacity is reduced.

Despite its name, Load-Aware Allocation does not monitor CPU utilization, memory usage, disk utilization, or indexing and search throughput to decide where shards should be allocated. Its purpose is more specific: to prevent surviving nodes from becoming overloaded with shards when the cluster loses nodes or operates below its provisioned capacity.

For example, consider a cluster designed to run with 10 data nodes. If four nodes fail, the remaining six nodes may receive additional shards during recovery. Without an allocation limit, they could end up holding significantly more shards than originally intended. 

Load-Aware Allocation helps control this situation by considering the cluster's provisioned capacity and the number of shards assigned to each node. It uses three main settings:

- `cluster.routing.allocation.load_awareness.provisioned_capacity`: the number of nodes the cluster is provisioned to run. Its default value is `-1`, which disables this allocation control.
- `cluster.routing.allocation.load_awareness.skew_factor`: the percentage of shard-count imbalance allowed between nodes. Its default value is `50`.
- `cluster.routing.allocation.load_awareness.flat_skew`: an additional absolute allowance for shard-count imbalance. Its default value is `2`.

The provisioned capacity must be updated when the cluster scales up or down. Otherwise, the allocation limits may not reflect the cluster's intended capacity.

There is also an important setting called `cluster.routing.allocation.load_awareness.allow_unassigned_primaries`. It defaults to `true`, allowing newly created primary shards to be allocated even if doing so exceeds the configured skew limit. Setting it to `false` can leave primary shards unassigned and cause the cluster to turn red.

This mechanism is implemented by [`NodeLoadAwareAllocationDecider.java`](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/decider/NodeLoadAwareAllocationDecider.java). Its implementation calculates an allowed shard count per node using the total number of shards, provisioned capacity, skew factor, and flat skew.

In short, Load-Aware Allocation is about controlling shard concentration when cluster capacity is reduced, not balancing shards according to the actual CPU or memory resources available on each node. It complements the default allocator and does not replace it with a resource-aware or size-based balancing strategy.

> _For more details, see <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/>_

---

__Manual Shard Allocation__: Allows administrators to manually move shards between nodes.

The [Cluster Reroute API](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/) allows administrators to manually move shards between nodes, among other operations. This can be useful for operational tasks or specific rebalancing scenarios, but it does not change the default allocation strategy or provide automatic size-based balancing.

## Balancing by Size: Disk Watermarks

So how does OpenSearch account for disk usage? That's where __disk watermarks__ come in. Watermark settings control shard allocation based on the percentage or absolute amount of disk space available on each node. They use three thresholds:

- `cluster.routing.allocation.disk.watermark.low`: when a node crosses this threshold, OpenSearch generally stops allocating new shards to it. One exception is primary shards of newly created indices. Existing shards remain in place.
- `cluster.routing.allocation.disk.watermark.high`: when a node crosses this threshold, OpenSearch attempts to relocate shards to other nodes with more available disk space.
- `cluster.routing.allocation.disk.watermark.flood_stage`: the last line of defense. When a node crosses this threshold, OpenSearch applies a read-only block to indices with shards on that node to prevent the disk from filling completely.

Watermarks bring disk usage into shard allocation decisions. The default allocator balances shard distribution using shard counts and index distribution, while disk watermarks react to disk pressure and can trigger allocation changes when nodes get too full.

> _For more details, see <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/>._

## Watermark Limitation: One Setting For All Storage Tiers

There is one limitation in the watermark design that I find particularly frustrating: __watermarks are global cluster settings__. You configure them once, and the same thresholds apply to every node, regardless of its storage tier.

This becomes a problem in tiered clusters with hot, warm, and searchable nodes. Each tier has a different storage profile and a different cost per gigabyte. For example, a watermark that works well for warm nodes, where you want to use disk capacity efficiently before relocating shards, might be too aggressive for hot nodes. Hot nodes need more free space to handle indexing and query workloads. Yet OpenSearch gives you no way to configure different watermark thresholds for each tier.

I'd like to see per-tier watermark configuration in OpenSearch. Until that happens, we're stuck with a single set of thresholds for the entire cluster. Keep this in mind when designing tiered clusters, because whatever values you choose will be a compromise across all storage tiers.

## References

- BalancedShardsAllocator.java: <https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java>
- NodeLoadAwareAllocationDecider.java: <https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/decider/NodeLoadAwareAllocationDecider.java>
- OpenSearch Cluster Management Settings: <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/>
- Cluster Settings API: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-settings/>
- Cluster Allocation Explain API: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/>
- Shard Allocation Filtering: <https://docs.opensearch.org/latest/api-reference/index-apis/shard-allocation/>
- Cluster Reroute API: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/>
- ShardsAllocator Interface (OpenSearch source code): <https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/ShardsAllocator.java>

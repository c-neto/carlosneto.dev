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

When shard allocation fails, the cluster can enter a yellow or red state, potentially resulting in data loss. Thus, a solid understanding of shard allocation can help protect cluster availability. The [`GET /_cluster/allocation/explain`](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/) endpoint is a useful way to investigate why a shard was allocated to a particular node or why an allocation or rebalance was rejected.

## How OpenSearch Balances Shards Across Data Nodes

OpenSearch's default shard allocator, [`BalancedShardsAllocator.java`](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java), uses a weighted balancing model. It considers both the total number of shards per node and how shards from each index are distributed across the nodes. The default weights are controlled by [`cluster.routing.allocation.balance.shard`](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/) and [`cluster.routing.allocation.balance.index`](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/). Their default values are `0.45` and `0.55`, respectively.

Shard size, however, is not a direct factor in this balancing model. As a result, two nodes can have a similar number of shards while consuming very different amounts of disk space. This can lead to unexpected results in production, especially in clusters with many small, granular indices. A node might hold dozens of tiny shards and use very little disk space, while another holds only a few large shards and is almost full. The shard distribution may look balanced, but disk usage tells a different story.

The allocation process also considers other constraints that influence shard placement. These include disk availability, allocation filters, awareness across availability zones or racks, and limits on the number of shards per node. These mechanisms can prevent an allocation even when it would improve shard balance.

For an overview of the available allocation deciders and their roles, see the _Common Allocators_ section in the OpenSearch documentation: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/#common-allocators>

## Other Shard Allocation Mechanisms

The default allocator is not the only mechanism that influences shard placement. OpenSearch provides additional allocation settings and APIs, although they do not all replace the default balancing strategy.

---

__Load-Aware Allocation__: Limits shard concentration when cluster capacity is reduced, such as when data nodes fail. For example, consider a cluster designed to run with 10 data nodes. If 4 nodes fail, the remaining 6 may receive additional shards during recovery, increasing their shard counts.

The following configuration tells OpenSearch that the cluster is provisioned for 10 nodes and defines how much shard-count imbalance is allowed:

```yaml
# >>> https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/
cluster.routing.allocation.load_awareness.provisioned_capacity: 10
cluster.routing.allocation.load_awareness.skew_factor: 50
cluster.routing.allocation.load_awareness.flat_skew: 2
cluster.routing.allocation.load_awareness.allow_unassigned_primaries: true
```

Even with only 6 nodes available, `provisioned_capacity` remains set to `10`, representing the cluster's intended capacity. The `skew_factor` allows a 50% deviation from the expected shard distribution, while `flat_skew` adds an allowance of 2 shards. Together, these settings determine when a node has too many shards to receive additional allocations.

The provisioned capacity must be updated whenever the cluster scales. The `allow_unassigned_primaries` setting controls whether new primary shards can still be allocated when the skew limit is exceeded.

See the [NodeLoadAwareAllocationDecider.java](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/decider/NodeLoadAwareAllocationDecider.java) implementation for details.

---

__Manual Shard Allocation__: Allows administrators to manually move shards between nodes. The [Cluster Reroute API](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/) allows administrators to manually move shards between nodes, among other operations. This can be useful for operational tasks or specific rebalancing scenarios, but it does not change the default allocation strategy or provide automatic size-based balancing.

## Balancing by Size: Disk Watermarks

OpenSearch uses three disk watermarks to control shard allocation based on disk usage: `low`, `high`, and `flood_stage`. Each one defines a threshold that triggers a different action.

Watermarks accept percentage-based values or absolute disk space values. Percentages are calculated relative to each node's total disk capacity. For example, consider a node with 1 TB of storage and the following configuration:

```yaml
# >>> https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/
cluster.routing.allocation.disk.watermark.low: 85%
cluster.routing.allocation.disk.watermark.high: 90%
cluster.routing.allocation.disk.watermark.flood_stage: 95%
```

When disk usage reaches 85%, the `low` watermark prevents OpenSearch from allocating new shards to that node, except for primary shards of newly created indices. At 90%, the `high` watermark triggers shard relocation attempts to nodes with more available disk space. If usage reaches 95%, the `flood_stage` watermark applies a read-only block to indices with shards on that node to prevent the disk from running out of space.

These percentages scale with disk capacity. A node with 10 TB of storage, for example, reaches the same thresholds at 8.5 TB, 9 TB, and 9.5 TB of used space. The default allocator balances shard counts and index distribution, while disk watermarks account for storage usage and trigger allocation or protection actions when nodes approach their disk limits.

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

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

When shard allocation fails, the cluster can enter a yellow or red state, affecting data availability. In a red state, at least one primary shard is unavailable, which can result in data loss if no recoverable copy exists. Understanding shard allocation is therefore important for protecting cluster availability. The [`GET /_cluster/allocation/explain`](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/) endpoint is useful for investigating why a shard was allocated to a particular node or why an allocation or rebalance was rejected.

## How OpenSearch Balances Shards Across Data Nodes

OpenSearch's default shard allocator, [`BalancedShardsAllocator.java`](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java), uses a weighted balancing model. It considers both the total number of shards per node and how shards from each index are distributed across the nodes.

The default weights are controlled by [`cluster.routing.allocation.balance.shard`](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/) and [`cluster.routing.allocation.balance.index`](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/). Their default values are `0.45` and `0.55`, respectively.

Shard size, however, is not a direct factor in this balancing model. As a result, two nodes can have a similar number of shards while consuming very different amounts of disk space. This can lead to unexpected results in production, especially in clusters with many small, granular indices. A node might hold dozens of tiny shards and use very little disk space, while another holds only a few large shards and is almost full. The shard distribution may look balanced, but disk usage tells a different story.

The allocation process also considers other constraints that influence shard placement. These include disk availability, allocation filters, awareness across availability zones or racks, and limits on the number of shards per node. These mechanisms can prevent an allocation even when it would improve shard balance. For an overview of the available allocation deciders and their roles, see the [Common Allocators](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/#common-allocators) section in the OpenSearch documentation.

## Shard Allocation Mechanisms

The default allocator is not the only mechanism that influences shard placement. OpenSearch provides additional allocation settings and APIs, although they do not all replace the default balancing strategy.

---

__Load-Aware Allocation__: Limits shard concentration when cluster capacity is reduced, such as when data nodes fail.

For example, consider a cluster with 10 data nodes and 100 shards, initially holding 10 shards per node. If 5 nodes fail, the remaining 5 nodes need to accommodate the 50 shards from the failed nodes. OpenSearch could redistribute all 50 shards across the surviving nodes, leaving each with around 20 shards: its original 10 shards plus 10 redistributed from the failed nodes.

Having each node handle twice as many shards as originally planned could become a problem, depending on the cluster's resources and workload. This is where Load-Aware Allocation comes in. It limits how many shards each node can hold based on the average shard count per node across the originally provisioned cluster capacity. This helps prevent the surviving nodes from becoming overloaded with shards after a failure.

The following configuration sets the provisioned capacity to 10 nodes and defines how much shard concentration is allowed:

```yaml
# https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/

cluster.routing.allocation.load_awareness.provisioned_capacity: 10
cluster.routing.allocation.load_awareness.skew_factor: 50
cluster.routing.allocation.load_awareness.flat_skew: 2
cluster.routing.allocation.load_awareness.allow_unassigned_primaries: true
```

Here, `provisioned_capacity` remains `10`, even after the failure, because it represents the intended cluster capacity. `skew_factor` allows 50% more shards than the original average of 10, while `flat_skew` adds 2 extra shards, bringing the limit to 17 per node.

With only 5 nodes available, each can hold up to 17 shards under this limit, allowing a total of 85 shards to be allocated from initial 100 shards. The remaining 15 shards stay unassigned until additional capacity becomes available. `allow_unassigned_primaries` controls whether primary shards can remain unassigned when the load-awareness limit prevents their allocation.

---

__Manual Shard Allocation__: Force manually shard allocation to specific Data node.

The Cluster Reroute API, [`POST /_cluster/reroute`](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/), allows administrators to manually move shards between nodes, among other operations. For example, imagine that `node1` is running low on disk space while `node2` has plenty of free capacity. You can simulate moving shard `0` of the `logs-2026.11` index from `node1` to `node2` with the following request:

```{code-block} json
:caption: POST /_cluster/reroute
{
  "commands": [
    {
      "move": {
        "index": "logs-2026.11",
        "shard": 0,
        "from_node": "node1",
        "to_node": "node2"
      }
    }
  ]
}
```

Shard movement is still subject to allocation deciders. For example, OpenSearch can reject the operation if the destination node does not have enough disk space or violates another allocation constraint. This API is useful for operational tasks or specific rebalancing scenarios, but it does not change the default allocation strategy or provide automatic size-based balancing.

## Balancing by Size: Disk Watermarks

OpenSearch uses three disk watermarks to control shard allocation based on disk usage: `low`, `high`, and `flood_stage`. Each one defines a threshold that triggers a different action. Watermarks accept percentage-based values or absolute disk space values. Percentages are calculated relative to each node's total disk capacity. For example, consider a node with 1 TB of storage and the following configuration:

```yaml
# https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/

cluster.routing.allocation.disk.watermark.low: 85%
cluster.routing.allocation.disk.watermark.high: 90%
cluster.routing.allocation.disk.watermark.flood_stage: 95%
```

When disk usage reaches 85%, the `low` watermark prevents OpenSearch from allocating new shards to that node, except for primary shards of newly created indices. At 90%, the `high` watermark triggers shard relocation attempts to nodes with more available disk space. If usage reaches 95%, the `flood_stage` watermark applies a read-only block to indices with shards on that node to prevent the disk from running out of space.

It's important to understand that shard allocation and disk watermarks are complementary mechanisms. The default allocator continues to balance shards based on shard counts and index distribution, while the disk threshold decider adds disk usage constraints to allocation decisions.

Disk usage is not a continuous balancing weight in the default allocator. Instead, the `low` watermark prevents new shard allocations to nodes that have reached the configured threshold, while the `high` watermark triggers attempts to relocate shards away from nodes with high disk usage. In other words, disk usage starts influencing shard placement through these allocation actions when nodes reach the configured watermark thresholds. Both mechanisms work together to keep shard distribution balanced while protecting disk capacity.

## Watermark Limitation: One Setting For All Storage Tiers

There is one limitation in the watermark design that I find particularly frustrating: __watermarks are global cluster settings__. You configure them once, and the same thresholds apply to every node, regardless of its storage tier. This becomes a problem in tiered clusters with hot, warm, and searchable nodes. Each tier has a different storage profile and a different cost per gigabyte. For example, a watermark that works well for warm nodes, where you want to use disk capacity efficiently before relocating shards, might be too aggressive for hot nodes. Hot nodes need more free space to handle indexing and query workloads. Yet OpenSearch gives you no way to configure different watermark thresholds for each tier.

Another scenario worth considering is OpenSearch Dashboards [multi-tenancy](https://docs.opensearch.org/latest/security/multi-tenancy/multi-tenancy-config/). When [multi-tenancy](https://docs.opensearch.org/latest/security/multi-tenancy/multi-tenancy-config/) is enabled, each user has a private tenant with a dedicated index to store saved objects, such as visualizations, dashboards, and index patterns. Custom tenants also have their own indexes, while the global tenant is shared among users. In environments with many Dashboards users, this can result in a large number of small, granular indexes. Although each index may consume very little disk space, its shards still contribute to the total shard count considered by the default allocation strategy. This can make shard distribution less representative of actual disk usage, reinforcing the need to understand how shard count balancing and disk watermarks complement each other.

I'd like to see per-tier watermark configuration in OpenSearch. Until that happens, we're stuck with a single set of thresholds for the entire cluster. Keep this in mind when designing tiered clusters, because whatever values you choose will be a compromise across all storage tiers.

## References

- BalancedShardsAllocator.java: <https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java>
- NodeLoadAwareAllocationDecider.java: <https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/decider/NodeLoadAwareAllocationDecider.java>
- OpenSearch Cluster Management Settings: <https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/>
- Cluster Settings API: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-settings/>
- Cluster Allocation Explain API: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/>
- Shard Allocation Filtering: <https://docs.opensearch.org/latest/api-reference/index-apis/shard-allocation/>
- Cluster Reroute API: <https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/>
- OpenSearch Dashboards Multi-tenancy: <https://docs.opensearch.org/latest/security/multi-tenancy/tenant-index/>
- ShardsAllocator Interface: <https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/ShardsAllocator.java>

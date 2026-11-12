---
tags: opensearch, sharding
date: "2026-11-04"
category: Observability
author: Carlos Neto
title: "OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks"
description: "How the OpenSearch default allocator balances shards by count instead of size, why that skews disk usage in clusters with many small indices, how disk watermarks correct it, and why one watermark setting for all tiers hurts."
myst:
  html_meta:
    description: "How the OpenSearch default allocator balances shards by count instead of size, why that skews disk usage in clusters with many small indices, how disk watermarks correct it, and why one watermark setting for all tiers hurts."
og:title: "OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks"
og:description: "How the OpenSearch default allocator balances shards by count instead of size, why that skews disk usage in clusters with many small indices, how disk watermarks correct it, and why one watermark setting for all tiers hurts."
---

*__Blog Post Publish Date:__ 2026/11/04*

---

# OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks

This blog post explains how OpenSearch distributes shards across data nodes. It covers how the default allocator works, why it can leave disk usage uneven in clusters with many small indices, and how disk watermarks correct that. It also covers other allocation mechanisms and a limitation I run into often: watermarks are one cluster-wide setting, even in clusters with different storage tiers.

## Why Shard Balance Matters

**Shard allocation** is the process that decides which data node holds each shard. An index is split into [shards](/blog/2025/2025-01-05-opensearch-concepts-index-and-shards.md), each one a Lucene index that holds part of the data, so indexing and search run in parallel across the cluster. That only works if data nodes have free disk space for new shards as indices are created and existing data grows.

If most of the free space is concentrated on a few nodes, the cluster can struggle to allocate new shards, even when there is plenty of storage in total.

When allocation fails, the cluster goes yellow or red. In a red state, at least one primary shard is unavailable, which can mean data loss if no recoverable copy exists. The [`GET /_cluster/allocation/explain`](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/) endpoint shows why a shard was allocated to a node, or why an allocation or rebalance was rejected.

## How OpenSearch Balances Shards Across Data Nodes

OpenSearch's default shard allocator, [`BalancedShardsAllocator.java`](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java), uses a weighted balancing model. It considers both the total number of shards per node and how shards from each index are distributed across the nodes. The default weights are controlled by [`cluster.routing.allocation.balance.shard`](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/) and [`cluster.routing.allocation.balance.index`](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/). Their default values are `0.45` and `0.55`, respectively.

Shard size is not a factor in this balancing model. As a result, two nodes can have a similar number of shards while consuming very different amounts of disk space. That leads to surprises in production, especially in clusters with many small, granular indices. A node might hold dozens of tiny shards and use very little disk space, while another holds only a few large shards and is almost full. The shard distribution may look balanced, but disk usage tells a different story.

Allocation also respects other constraints, called **allocation deciders**: disk availability, allocation filters, awareness across availability zones or racks, and limits on shards per node. A decider can block an allocation even when it would improve the balance. The [common allocators](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/#common-allocators) section of the documentation lists them.

## Shard Allocation Mechanisms

The default allocator isn't the only thing that influences shard placement. OpenSearch has other settings and APIs, although none of them replaces the default balancing strategy.

### Load-Aware Allocation

**Load-aware allocation** limits how many shards can pile up on each node when the cluster loses capacity, for example when data nodes fail.

For example, consider a cluster with 10 data nodes and 100 shards, initially holding 10 shards per node. If 5 nodes fail, the remaining 5 nodes need to accommodate the 50 shards from the failed nodes. OpenSearch could redistribute all 50 shards across the surviving nodes, leaving each with around 20 shards: its original 10 shards plus 10 redistributed from the failed nodes.

Twice as many shards per node as planned can be a problem, depending on the node resources and workload. Load-aware allocation caps the shards per node based on the average shard count across the originally provisioned capacity, so the surviving nodes don't get overloaded after a failure.

The following configuration sets the provisioned capacity to 10 nodes and defines how much shard concentration is allowed:

```yaml
cluster.routing.allocation.load_awareness.provisioned_capacity: 10
cluster.routing.allocation.load_awareness.skew_factor: 50
cluster.routing.allocation.load_awareness.flat_skew: 2
cluster.routing.allocation.load_awareness.allow_unassigned_primaries: true
```

Here, `provisioned_capacity` remains `10`, even after the failure, because it represents the intended cluster capacity. `skew_factor` allows 50% more shards than the original average of 10, while `flat_skew` adds 2 extra shards, bringing the limit to 17 per node.

With only 5 nodes available, each can hold up to 17 shards, so 85 of the 100 shards can be allocated. The remaining 15 shards stay unassigned until additional capacity becomes available. `allow_unassigned_primaries` controls whether primary shards can remain unassigned when the load-awareness limit prevents their allocation.

### Manual Shard Allocation

The Cluster Reroute API, [`POST /_cluster/reroute`](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/), lets you move shards between nodes by hand, among other operations. For example, if `node1` is running low on disk and `node2` has plenty of free space, this request moves shard `0` of the `logs-2026.11` index from `node1` to `node2`. Add `?dry_run=true` to simulate it first:

```opensearch
POST /_cluster/reroute
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

The move still goes through the allocation deciders, so OpenSearch rejects it if the destination doesn't have enough disk or breaks another constraint. The API is useful for one-off operations, but it doesn't change the default strategy or add automatic size-based balancing. To move every shard off a node, an allocation exclusion is a better tool, as I show in [Scaling Down and Resizing OpenSearch Data Nodes](/blog/2026/2026-11-10-opensearch-scale-down.md).

## Balancing by Size: Disk Watermarks

**Disk watermarks** are thresholds of disk usage that change how OpenSearch allocates shards. There are three, `low`, `high`, and `flood_stage`, and each triggers a different action. They accept a percentage of each node's disk or an absolute amount of free space. For example, consider a node with 1 TB of storage and this [configuration](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/):

```yaml
cluster.routing.allocation.disk.watermark.low: 85%
cluster.routing.allocation.disk.watermark.high: 90%
cluster.routing.allocation.disk.watermark.flood_stage: 95%
```

When disk usage reaches 85%, the `low` watermark prevents OpenSearch from allocating new shards to that node, except for primary shards of newly created indices. At 90%, the `high` watermark triggers shard relocation attempts to nodes with more available disk space. If usage reaches 95%, the `flood_stage` watermark applies a read-only block to indices with shards on that node to prevent the disk from running out of space.

Shard balancing and disk watermarks complement each other. The default allocator keeps balancing by shard count and index distribution, while the disk threshold decider adds disk usage limits to its decisions.

Disk usage is not a continuous weight in the default allocator. It only starts to influence placement when a node crosses a watermark: `low` stops new shards from landing there, and `high` starts moving shards away. Together, the two mechanisms keep shards balanced while protecting disk capacity.

## Watermark Limitation: One Setting For All Storage Tiers

There is one limitation in the watermark design that I find particularly frustrating: __watermarks are global cluster settings__. You configure them once, and the same thresholds apply to every node, regardless of its storage tier. That's a problem in tiered clusters with hot, warm, and searchable nodes, such as the [hot tier on EC2 Instance Store](/blog/2026/2026-11-08-opensearch-hot-instance-store.md) I run. Each tier has a different storage profile and a different cost per gigabyte. For example, a watermark that works well for warm nodes, where you want to use disk capacity efficiently before relocating shards, might be too aggressive for hot nodes. Hot nodes need more free space to handle indexing and query workloads. Yet OpenSearch gives you no way to configure different watermark thresholds for each tier.

Another scenario worth considering is OpenSearch Dashboards [multi-tenancy](https://docs.opensearch.org/latest/security/multi-tenancy/multi-tenancy-config/). When [multi-tenancy](https://docs.opensearch.org/latest/security/multi-tenancy/multi-tenancy-config/) is enabled, each user has a private tenant with a dedicated index to store saved objects, such as visualizations, dashboards, and index patterns. Custom tenants also have their own indexes, while the global tenant is shared among users. In environments with many Dashboards users, this can result in a large number of small, granular indexes. Although each index may consume very little disk space, its shards still contribute to the total shard count considered by the default allocation strategy. That makes the shard distribution even less representative of real disk usage. The same happens when you create one small index per environment, which is why I [replace per-environment indexes with filtered aliases](/blog/2026/2026-11-11-opensearch-alias-filtered-by-field.md).

I'd like to see per-tier watermark configuration in OpenSearch. Until that happens, we're stuck with a single set of thresholds for the entire cluster. Keep this in mind when designing tiered clusters, because whatever values you choose will be a compromise across all storage tiers.

## Key Takeaways

- The default allocator balances by shard count and index distribution (`balance.shard` 0.45, `balance.index` 0.55). Shard size is not a factor.
- With many small indices, nodes can have similar shard counts and very different disk usage.
- Disk watermarks add size awareness: `low` stops new shards on a node, `high` moves shards away, and `flood_stage` puts a read-only block on indices with shards on the node.
- Load-aware allocation caps shards per node after a capacity loss, based on the provisioned capacity, `skew_factor`, and `flat_skew`.
- `POST /_cluster/reroute` moves individual shards, but it still goes through the allocation deciders.
- Watermarks are global, so tiered clusters must use one compromise threshold for every tier.
- `GET /_cluster/allocation/explain` shows why a shard was or wasn't allocated.

## References

- [BalancedShardsAllocator.java (OpenSearch source)](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/BalancedShardsAllocator.java)
- [NodeLoadAwareAllocationDecider.java (OpenSearch source)](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/decider/NodeLoadAwareAllocationDecider.java)
- [ShardsAllocator interface (OpenSearch source)](https://github.com/opensearch-project/OpenSearch/blob/main/server/src/main/java/org/opensearch/cluster/routing/allocation/allocator/ShardsAllocator.java)
- [Cluster settings (OpenSearch)](https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/cluster-settings/)
- [Cluster Settings API (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-settings/)
- [Cluster Allocation Explain API (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-allocation/)
- [Cluster Reroute API (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-reroute/)
- [Shard allocation filtering (OpenSearch)](https://docs.opensearch.org/latest/api-reference/index-apis/shard-allocation/)
- [Dashboards multi-tenancy: tenant indexes (OpenSearch)](https://docs.opensearch.org/latest/security/multi-tenancy/tenant-index/)

*I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks",
      "description": "How the OpenSearch default allocator balances shards by count instead of size, why that skews disk usage in clusters with many small indices, how disk watermarks correct it, and why one watermark setting for all tiers hurts.",
      "datePublished": "2026-11-04",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-11-04-opensearch-watermark/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-11-04-opensearch-watermark/",
      "keywords": ["OpenSearch", "shard allocation", "disk watermarks", "load-aware allocation", "cluster reroute"],
      "author": {"@id": "https://carlosneto.dev/#person"}
    },
    {
      "@type": "Person",
      "@id": "https://carlosneto.dev/#person",
      "name": "Carlos Neto",
      "url": "https://carlosneto.dev/",
      "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
        {"@type": "ListItem", "position": 3, "name": "OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks"}
      ]
    }
  ]
}
</script>
```

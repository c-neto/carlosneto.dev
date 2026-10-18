---
tags: opensearch
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# OpenSearch Shard Allocation: It Counts Shards, Not Their Size

This blog post explains how OpenSearch balances indices across data nodes. It covers how shard allocation works by counting shards instead of measuring their size, why this matters when you have many small and granular indices, how disk watermarks rebalance data based on free disk space, and a critique about the watermark being a cluster-wide setting.

## How OpenSearch Balances Shards Across Data Nodes

When OpenSearch distributes the shards of your indices across the data nodes, it balances them based on the **number of shards per node**, not the **size of those shards**. The cluster tries to keep roughly the same shard count on every data node, and it does not care how much disk each shard actually consumes.

This looks fine at first glance, but it has a consequence that surprised me in production. Picture a cluster with granular indices, many small indices with a low storage footprint. Because the allocation logic only counts shards, you can easily end up with nodes holding a lot of tiny shards and very little disk usage, while other nodes hold a few heavy shards and are almost full. The shard count is balanced, the disk usage is not, and the cluster still thinks every node has a fair share.

So the first thing to keep in mind is that shard allocation balances by count, not by size.

## Balancing by Size: Disk Watermarks

If the default allocation does not look at size, how do you get OpenSearch to react to disk usage? That is the job of the **disk watermarks**.

The watermark settings make the cluster relocate shards based on the percentage (or absolute amount) of free disk space remaining on a node. Instead of counting shards, these thresholds watch how full each node is and trigger reallocation when a node crosses a limit. There are three of them:

- `cluster.routing.allocation.disk.watermark.low`: once a node crosses this threshold, OpenSearch stops allocating new shards to it. Existing shards stay where they are.
- `cluster.routing.allocation.disk.watermark.high`: once a node crosses this one, OpenSearch starts relocating shards away from it to other nodes with more free space.
- `cluster.routing.allocation.disk.watermark.flood_stage`: the last line of defense. When a node crosses this threshold, OpenSearch applies a read-only block to the indices with shards on that node, so the node does not fill up completely.

So the watermarks are what brings disk size back into the picture. Shard count balances the layout, and the watermarks correct it when a node gets too full.

## Conclusion (Author Opinion)

Understanding this split between count-based allocation and size-based watermarks saved me a lot of confusion when debugging clusters where disk usage was all over the place while the shard count looked perfectly balanced.

That said, I have a real criticism about the watermark design. The watermark is a **global cluster setting**. You configure it once, and it applies to every node regardless of the storage tier it belongs to. In a cluster with tiering (hot, warm, and searchable nodes), this is a problem, because each tier has a very different disk profile and a very different cost per gigabyte.

A watermark value that makes perfect sense for a warm node, where you want to pack as much data as possible before relocating, is a terrible value for a hot node, where you want to keep more headroom for heavy indexing and query load. You cannot express that difference. One value has to serve all tiers, and that forces a compromise that fits none of them well.

I would love to see per-tier watermark configuration in OpenSearch. Until then, keep this limitation in mind when you design a tiered cluster, and pick your watermark values knowing they are a one-size-fits-all compromise.

## References

- https://opensearch.org/docs/latest/api-reference/cluster-api/cluster-settings/
- https://opensearch.org/docs/latest/install-and-configure/configuring-opensearch/cluster-settings/

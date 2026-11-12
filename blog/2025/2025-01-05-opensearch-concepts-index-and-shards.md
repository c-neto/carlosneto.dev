---
tags: opensearch, sharding
date: "2025-01-05"
category: Observability
author: Carlos Neto
title: "OpenSearch Concepts: Index and Shards"
description: "What OpenSearch indices, primary shards, and replica shards are, how shard counts affect write throughput and fault tolerance, and the API calls I use to troubleshoot indices and shards."
myst:
  html_meta:
    description: "What OpenSearch indices, primary shards, and replica shards are, how shard counts affect write throughput and fault tolerance, and the API calls I use to troubleshoot indices and shards."
og:title: "OpenSearch Concepts: Index and Shards"
og:description: "What OpenSearch indices, primary shards, and replica shards are, how shard counts affect write throughput and fault tolerance, and the API calls I use to troubleshoot indices and shards."
---

*__Blog Post Publish Date:__ 2025/01/05*

---

# OpenSearch Concepts: Index and Shards

This blog post explains two of the most basic concepts in OpenSearch administration: indices and shards. It covers what primary and replica shards are, how their counts affect performance and fault tolerance, and the API calls I use most to inspect indices and shards while troubleshooting.

## Understanding Indices and Shards

An **index** is a logical namespace for a collection of documents and their characteristics, such as field types, lifecycle policies, and storage tier. OpenSearch stores those documents on disk in partitions called shards.

A **shard** is one partition of an index, and each shard is a full Lucene index. As the [OpenSearch introduction](https://docs.opensearch.org/latest/getting-started/intro/) describes, shards come in two kinds:

- **Primary shards** receive every write and can also serve reads.
- **Replica shards** are copies of the primaries. They provide fault tolerance and serve reads, which spreads the query load.

An index can have one or more shards spread across several nodes. That distribution is what lets an OpenSearch cluster scale an index beyond one machine and survive the loss of a node.

| | Primary shards | Replica shards |
| --- | --- | --- |
| Purpose | Hold the data and receive every write | Copies of the primaries for fault tolerance and reads |
| More of them means | More parallel indexing, until shards get too small | More read capacity and more copies to survive node failures |
| Can change after creation? | Only with split, shrink, or reindex | Yes, at any time |

More primary shards spread writes across more partitions and nodes, which raises indexing throughput. More replicas add fault tolerance and more nodes that can answer queries.

The number of primary shards is set when the index is created. Changing it later means creating a new index with the [split](https://docs.opensearch.org/latest/api-reference/index-apis/split/) or [shrink](https://docs.opensearch.org/latest/api-reference/index-apis/shrink-index/) APIs, or reindexing. Choose it carefully, based on your query load and, above all, your write load. Replicas can be changed at any time.

More shards are not always better, though. Every shard costs heap, file handles, and cluster state, so many small shards hurt more than they help. I wrote about one way to avoid that in [Avoiding Over-Sharding in OpenSearch with Filtered Aliases](/blog/2026/2026-11-11-opensearch-alias-filtered-by-field.md).

:::{note}
A primary shard and its replica are never allocated to the same node. If that node fails, the other copy is still available.
:::

## Useful API Calls for Indices and Shards

These calls help with troubleshooting and monitoring indices and shards. You can run them in _OpenSearch Dashboards » Dev Tools_ or with an HTTP client such as _cURL_ or _Postman_.

- List all indices, sorted by name ([CAT indices](https://docs.opensearch.org/latest/api-reference/cat/cat-indices/)):

```opensearch
GET _cat/indices?v&s=index
```

- List the shards of a specific index:

```opensearch
GET <INDEX-NAME>/_search_shards
```

- Get the index settings, for example the number of shards, replicas, and creation time:

```opensearch
GET <INDEX-NAME>/_settings
```

- Get the field types defined in the index mapping:

```opensearch
GET <INDEX-NAME>/_mapping
```

- Show the ISM policy attached to an index ([ISM explain API](https://docs.opensearch.org/latest/im-plugin/ism/api/)):

```opensearch
GET _plugins/ism/explain/<INDEX-NAME>?show_policy=true
```

- List shards that are not allocated to any node (status _UNASSIGNED_) and why ([CAT shards](https://docs.opensearch.org/latest/api-reference/cat/cat-shards/)):

```opensearch
GET _cat/shards?v&h=index,shard,prirep,state,unassigned.reason&s=state
```

- Check how shards and disk are distributed across nodes ([CAT allocation](https://docs.opensearch.org/latest/api-reference/cat/cat-allocation/)):

```opensearch
GET _cat/allocation?v
```

- Follow shard recovery or relocation progress ([CAT recovery](https://docs.opensearch.org/latest/api-reference/cat/cat-recovery/)):

```opensearch
GET _cat/recovery/<INDEX-NAME>?v&s=stage:desc
```

- List all shards, sorted by index:

```opensearch
GET _cat/shards?v&s=index
```

- List indices, sorted by size:

```opensearch
GET _cat/indices?v&h=index,store.size&s=store.size:desc
```

These calls answer most of my day-to-day questions about a cluster. When the allocation output shows nodes with very different disk usage, [OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks](/blog/2026/2026-11-04-opensearch-watermark.md) explains why. When you need to remove nodes, [Scaling Down and Resizing OpenSearch Data Nodes](/blog/2026/2026-11-10-opensearch-scale-down.md) shows how to move their shards safely first.

## Key Takeaways

- An index is a logical collection of documents. Shards are the partitions that store it, and each shard is a Lucene index.
- Primary shards receive every write. Replica shards are copies that add fault tolerance and serve reads.
- The number of primary shards is fixed at creation. Changing it requires split, shrink, or reindex. Replicas can change at any time.
- More primaries raise write throughput, but too many small shards waste heap and cluster state.
- A primary and its replica are never placed on the same node.
- `_cat/indices`, `_cat/shards`, `_cat/allocation`, and `_cat/recovery` cover most troubleshooting questions about indices and shards.

## References

- [Introduction to OpenSearch (OpenSearch)](https://docs.opensearch.org/latest/getting-started/intro/)
- [Split index (OpenSearch)](https://docs.opensearch.org/latest/api-reference/index-apis/split/)
- [Shrink index (OpenSearch)](https://docs.opensearch.org/latest/api-reference/index-apis/shrink-index/)
- [CAT indices (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cat/cat-indices/)
- [CAT shards (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cat/cat-shards/)
- [CAT allocation (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cat/cat-allocation/)
- [CAT recovery (OpenSearch)](https://docs.opensearch.org/latest/api-reference/cat/cat-recovery/)
- [ISM API (OpenSearch)](https://docs.opensearch.org/latest/im-plugin/ism/api/)

---

> *I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "OpenSearch Concepts: Index and Shards",
      "description": "What OpenSearch indices, primary shards, and replica shards are, how shard counts affect write throughput and fault tolerance, and the API calls I use to troubleshoot indices and shards.",
      "datePublished": "2025-01-05",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2025/2025-01-05-opensearch-concepts-index-and-shards/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2025/2025-01-05-opensearch-concepts-index-and-shards/",
      "keywords": ["OpenSearch", "index", "shards", "primary shard", "replica shard"],
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
        {"@type": "ListItem", "position": 3, "name": "OpenSearch Concepts: Index and Shards"}
      ]
    }
  ]
}
</script>
```

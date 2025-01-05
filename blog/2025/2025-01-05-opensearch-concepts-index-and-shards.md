---
tags: opensearch
date: "2025-01-05"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/01/05*

---

# OpenSearch Concepts - Index and Shards

OpenSearch is a powerful platform, but having a solid understanding of its basic concepts is essential for a seamless experience with the stack. In this blog post, we’ll cover one of the most fundamental aspects of OpenSearch administration: **Indices and Shards**. 

This article provides a high-level explanation of these concepts and includes useful commands for retrieving information about indices and shards—particularly helpful during troubleshooting.  

## Understanding Indices and Shards

An **index** is a logical namespace that organizes a collection of documents along with their associated characteristics, such as field types, life cycle policies, and storage layer state. These documents are stored on disk within logical partitions called **shards**.  

### Shards: Primary and Replica

Shards can be classified as **primary** or **replica**:  

**Primary shards** handle write operations and can also serve read requests when needed.

**Replica shards** are exact copies of primary shards, designed to ensure fault tolerance and improve query performance by handling read operations.  

An index can consist of one or more shards distributed across multiple nodes. This distributed nature enables OpenSearch to form clusters, allowing indices to span across different machines for improved scalability and reliability.  

Increasing the number of primary shards improves throughput and indexing performance by distributing data across multiple partitions. Conversely, increasing the number of replica shards enhances fault tolerance and boosts query performance by providing additional nodes to handle read operations.

The number of primary shards can only be defined during the creation of an index. Carefully consider the number of shards needed to meet your current requirements, factoring in query demands and, most importantly, write performance. Replica shards, however, can be adjusted on demand.

:::{note}
A primary shard and its corresponding replica cannot reside on the same node within a cluster, ensuring fault tolerance in case of node failure.
:::

## Useful Commands for Managing Indices and Shards Using the OpenSearch API

The following commands are especially useful for troubleshooting and monitoring the status of indices and shards. They can be executed in _OpenSearch Dashboards » Dev Tools_ or via an HTTP client like _cURL_ or _Postman_.

- List all indices, sorted by name:  

```bash
GET _cat/indices?v&s=index
```  

- List the shards composing a specific index:  

```bash
GET <INDEX-NAME>/_search_shards
```  

- Get index metadata (e.g., number of shards, replicas, creation time):  

```bash
GET <INDEX-NAME>/_settings
```  

- Retrieve field types defined in the index mapping:  

```bash
GET <INDEX-NAME>/_mapping
```  

- List the ISM Policy attached to an index during creation:  

```bash
GET _plugins/ism/explain/<INDEX-NAME>?show_policy=true
```  

- List shards not currently allocated to any node (status: _UNASSIGNED_):  

```bash
GET _cat/shards?v&h=index,shard,prirep,state,unassigned.reason&s=state
```  

- Check shard allocation across cluster nodes:  

```bash
GET _cat/allocation?v
```  

- Monitor shard recovery or relocation progress:  

```bash
GET _cat/recovery/<INDEX-NAME>?v&s=stage:desc
```  

- List all shards, sorted by index:  

```bash
GET _cat/shards?v&s=index
```  

- List indices, sorted by size:  

```bash
GET _cat/indices?v&h=index,store.size&s=store.size:desc
```  

With these commands you can efficiently get useful information about your OpenSearch clusters and streamline troubleshooting processes. If you have any questions or need further insights into OpenSearch, feel free to leave a comment below!  

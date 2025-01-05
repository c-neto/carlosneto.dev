---
tags: opensearch
date: "2025-01-02"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/01/02*

---

# OpenSearch Alias Filtered By Field - A Better Approach for Log Indexing and Query

This blog post outlines an alternative to manage OpenSearch indices using alias that filter documents by fields values.

## When to create OpenSearch Index

First of all, it is necessary to understand what is and what is for the Index in the OpenSearch. An index is a logical namespace that holds a collection of documents and their characteristics, like field typing, life cycle, storage layer definition.   

The new index creation depends on your needs. Sometimes it is interesting create index template and life cycle policy to create one index each day, sometimes it is necessary create index based on log characteristics like an

In my experience, three points must be important to consider for planning a creation of the new index: 

- `access permission`: 
- `structure`: 
- `lifecyle`: 
- `storage layer`: 

If all points are satisfied, not is necessary planning a creation of the new index template. If any point are susceptible to change, maybe it is necessary create another index template.



## The Problem - Unbalanced Node Utilization in OpenSearch Cluster

## The Solution - Utilizing OpenSearch API for Dynamic Hosts Registration

## Conclusion (Author Opinion)

## Links


This approach combines the advantages of managing only one index template with an enhanced experience for querying logs in OpenSearch through index patterns categorized by field.

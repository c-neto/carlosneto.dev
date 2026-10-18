---
tags: opensearch, observability, logs
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# The OpenSearch API Cheatsheet Every Operator Needs

When you are running an OpenSearch cluster in production, the difference between a five-minute fix and a two-hour incident is often just knowing the right API call. This blog post collects the day-to-day commands I reach for most: inspecting cluster health, hunting down slow queries, managing shard allocation, running maintenance operations, and troubleshooting ingestion, all in one place.

Every command is a raw REST call you can paste straight into OpenSearch Dashboards Dev Tools (or `curl`). Replace placeholders in `<angle-brackets>` with your own index names, patterns, or node names.

## Cluster Status

Start here when something feels off. These give you a top-down view of the cluster's health and where the work is happening.

```bash
# Overall cluster health (green / yellow / red)
GET /_cluster/health

# Current cluster-wide settings
GET /_cluster/settings

# Disk and shard allocation per node
GET /_cat/allocation?v

# Node health, sorted by JVM heap usage (spot memory pressure fast)
GET _cat/nodes?v&s=heap.percent

# All shards, sorted by index
GET _cat/shards?v&s=index

# Only UNASSIGNED shards, with the reason they're unassigned
GET _cat/shards?v&h=index,shard,prirep,state,unassigned.reason&s=state

# Indices sorted by store size
GET _cat/indices/<index-name|index-pattern>?h=health,status,index,uuid,pri,rep,docs.count,docs.deleted,store.size,creation.date.string&v&s=store.size

# Recovery / relocation progress
GET _cat/recovery?v&s=stage:desc
GET _cat/recovery/?v&active_only=true&h=index,source_node,target_node,bytes_percent&s=bytes_percent:desc

# Merge activity by index (high merges = heavy write/segment churn)
GET /_cat/indices?v&h=index,docs.count,store.size,search.query_total,search.query_time,merges.current&s=merges.current:desc
```

## Finding Long-Running Tasks and Queries

A single runaway query can pin a node's CPU and degrade the whole cluster. Use these to find and kill it.

```bash
# List tasks ordered by how long they've been running
GET _cat/tasks?v&s=running_time:desc&detailed=true

# Describe a single task
GET /_tasks/<taskHash:taskId>

# Force-cancel ALL running searches (emergency brake for a stuck query)
POST _tasks/_cancel?actions=*search*

# Hot threads on a specific node: see exactly what's eating CPU
GET /_nodes/<node-name>/hot_threads?threads=8&interval=2s&type=cpu
```

## Index Operations

The everyday index inspection and management calls.

```bash
# View an index's settings
GET /<index-name>/_settings

# Detailed index info, sorted by creation date
GET _cat/indices/<index-name|index-pattern>/?h=health,status,index,uuid,pri,rep,docs.count,docs.deleted,store.size,creation.date.string&v&s=creation.date.string

# Which ISM policy is managing this index, and its current state
GET _plugins/_ism/explain/<index-name>?show_policy=true

# List aliases, showing which index is the write target
GET /_cat/aliases/<index-pattern>?v&s=is_write_index

# Force a rollover on a write alias
POST <alias-name>/_rollover

# Peek at the latest documents by timestamp
GET <index-name>/_search
{
  "size": 10,
  "sort": { "@timestamp": "desc" },
  "query": { "match_all": {} }
}
```

## Searching

A handy pattern for substring/wildcard searches on analyzed (non-keyword) text fields:

```json
GET <index-name>/_search
{
  "query": {
    "query_string": {
      "query": "(*abc*) AND (*xyz*)",
      "default_field": "<field-name>"
    }
  }
}
```

> <i class="fa-solid fa-circle-info"></i> **About leading wildcards:**
>
> Leading wildcards (`*abc`) are expensive, they cannot use the inverted index efficiently. Great for a one-off investigation, bad for hot-path queries.

## Shard Allocation and Rebalancing

This is the heart of safe cluster maintenance: controlling where shards live so you can restart or drain nodes without losing data or triggering a storm of unnecessary relocation.

```json
# Explain why a shard is unassigned, then retry failed allocations
GET _cluster/allocation/explain
POST /_cluster/reroute?retry_failed=true
```

```json
# Disable rebalancing before restarting a node (prevents needless shard churn)
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.rebalance.enable": "none"
  }
}
```

```json
# Re-enable rebalancing when maintenance is done
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.rebalance.enable": "all"
  }
}
```

```json
# Drain nodes (decommission): move all shards OFF the named nodes
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "all",
    "cluster.routing.allocation.exclude._name": "<node-a>, <node-b>, <node-c>"
  }
}
```

```json
# Clear the drain / decommission exclusion
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": null,
    "cluster.routing.allocation.exclude._name": null
  }
}
```

```json
# Rebalance by index spread only (useful right after adding new nodes
# so new indices get balanced without reshuffling everything)
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.rebalance.enable": "none",
    "cluster.routing.allocation.enable": "all",
    "cluster.routing.allocation.balance.index": "1.0f",
    "cluster.routing.allocation.balance.shard": "0.0f"
  }
}
```

```json
# How many shards may rebalance at once (tune relocation throughput)
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.cluster_concurrent_rebalance": "4"
  }
}
```

```json
# Speed up (or cap) recovery/relocation bandwidth per node
PUT _cluster/settings
{
  "persistent": {
    "indices.recovery.max_bytes_per_sec": "100mb"
  }
}
```

## Settings and Logging

```json
# Dump every setting, including defaults, in flat form
GET _cluster/settings?include_defaults&flat_settings
```

```json
# Raise log verbosity for a single module (e.g. discovery)
PUT /_cluster/settings
{
  "persistent": {
    "logger.org.opensearch.discovery": "DEBUG"
  }
}
```

```json
# Raise log verbosity for everything (use sparingly!)
PUT /_cluster/settings
{
  "persistent": {
    "logger.org.opensearch": "INFO"
  }
}
```

## Thread Pool Troubleshooting

When indexing starts failing, the write thread pool queue is the first place to look. A growing queue or non-zero `rejected` count means the cluster cannot keep up with writes.

```bash
# All thread pools at a glance
GET /_cat/thread_pool/

# The write pool specifically, worst queues first
GET /_cat/thread_pool/write?v&h=node_name,name,active,queue,rejected&s=queue:desc
```

## Reindex, Move, and Delete

Heavy data operations. The `wait_for_completion=false` flag runs them asynchronously and returns a task ID you can poll.

```json
# Merge several source indices into one destination index
POST _reindex?wait_for_completion=false
{
  "conflicts": "proceed",
  "source": { "index": "<source-index-1>,<source-index-2>,<source-index-3>" },
  "dest": { "index": "<destination-index>", "op_type": "index" }
}

# Follow up on the async task
GET _tasks/<task-id>
```

```json
# Move an index from the hot tier to the warm tier
PUT <index-name>/_settings
{
  "settings": {
    "index.routing.allocation.require.temp": "warm"
  }
}
```

```json
# Delete documents by query (async). Here: a logger within a time range
POST <index-pattern>/_delete_by_query?wait_for_completion=false
{
  "query": {
    "bool": {
      "filter": [
        { "match": { "<field-name>": "<value>" } },
        {
          "range": {
            "@timestamp": {
              "gte": "2025-06-25T00:00:00.000Z",
              "lte": "2025-07-02T00:00:00.000Z",
              "format": "strict_date_optional_time"
            }
          }
        }
      ]
    }
  }
}
```

## ISM Policies

Index State Management drives the automatic lifecycle (rollover, warm migration, deletion). These commands let you inspect and override it.

```json
# What policy is attached, and what state is the index in?
GET _plugins/_ism/explain/<index-name>?show_policy=true

# Reassign a policy: remove, then add a new one by pattern
POST _plugins/_ism/remove/<index-pattern>
POST _plugins/_ism/add/<index-pattern>
{
  "policy_id": "<policy-id>"
}

# Change an existing index's policy and jump to a specific state
POST _plugins/_ism/change_policy/<index-name>
{
  "policy_id": "<policy-id>",
  "state": "rollover"
}

# Force a retry when a managed index is stuck in a failed action
POST _plugins/_ism/retry/<index-name>
```

## Snapshots

```bash
# Inspect a snapshot repository
GET _snapshot/<repository-name>

# List snapshots matching a pattern (verbose=false for a quick list)
GET _snapshot/<repository-name>/<snapshot-pattern>?verbose=false
```

## Ingest Pipelines

```json
# List all ingest pipelines
GET _ingest/pipelines

# Simulate a pipeline against a test document before deploying
POST /_ingest/pipeline/<pipeline-name>/_simulate
{
  "docs": [
    {
      "_index": "<optional-index-for-mapping>",
      "_source": { "<field>": "<test-value>" }
    }
  ]
}
```

## Logstash (Node API)

If Logstash sits in front of your cluster, these hit its own monitoring API (default port 9600).

```bash
# Hot threads inside Logstash
curl localhost:9600/_node/hot_threads?pretty

# Pipeline throughput and backpressure stats
curl localhost:9600/_node/stats/pipelines
curl localhost:9600/_node/stats/pipelines/<pipeline-name>
```

## Alerts and Monitors

```json
# List all alerting monitors
GET _plugins/_alerting/monitors/_search
{
  "size": 5000,
  "query": { "exists": { "field": "monitor" } }
}

# List all notification channels (destinations)
GET /_plugins/_notifications/channels
{
  "size": 5000,
  "query": { "match_all": {} }
}
```

## Quick Reference: When to Reach for What

| Situation | First command to run |
| --- | --- |
| Cluster is red/yellow | `GET /_cluster/health` then `GET _cat/shards?v&h=index,shard,prirep,state,unassigned.reason&s=state` |
| A node is maxed out on CPU | `GET /_nodes/<node>/hot_threads?type=cpu` |
| Indexing is failing | `GET /_cat/thread_pool/write?v&h=node_name,name,active,queue,rejected&s=queue:desc` |
| Shards won't allocate | `GET _cluster/allocation/explain` |
| About to restart a node | Disable rebalance, then drain with `exclude._name` |
| A query is hung | `POST _tasks/_cancel?actions=*search*` |
| Index stuck in its lifecycle | `GET _plugins/_ism/explain/<index>?show_policy=true` then `POST _plugins/_ism/retry/<index>` |

## Conclusion (Author Opinion)

This is the cheatsheet I keep open in a pinned tab, built up over years of 3 a.m. pages and "why is the cluster yellow again" afternoons. None of these commands are secret, they are all in the docs, but having them collected and labeled is what turns a stressful incident into a copy-paste.

Bookmark it, adapt the placeholders to your naming, and add your own calls as you go. If you have a command you reach for that I missed, I would genuinely like to hear about it.

## References

- <https://opensearch.org/docs/latest/api-reference/>
- <https://opensearch.org/docs/latest/api-reference/cat/index/>
- <https://opensearch.org/docs/latest/im-plugin/ism/api/>

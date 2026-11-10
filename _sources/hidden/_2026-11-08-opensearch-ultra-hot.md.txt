---
tags: opensearch
date: "2026-11-09"
category: OpenSearch
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# How to Scaling OpenSearch Data Nodes Safely

This blog post covers the patterns and API calls I use to scale down and resize OpenSearch data nodes with zero data loss. The data on a node you remove has to end up somewhere else first, and if you take nodes away faster than the cluster can relocate their shards, you lose data.

## The Core Challenge

Every time I scale down a data tier, I treat it as the risky operation it is, and I have never regretted being slow about it. The rule that keeps me out of trouble is boring and absolute: move the data off before the node disappears. Disable rebalancing first, drain with `exclude._name`, check capacity, and never advance a step until the cluster is green and every shard is assigned.

For ephemeral storage, Blue/Green is not optional, it is the only safe way to resize or scale down, because you cannot drain a disk that gets wiped on termination. And whatever pattern you use, clear your transient settings afterward. Leftover exclusion rules or disabled rebalancing will bite you the next time the topology changes. Go slow, verify at every step, and the scariest operation on the cluster becomes routine.

Scaling down or resizing the data tier is one of the riskiest operations you can perform on an OpenSearch cluster. Whether you are shrinking the fleet to cut cost, moving to a smaller or larger instance type, or swapping out ephemeral-storage nodes, doing it wrong can cause data loss or extended downtime.

OpenSearch distributes data as shards across nodes. When you remove a node abruptly, the cluster scrambles to re-replicate its shards from elsewhere, consuming bandwidth, CPU, and I/O. If you scale down multiple nodes simultaneously, or if replica counts are too low, you risk losing data before recovery can complete.

Scaling down is riskier than scaling up for a simple reason: you are removing capacity that currently holds data. Every node you take out must have its shards relocated to the survivors before it goes. Resizing is just a scale-down and scale-up chained together. You replace a node (or a whole node group) with a different shape, so the same rule applies: move the data off before the old node disappears.

The safe path is always the same: control shard allocation explicitly, verify state before each step, and only then remove nodes.

## Monitoring Shard Relocation and Cluster Health

- __Allocation__: OpenSearch automatically assigns shards to nodes and rebalances when the cluster topology changes. You can override this behavior via the cluster settings API.

- __Rebalancing__: the process of moving shards between nodes to maintain an even distribution. This runs continuously in the background. During a scale-down or resize, you want to pause it to avoid unnecessary shard movement.

- __Draining__: using allocation exclusion to tell OpenSearch to move every shard off a specific node before you remove it. This is the heart of a safe scale-down.

- __Blue/Green for stateful workloads__: when nodes use locally-attached (ephemeral) storage such as NVMe Instance Store, data is lost when the node terminates. For resizing these nodes you cannot drain in place, so Blue/Green lets you bring up a parallel set of nodes in the new shape, migrate all data to them, then decommission the old ones cleanly.

Monitoring is essential during shard migrations, especially when increasing recovery concurrency or bandwidth limits. I use the following APIs to track shard relocation progress, identify allocation issues, and monitor resource consumption across the cluster.

```bash
# All shards, sorted by state
GET /_cat/shards?v&s=state

# Shards grouped by index
GET /_cat/shards?v&s=index

# Shards grouped by node
GET /_cat/shards?v&s=node

# Shards assigned to a specific node
GET /_cat/shards?v&h=index,shard,prirep,state,node&s=index

# All ongoing recoveries with detailed information
GET /_cat/recovery?active_only=true&detailed=true&bytes=gb&v

# Recovery history, including completed operations
GET /_cat/recovery?v

# Overall cluster health
GET /_cluster/health

# Wait for ongoing shard relocations and initializations
GET /_cluster/health?wait_for_no_relocating_shards=true&wait_for_no_initializing_shards=true

# Pending cluster tasks
GET /_cat/pending_tasks?v

# Active cluster tasks
GET /_cat/tasks?v

# If a shard remains unassigned or relocation does not progress as expected, use the Cluster Allocation Explain API to understand why OpenSearch cannot allocate it:
GET /_cluster/allocation/explain

# You can also investigate a specific shard:
POST /_cluster/allocation/explain
{
  "index": "my-index",
  "shard": 0,
  "primary": true
}

# Node list and resource information
GET /_cat/nodes?v&s=name

# Disk allocation per node
GET /_cat/allocation?v

# Filesystem and JVM statistics
GET /_nodes/stats/fs,jvm

# Operating system and thread pool statistics
GET /_nodes/stats/os,thread_pool

# Network transport statistics
GET /_nodes/stats/transport
```

Pay particular attention to filesystem utilization and JVM memory pressure. When increasing recovery concurrency, also monitor network throughput at the infrastructure level, since the OpenSearch transport statistics alone do not provide a complete picture of network bandwidth utilization.

If nodes start approaching resource limits, reduce recovery concurrency and bandwidth settings before the migration affects normal cluster operations.

I recommend keeping these commands available throughout the migration and checking them before removing each node. A migration is only complete when the intended nodes are empty, shard recoveries have finished, and the cluster has returned to a healthy state.

## Speed Up Shard Migration

OpenSearch applies conservative limits to shard recovery and relocation to prevent these operations from consuming too many cluster resources. By default, a node allows two concurrent incoming and two concurrent outgoing shard recoveries, while the maximum recovery transfer rate is limited to `40mb` per second per node.

These limits help preserve cluster stability during shard movements, but they can also make large migrations take longer than necessary.

If your cluster has spare CPU, memory, disk I/O, and network capacity, you can increase these limits to speed up the migration. For example:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.node_concurrent_recoveries": 10,
    "cluster.routing.allocation.cluster_concurrent_rebalance": 10,
    "indices.recovery.max_bytes_per_sec": "200mb"
  }
}
```

Be careful when increasing these values. More concurrent recoveries and higher transfer rates can put significant pressure on data nodes, consuming CPU, memory, disk I/O, and network bandwidth. If the infrastructure cannot handle the additional workload, the nodes can become overloaded, affecting normal cluster operations and potentially making the entire cluster unresponsive.

I've experienced this firsthand: increasing recovery concurrency too aggressively caused node overload and brought the cluster to a point where it stopped responding properly. Network saturation is another risk, especially when relocating large amounts of data between nodes.

Treat these values as temporary tuning parameters, not recommended defaults. Increase them gradually, monitor node and network utilization, and reduce them if the cluster starts showing signs of saturation. Once the migration is complete, restore the original settings.

## Pattern 1: Scaling Down / Resizing Nodes with Network-Attached Storage

Use this when your data nodes use EBS, NFS, or any other persistent storage that survives node termination. This is the pattern for shrinking the fleet or resizing to a different instance type when the disk is not ephemeral.

### Step 1: Disable shard rebalancing

Before draining or terminating any node, tell OpenSearch to stop moving shards around:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.rebalance.enable": "none"
  }
}
```

This prevents the cluster from immediately trying to re-distribute shards the moment a node disappears, which would waste I/O and bandwidth on work you are about to undo.

### Step 2: Drain the node you are removing

Mark the node for exclusion from shard allocation before terminating it:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._name": "node-name-0, node-name-1, node-name-2"
  }
}
```

OpenSearch will now move all primary and replica shards off that node before it is empty. When resizing, exclude every node you intend to replace. When scaling down, exclude the nodes you are removing. Monitor progress with:

```bash
GET _cat/shards?v&s=node
GET _cat/nodes?v&s=name
GET _cat/tasks
```

Wait until the target node has zero shards assigned before proceeding.

Before draining, make sure the remaining nodes have enough free disk to absorb the shards you are about to relocate, and stay under the watermark thresholds. Removing a node redistributes its data onto fewer nodes. If they fill past `cluster.routing.allocation.disk.watermark.high`, allocation stalls and you can get stuck mid-scale-down. Shrink too far and the cluster has nowhere to put the data at all.

### Step 3: Terminate the drained node (and, for resize, bring up its replacement)

Once the node is empty, you can safely terminate it. For a pure scale-down, you simply stop here with fewer nodes. For a resize, bring up a replacement in the new instance shape. The new node will join the cluster and receive shards as part of normal allocation.

### Step 4: Re-enable rebalancing

After all nodes have been rotated and the cluster is green:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.rebalance.enable": "all"
  }
}
```

## Pattern 2: Blue/Green for Resizing Ephemeral Storage Nodes

Use this when nodes have locally-attached storage (for example, NVMe SSDs via EC2 Instance Store). Because data is wiped when the instance terminates, you cannot drain and resize these nodes in place. You must migrate the data to the new node set first. This is the safe way to resize (or scale down) an ephemeral hot tier.

The idea: run two StatefulSets in parallel (`blue` and `green`), migrate shards from one to the other, then decommission the old set.

### Step 1: Disable shard rebalancing

Same as above, prevent automatic redistribution while you are in control:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.rebalance.enable": "none"
  }
}
```

### Step 2: Bring up the new node set (green) without data

Start your new nodes but exclude them from receiving any shard allocations immediately. This lets them boot and join the cluster without triggering a flood of shard movement:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._name": "green-node-1, green-node-2, green-node-N"
  }
}
```

Deploy your new node set and wait for all nodes to reach `Ready` status.

### Step 3: Migrate data from blue to green

Now flip the exclusion to the old (blue) nodes. OpenSearch will begin moving shards off the blue nodes and onto the green nodes:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._name": "blue-node-1, blue-node-2, blue-node-N"
  }
}
```

Monitor the migration closely:

```bash
# Overall shard state: look for RELOCATING or UNASSIGNED
GET _cat/shards?v&s=state

# Shards by node: verify blue nodes are draining
GET _cat/shards?v&s=node

# Active tasks: watch for recover and relocation tasks
GET _cat/tasks

# Cluster health: wait for green
GET _cluster/health
```

Do not proceed until all shards have moved off the blue nodes and cluster health is green.

### Step 4: Decommission the old node set

Once all data is on the green nodes, delete the old (blue) StatefulSet:

```bash
kubectl delete sts <blue-statefulset-name>
```

### Step 5: Clear allocation exclusions

Remove the exclusion rules so future shard assignments work normally:

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._name": null
  }
}
```

### Step 6: Re-enable rebalancing

```json
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.rebalance.enable": "all"
  }
}
```


## Key Takeaways

- Scaling down is riskier than scaling up because existing data must be relocated before nodes are removed.
- Disable shard rebalancing during planned migrations to avoid unnecessary background shard movements while retaining the allocation required for draining nodes.
- For persistent storage, use shard allocation exclusions to drain nodes before terminating them.
- For ephemeral storage, use a Blue/Green approach to migrate shards to a new node group before removing the old instances.
- Always verify shard allocation, cluster health, and available disk capacity before proceeding to the next step.
- Restore the original cluster settings after the migration. Leftover allocation exclusions or disabled rebalancing can interfere with future topology changes.

## References

- <https://opensearch.org/docs/latest/api-reference/cluster-api/cluster-settings/>
- <https://opensearch.org/docs/latest/tuning-your-cluster/availability-and-recovery/>
- <https://opensearch.org/docs/latest/api-reference/cat/cat-shards/>

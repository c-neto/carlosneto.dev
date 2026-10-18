---
tags: opensearch, kubernetes, aws, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# How to Scale Down and Resize OpenSearch Data Nodes Safely

Scaling down or resizing the data tier is one of the riskiest operations you can perform on an OpenSearch cluster. Whether you are shrinking the fleet to cut cost, moving to a smaller or larger instance type, or swapping out ephemeral-storage nodes, doing it wrong can cause data loss or extended downtime.

This blog post covers the patterns and API calls I use to scale down and resize OpenSearch data nodes with zero data loss. The data on a node you remove has to end up somewhere else first, and if you take nodes away faster than the cluster can relocate their shards, you lose data.

## The Core Challenge

OpenSearch distributes data as shards across nodes. When you remove a node abruptly, the cluster scrambles to re-replicate its shards from elsewhere, consuming bandwidth, CPU, and I/O. If you scale down multiple nodes simultaneously, or if replica counts are too low, you risk losing data before recovery can complete.

Scaling down is riskier than scaling up for a simple reason: you are removing capacity that currently holds data. Every node you take out must have its shards relocated to the survivors before it goes. Resizing is just a scale-down and scale-up chained together. You replace a node (or a whole node group) with a different shape, so the same rule applies: move the data off before the old node disappears.

The safe path is always the same: control shard allocation explicitly, verify state before each step, and only then remove nodes.

## Concepts You Need to Know

__Shard allocation__: OpenSearch automatically assigns shards to nodes and rebalances when the cluster topology changes. You can override this behavior via the cluster settings API.

__Rebalancing__: the process of moving shards between nodes to maintain an even distribution. This runs continuously in the background. During a scale-down or resize, you want to pause it to avoid unnecessary shard movement.

__Draining a node__: using allocation exclusion to tell OpenSearch to move every shard off a specific node before you remove it. This is the heart of a safe scale-down.

__Blue/Green for stateful workloads__: when nodes use locally-attached (ephemeral) storage such as NVMe Instance Store, data is lost when the node terminates. For resizing these nodes you cannot drain in place, so Blue/Green lets you bring up a parallel set of nodes in the new shape, migrate all data to them, then decommission the old ones cleanly.

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
    "cluster.routing.allocation.exclude._name": "node-name-1"
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

> <i class="fa-solid fa-circle-info"></i> **Capacity check for scale-down:**
>
> Before draining, make sure the remaining nodes have enough free disk to absorb the shards you are about to relocate, and stay under the watermark thresholds. Removing a node redistributes its data onto fewer nodes. If they fill past `cluster.routing.allocation.disk.watermark.high`, allocation stalls and you can get stuck mid-scale-down. Shrink too far and the cluster has nowhere to put the data at all.

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

## Useful Monitoring Commands

Keep these handy throughout any migration:

```bash
# Shard distribution sorted by state (spot UNASSIGNED or RELOCATING)
GET _cat/shards?v&s=state

# Shard distribution sorted by index
GET _cat/shards?v&s=index

# Shard distribution sorted by node
GET _cat/shards?v&s=node

# Node list with health stats
GET _cat/nodes?v&s=name

# Active cluster tasks
GET _cat/tasks

# Full cluster health
GET _cluster/health
```

## Conclusion (Author Opinion)

Every time I scale down a data tier, I treat it as the risky operation it is, and I have never regretted being slow about it. The rule that keeps me out of trouble is boring and absolute: move the data off before the node disappears. Disable rebalancing first, drain with `exclude._name`, check capacity, and never advance a step until the cluster is green and every shard is assigned.

For ephemeral storage, Blue/Green is not optional, it is the only safe way to resize or scale down, because you cannot drain a disk that gets wiped on termination. And whatever pattern you use, clear your transient settings afterward. Leftover exclusion rules or disabled rebalancing will bite you the next time the topology changes. Go slow, verify at every step, and the scariest operation on the cluster becomes routine.

## References

- <https://opensearch.org/docs/latest/api-reference/cluster-api/cluster-settings/>
- <https://opensearch.org/docs/latest/tuning-your-cluster/availability-and-recovery/>
- <https://opensearch.org/docs/latest/api-reference/cat/cat-shards/>

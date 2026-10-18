---
tags: opensearch, aws, kubernetes, performance
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# OpenSearch Instance Storage: The Controlled Risk for Superior Performance

When you run OpenSearch at scale, storage I/O is often the bottleneck that decides how fast you can index documents and how quickly you can serve queries. Most teams reach for network-attached block storage like Amazon EBS by default. It is durable, resizable, and survives instance termination. But there is a faster option hiding in plain sight: the local NVMe SSD that comes physically attached to certain EC2 instances, known as instance store (or ephemeral storage).

This blog post explains why instance store delivers dramatically better I/O performance for OpenSearch hot data nodes, backs that claim with technical evidence, and shows how the one serious drawback, data loss when an instance dies, is a controlled risk thanks to OpenSearch's native replication.

## The Core Idea

OpenSearch hot data nodes handle the most demanding workload in the cluster: freshly indexed documents, the most frequent searches, and continuous merges and refreshes. All of that is I/O-bound. The storage you put under those nodes directly caps your indexing throughput and query latency.

There are two architectural choices on AWS:

- __EBS (network-attached block storage)__: the disk lives on a separate storage tier in the same availability zone and is reached over the network.
- __Instance store NVMe (locally-attached SSD)__: the disk is physically present in the host machine running your instance.

That single difference, network hop vs. no network hop, is the root cause of the performance gap.

## Why EBS Is Slower: It Is Not Actually "In" the Instance

EBS is often described as a disk attached to your EC2 instance, but physically it is not inside the host at all. It is a separate storage system that your instance talks to over the network. Every read and write has to:

1. Leave the instance through the network interface,
2. Traverse the AWS storage fabric to reach the EBS backend,
3. Get acknowledged back across the same path.

AWS has engineered this path to be very good. Modern `gp3` volumes deliver single-digit millisecond latency, and `io2 Block Express` can hit sub-500-microsecond averages. But it is still a network round trip, and it is subject to two hard ceilings:

- __The volume's provisioned limits__, for example `gp3` tops out at 80,000 IOPS and 2,000 MiB/s (and you pay extra for anything above the 3,000 IOPS / 125 MiB/s baseline).
- __The instance's EBS bandwidth cap__: every instance type has a dedicated EBS link. For example, an `i8g.2xlarge` provides up to 10 Gbps of EBS bandwidth, which is the aggregate ceiling for all EBS traffic on that node, no matter how many volumes you attach.

Instance store NVMe has none of these problems because the SSD is wired directly into the host. There is no network, no provisioned IOPS to buy, and no shared EBS bandwidth budget to compete for.

## The Evidence: A Concrete Comparison

Let's compare two instances with identical compute and memory, differing only in storage architecture. We will use the `i8g.2xlarge` (storage-optimized, local NVMe) against a compute-equivalent instance of the same vCPU/memory shape that relies on EBS.

| Attribute | `i8g.2xlarge` (local NVMe) | Equivalent instance + EBS `gp3` |
| --- | --- | --- |
| vCPU | 8 (Graviton4) | 8 |
| Memory | 64 GiB | 64 GiB |
| Storage type | 1 x 1,875 GB NVMe instance store (3rd-gen Nitro SSD) | Network-attached `gp3` volume |
| Storage path | Directly attached to host | Over the network |
| Latency (4K random read) | ~20-100 microseconds | ~200 microseconds (p50), ~900 microseconds (p99) |
| Max throughput | 10+ GB/s (local bus) | Capped by instance EBS link (~1,250 MiB/s on a 10 Gbps class node) |
| IOPS ceiling | Native drive IOPS (100k+) | Must be provisioned and paid for; also capped by EBS bandwidth |
| Extra IOPS/throughput cost | $0 (bundled) | Billed per provisioned IOPS and MiB/s above baseline |

### Latency is the headline number

Published benchmarks consistently show local NVMe serving 4K random reads at roughly 30 microseconds (p50) and 100 microseconds (p99), compared to EBS `gp3` at roughly 200 microseconds (p50) and 900 microseconds (p99). That is a 5-10x advantage in small-block random read latency, exactly the access pattern OpenSearch generates when fetching documents and traversing on-disk data structures that are not resident in RAM.

### Real-world OpenSearch/Elasticsearch results

This is not just synthetic benchmarking. Teams running search workloads on these instances report concrete gains:

- __HubSpot__, migrating a large Elasticsearch/OpenSearch fleet to EC2 `i8g` instances, measured up to 20% better p99 search and index latencies, 40% better bulk index latencies, and 100ms faster client search response times versus the previous generation.
- __Elastic__ reported up to 21% better indexing throughput on the storage-dense `i8ge` variant versus the prior generation.
- __ScyllaDB__ measured up to 400% higher write throughput on `i8g` compared to older storage-optimized instances.

The common thread: workloads that constantly hit disk for writes (indexing, merges) and random reads (queries) benefit enormously from eliminating the network hop.

### A fair caveat

Local NVMe is not universally faster. For large-block, high-residency workloads where most reads are served from RAM, modern EBS `gp3` on a high-bandwidth instance can match or even edge out local NVMe on sustained throughput, because the bottleneck shifts to instance-level EBS bandwidth rather than the disk itself. The decisive, un-closable gap is small-block random read latency, and that is precisely what dominates an OpenSearch hot tier that is actively serving queries against data larger than RAM.

## The Catch: Ephemeral Means Ephemeral

Here is the tradeoff you cannot ignore. Instance store data is wiped the moment the instance stops, terminates, or is rotated. There is no snapshot, no detach-and-reattach, no recovery of the raw volume. If the underlying host fails, the data on that NVMe disk is simply gone.

For a stateful system like OpenSearch, that sounds terrifying. A node holding primary shards vanishing with no disk recovery is a classic data-loss scenario.

This is a real risk. But it is a controlled one.

## Why the Risk Is Controlled: OpenSearch Replication

OpenSearch is a distributed system designed from the ground up to survive node loss. The mechanism that makes ephemeral storage safe is shard replication.

Every index is split into primary shards, and OpenSearch maintains one or more replica shards for each primary. The critical guarantee: OpenSearch always places a replica on a different node than its primary. A replica is a full, continuously-updated copy of the data.

```json
PUT /my-index/_settings
{
  "index": {
    "number_of_replicas": 1
  }
}
```

With `number_of_replicas` set to at least `1`, the loss of any single node, including the total loss of its ephemeral disk, does not lose data:

1. A node dies and its instance store NVMe is wiped.
2. OpenSearch detects the node left the cluster.
3. For every primary that was on the dead node, OpenSearch promotes its replica (living on another node) to primary.
4. OpenSearch then rebuilds the missing replicas on surviving nodes to restore full redundancy.

The data was never in a single place to begin with. The ephemeral disk held a copy, not the copy.

### Making the control robust

Replication turns a catastrophic risk into a routine, self-healing event, but only if you configure the cluster to respect it:

- __Keep at least one replica__ (`number_of_replicas >= 1`) on any index you cannot afford to lose. Zero replicas means ephemeral storage will lose data on node failure.
- __Spread replicas across failure domains.__ Use shard allocation awareness / topology spread so that a primary and its replica never land in the same availability zone. Losing an entire AZ should still leave a full copy.
- __Rotate nodes safely.__ Because the disk is ephemeral, you cannot rotate these nodes in place. Use a controlled migration (drain shards off a node, or a blue/green node-group swap) so OpenSearch moves all data to new nodes before the old ones are terminated. Never terminate an instance-store node while it still holds the only copy of a shard.
- __Consider `wait_for_active_shards`__ on critical writes to ensure a write is acknowledged by more than just the primary before it is considered durable.

## Critical on Kubernetes: Stop the Node From Being Rotated Out From Under You

Everything above assumes node loss is an occasional, handled event. But on Kubernetes with a node autoscaler, there is a far more frequent threat to ephemeral hot nodes: voluntary disruption. The autoscaler may decide to consolidate, bin-pack, or rotate a node for perfectly ordinary reasons, and when it does, the local NVMe on that node is wiped, exactly as if the host had failed.

For a stateless workload that is a non-event. For an instance-store hot node, a careless rotation can race ahead of shard recovery and destroy the last surviving copy of a shard. So on top of replication, it is of utmost importance to configure policies that prevent these nodes from being casually rotated. Two controls do the heavy lifting.

### 1. Tell the autoscaler not to disrupt hot nodes

If you run Karpenter, the single most important annotation on an instance-store hot pod is `do-not-disrupt`. It tells Karpenter it may not voluntarily drain or terminate the node hosting that pod (no consolidation, no drift rotation), so the only disruptions left are ones you initiate deliberately:

```yaml
# On the hot data pod template
metadata:
  annotations:
    karpenter.sh/do-not-disrupt: "true"
```

This converts node rotation from something the platform does to you on its own schedule into something you do, under a controlled, shard-aware process. On ephemeral storage, that distinction is the difference between a routine maintenance window and silent data loss.

### 2. Size the PodDisruptionBudget to your replica count

A PodDisruptionBudget (PDB) caps how many data pods may be unavailable at once during voluntary disruptions. The safe limit is dictated directly by how many copies of your data you keep, which is your index replica count.

The rule of thumb: you can afford to lose at most as many nodes simultaneously as you have extra copies of every shard.

- With `number_of_replicas: 1` (one primary plus one replica, so 2 copies), only one node may go down at a time. Lose two at once and you can lose the only remaining copy of a shard. So `maxUnavailable: 1`.
- With `number_of_replicas: 2` (three copies), you can tolerate two nodes down simultaneously: `maxUnavailable: 2`.

```yaml
# PDB for a hot tier running number_of_replicas: 1
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: opensearch-data-hot
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app: opensearch
      role: data
      category: hot
```

If you raise your indexes to two replicas, raise the PDB to `maxUnavailable: 2` to match, and vice versa. The PDB and the replica count are two halves of the same guarantee: the PDB must never allow more nodes to be disrupted at once than your replication can survive.

### How the two work together

`do-not-disrupt` stops the autoscaler from rotating hot nodes on its own initiative. The PDB bounds the blast radius of any disruption that does happen (including the deliberate ones you trigger) to what your replicas can cover. With both in place, replication's safety guarantee, "there is always another copy", is never quietly violated by the orchestration layer.

## When to Reach for Instance Store

Use locally-attached NVMe instance store for your OpenSearch hot data tier when:

- Indexing throughput and query latency are your bottleneck.
- Your dataset on the hot tier exceeds RAM, so reads actually hit disk.
- You run `number_of_replicas >= 1` with AZ-aware allocation.
- You have a safe node-rotation / blue-green process in place.

Stick with EBS when:

- You need the disk to survive instance termination without relying on replication (for example, single-node setups, or tiers where you have chosen zero replicas).
- Your workload is high-residency and served mostly from RAM, where the latency gap disappears.
- Operational simplicity (snapshots, resize, detach/reattach) outweighs the raw performance gain.

## Conclusion (Author Opinion)

Instance store used to make me nervous, and I understand why it makes other people nervous too. The word "ephemeral" sounds like a trap for a stateful system. But once I internalized that replication means no single disk is ever the only copy, the fear turned into a deliberate engineering trade I am comfortable making on hot tiers.

It is not a reckless shortcut. You accept that any single disk is disposable, and you lean on OpenSearch's distributed design to make that disposability safe. In exchange you get storage performance that network-attached disks simply cannot match. On a hot tier backed by replicas and AZ-aware allocation, with a safe rotation process (and the right Kubernetes guardrails), I recommend it. Just make sure the controls are actually in place before you rely on them.

## References

- <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html>
- <https://opensearch.org/docs/latest/tuning-your-cluster/availability-and-recovery/>
- <https://karpenter.sh/docs/concepts/disruption/>

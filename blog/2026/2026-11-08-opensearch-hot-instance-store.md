---
tags: opensearch, aws, kubernetes
date: "2026-11-08"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/11/08*

---

# OpenSearch + EC2 Instance Store: A Disruptive Approach to Hot Tier Storage

This blog post covers running the OpenSearch Hot Data Tier on EC2 Instance Store (local NVMe) instead of EBS: why it performs better for this workload, and how to manage the risk of data loss with OpenSearch replication, Kubernetes, and Karpenter.

## Instance Store: Less Durability, More Performance

I've been managing OpenSearch clusters on [EKS](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) for over five years, handling ingestion rates of around 70K~100K documents per second. During this time, I've worked on improving indexing throughput, reducing query latency, and optimizing infrastructure costs. One of the most important changes was introducing hot, warm, and cold storage tiers to handle different data access patterns more efficiently. As the clusters grew, however, the hot tier became a performance bottleneck.

I experimented with different EC2 instance families and increased CPU and memory, but the metrics consistently pointed to storage I/O as the limiting factor. This led me to test [Storage Optimized EC2 instances](https://aws.amazon.com/ec2/instance-types/storage-optimized) with local NVMe Instance Store for the hot data nodes. The results were very good: the local disks gave us the performance we needed and reduced storage costs compared with EBS.

There is an important trade-off, though. Instance Store disks are tied to the physical EC2 host. If an instance is stopped, terminated, or hits a host failure, its local data is permanently lost. That makes Instance Store less durable, but it does not make it unsuitable for OpenSearch. The key is understanding how [shard replication](https://docs.opensearch.org/latest/tuning-your-cluster/availability-and-recovery/replica-shards) works (I covered the basics in [OpenSearch Concepts - Index and Shards](/blog/2025/2025-01-05-opensearch-concepts-index-and-shards.md)) and designing the infrastructure so that losing a node never means losing the only copy of its data.

For more on performance, see these public benchmarks and case studies:

- [Tuning Your Cluster for Indexing Speed (by OpenSearch)](https://docs.opensearch.org/latest/tuning-your-cluster/performance): Official OpenSearch guidance on indexing performance, including recommendations for SSD-backed Instance Store and storage configuration.
- [Postgres Isn't Slow. Your Storage Is (by ClickHouse)](https://clickhouse.com/blog/posette-talk-recap-postgres-isnt-slow-your-storage-is): Benchmark comparing EBS gp3 and local NVMe Instance Store using PostgreSQL workloads. Reports significant improvements in transaction throughput and latency with local NVMe.
- [Amazon EC2 i3.metal Review (by StorageReview)](https://www.storagereview.com/review/amazon-ec2-i3-metal-review): Storage benchmark comparing EBS and local NVMe on EC2 i3.metal instances, including random read/write IOPS and sequential throughput.

## EC2 Instance Store vs. EBS

The difference comes down to where the disk is. An EBS volume is a network-attached block device that exists independently of any EC2 instance, so every I/O makes a network round trip. Instance Store is an NVMe SSD attached to the host's PCIe bus, with no network in the path.

| | EBS (gp3) | Instance Store (local NVMe) |
|---|---|---|
| Attachment | Network-attached, independent of the instance | Physically attached to the host |
| Survives stop or terminate | Yes, and can be detached and reattached | No, the data is lost |
| Performance | [3,000 IOPS and 125 MiB/s baseline](https://docs.aws.amazon.com/ebs/latest/userguide/general-purpose.html), provisioned higher if needed and capped by the instance's EBS bandwidth | Fixed by the instance type, with no network hop |
| Size | Chosen per volume, can grow | Fixed by the instance type, e.g. 1 x 1,875 GB on an [`i8g.2xlarge`](https://aws.amazon.com/ec2/instance-types/i8g/) |
| Cost | Billed separately per GB-month, plus provisioned IOPS and throughput above the baseline | Included in the instance price |

Local NVMe is not faster for every workload. For large sequential reads and writes, where most of the active data fits in RAM, a `gp3` volume on an instance with enough EBS bandwidth can keep up with local drives, and the bottleneck becomes the instance's EBS bandwidth rather than the disk.

Small random reads are where local NVMe clearly wins, because removing the network hop removes latency from every single I/O. This is the access pattern that matters for a search engine. When an OpenSearch hot tier serves queries against indices larger than the available RAM, [Lucene](https://lucene.apache.org/core/9_12_0/core/org/apache/lucene/search/package-summary.html) has to read many small blocks from disk, and local storage answers those reads faster.

For most stateful applications, EBS remains the sensible default. In a distributed search system where shard replication already handles node failure, the durability EBS adds matters less, and local NVMe removes storage latency as the bottleneck.

## Why Instance Store Works for OpenSearch

OpenSearch splits index data into shards and can keep [replica copies](https://docs.opensearch.org/latest/tuning-your-cluster/availability-and-recovery/replica-shards) of each shard on different data nodes. When a hot data node fails, its local NVMe data is gone, but if another node holds a valid copy of each affected shard, OpenSearch promotes those replicas to primary and allocates new replicas on the remaining nodes. Once a replacement node joins the cluster, it receives shard copies and the configured redundancy is restored.

This is what makes it possible to treat Instance Store disks as disposable, as long as every shard has another valid copy on a different node. The risk is losing several nodes that hold copies of the same shard before OpenSearch finishes recovering. So Instance Store is viable only when replication, placement, and node replacement are designed together. If you want more detail on how OpenSearch decides where shards go, see [OpenSearch Shard Allocation: Balanced by Count, Rebalanced by Watermarks](/blog/2026/2026-11-04-opensearch-watermark.md).

## Running Instance Store Safely on Kubernetes

The following six mechanisms combine OpenSearch, Kubernetes, and Karpenter features to reduce the risk of data loss. They cover three areas: shard redundancy, workload placement, and controlled node replacement.

These mechanisms reduce risk during controlled operations, but they cannot guarantee durability. If multiple nodes fail before OpenSearch recovers their shard copies, data can still be lost. Using Instance Store means accepting that trade-off in exchange for performance. When durability is the priority, EBS remains the safer choice.

### 1. Ensure All Indices Have Replicas

Every index stored on Instance Store nodes needs at least one replica. Without replicas, a node failure can permanently remove the only copy of a shard. An [index template](https://docs.opensearch.org/latest/im-plugin/index-templates) can set a default replica count for new indices:

```{code-block} json
:caption: PUT /_index_template/default-replicas
{
  "index_patterns": ["*"],
  "template": {
    "settings": {
      "number_of_replicas": 1
    }
  }
}
```

This template only applies to new indices. Existing indices must be checked and updated separately, and explicit index settings or other templates with a higher `priority` can override it. Validate and monitor replica counts so that no index is left without redundancy.

### 2. Use StatefulSets for Hot Data Nodes

[StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) give each pod a stable identity and a predictable name, which helps when managing OpenSearch nodes that use local storage. With the default `RollingUpdate` strategy, Kubernetes replaces StatefulSet pods one at a time and waits for each updated pod to become Ready before moving to the next one. This prevents multiple hot data nodes from being replaced at the same time during an update.

Stable pod names are also useful when decommissioning or migrating nodes. For example, before removing `opensearch-hot-3`, you can ask OpenSearch to move its shards elsewhere by excluding it from shard allocation:

```{code-block} json
:caption: PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.exclude._name": "opensearch-hot-3"
  }
}
```

OpenSearch then relocates the shards away from the excluded node, and once relocation finishes, the node can be removed safely. This requires the OpenSearch `node.name` to match the pod name. After the operation, clear the exclusion setting so the node can receive shards again.

### 3. One Hot Data Pod per Worker Node

If two OpenSearch hot data pods run on the same Kubernetes worker, one EC2 failure takes down both, and they may hold the primary and the replica of the same shard. Running at most one hot data pod per worker keeps each EC2 instance a separate failure domain.

The following configuration uses [pod anti-affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) to keep hot pods on separate Kubernetes nodes. You can combine it with node affinity to select dedicated hot-tier workers and [topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints) to distribute the pods across Availability Zones.

```{code-block} yaml
:caption: opensearch-data-hot-statefulset.yaml
spec:
  template:
    metadata:
      labels:
        app: opensearch-hot
    spec:
      affinity:
        # Ensure only one OpenSearch hot pod per Kubernetes node
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: opensearch-hot
              topologyKey: kubernetes.io/hostname
```

OpenSearch also supports [shard allocation awareness](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-awareness), which tags nodes with their failure domain, such as the Availability Zone, so that OpenSearch places a shard's copies in different zones. Keep in mind that cross-AZ traffic increases AWS data transfer costs.

### 4. Use a Readiness Probe to Wait for Cluster Green

An OpenSearch node that answers HTTP requests is not necessarily safe to move past. The process can be up before the cluster has recovered its shards and restored replica redundancy. A [readiness probe](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes) that only checks the HTTP endpoint lets Kubernetes replace the next pod too early.

Instead, the probe can call the [Cluster Health API](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-health) and only report Ready when the cluster is green. Because the StatefulSet rolling update waits for each pod to be Ready, Kubernetes now waits for shard recovery before replacing the next pod. Set `timeoutSeconds` above the API's own `timeout`; the default probe timeout is one second, which would make the probe fail while the request is still waiting:

```{code-block} yaml
:caption: opensearch-data-hot-statefulset.yaml
readinessProbe:
  timeoutSeconds: 10
  exec:
    command:
      - sh
      - -c
      - |
        curl -sSkf \
        -u "${USER}:${PASS}" \
        "${URL}/_cluster/health?wait_for_status=green&timeout=5s" \
        | jq -e '.status == "green" and .timed_out == false'
```

This check is cluster-wide. If any index turns yellow for an unrelated reason, every hot pod becomes NotReady at the same time, and Kubernetes removes all of them from the endpoints of any Service that selects them. Make sure clients reach the cluster through a Service that does not depend on this probe, such as one that points to coordinating nodes.

### 5. Use a PodDisruptionBudget (PDB)

A [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb) limits how many pods can be voluntarily evicted at the same time, for example while Kubernetes drains a worker node. The following PDB allows at most one hot data pod to be unavailable due to voluntary disruptions:

```{code-block} yaml
:caption: opensearch-data-hot-pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: opensearch-hot
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app: opensearch-hot
```

Choose `maxUnavailable` according to the cluster size, replica configuration, and failure tolerance. A limit of one is reasonable for many clusters, but it is not universally safe. A PDB also only covers evictions made through the [Eviction API](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction). It does not prevent involuntary failures, such as an EC2 instance interruption, and it does not control pod replacements made by a StatefulSet rolling update.

### 6. Control Node Disruptions with Karpenter

> I'll use Karpenter as an example, but the same logic applies to any node autoscaler.

Karpenter can replace nodes for several reasons, including consolidation and drift from the desired [NodePool](https://karpenter.sh/docs/concepts/nodepools) configuration. With Instance Store, terminating a node destroys its local data, so these replacements must be coordinated with OpenSearch shard recovery. Karpenter provides [disruption controls](https://karpenter.sh/docs/concepts/disruption/) for this.

One option is to add the `karpenter.sh/do-not-disrupt` annotation to the pod template. Karpenter will not voluntarily disrupt a node running the annotated pod, subject to the documented exceptions:

```{code-block} yaml
:caption: opensearch-data-hot-statefulset.yaml
spec:
  template:
    metadata:
      annotations:
        karpenter.sh/do-not-disrupt: "true"
```

Drift needs separate attention. When a node no longer matches its NodePool configuration, Karpenter may replace it, and for Instance Store hot nodes that means unplanned data movement and local data loss. A NodePool disruption budget set to zero for the `Drifted` reason stops Karpenter from voluntarily replacing drifted nodes:

```{code-block} yaml
:caption: opensearch-karpenter-nodepool.yaml
spec:
  disruption:
    budgets:
      - nodes: "0"
        reasons:
          - Drifted
```

When a node needs to be updated, adjust the budget to allow a controlled replacement, one node at a time.

Each of these mechanisms covers a different kind of disruption. The readiness probe and the StatefulSet rolling update control the order of pod replacements during an update. The PDB limits voluntary evictions, such as Karpenter draining a node, but not StatefulSet-initiated replacements. The `do-not-disrupt` annotation and the NodePool budget stop Karpenter from replacing nodes on its own. None of them protects against unexpected infrastructure failures, such as an EC2 instance interruption.

## Takeaways

- Neither Instance Store nor EBS is better in general. EBS is durable and flexible; Instance Store trades durability for lower latency.
- For an OpenSearch hot tier that serves queries on indices larger than RAM, the small random reads favor local NVMe.
- Instance Store data is lost when the EC2 instance stops, terminates, or fails, so every index needs replicas.
- Kubernetes and Karpenter guardrails (StatefulSet rolling updates, a green-cluster readiness probe, PDBs, anti-affinity, and disruption budgets) control planned replacements. Replication is what protects against unplanned ones.

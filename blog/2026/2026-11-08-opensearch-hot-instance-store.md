---
tags: opensearch, aws, kubernetes
date: "2026-11-08"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/11/08*

---

# OpenSearch + EC2 Instance Store: A Disruptive Approach to Hot Tier Storage

This blog post covers an architectural approach for running the OpenSearch Hot Data Tier using EC2 Instance Store (local NVMe) instead of EBS, exploring performance gains and how to manage the risks of data loss through OpenSearch replication, Kubernetes, and Karpenter.

## Instance Store: Less Durability, More Performance

I've been managing OpenSearch clusters on [EKS](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) for over five years, handling ingestion rates of around 70K~100K documents per second. During this time, I've worked on improving indexing throughput, reducing query latency, and optimizing infrastructure costs. One of the most important changes was introducing hot, warm, and cold storage tiers to handle different data access patterns more efficiently. As the clusters grew, however, the hot tier eventually became a performance bottleneck.

I experimented with different EC2 instance families and increased CPU and memory resources, but the metrics consistently pointed to storage I/O as the limiting factor. This led me to test [Storage Optimized EC2 instances](https://aws.amazon.com/ec2/instance-types/storage-optimized) equipped with local NVMe Instance Store instead of EBS for hot data nodes. The results were very good: the local disks provided the performance we needed while significantly reducing storage costs compared with EBS.

There is an important trade-off, though. Unlike EBS volumes, Instance Store disks are tied to the physical EC2 host. If an instance is stopped, terminated, or experiences a host failure, its local data is permanently lost. This makes Instance Store a less durable storage option, but it does not necessarily make it unsuitable for OpenSearch. The key is to understand how [shard replication](https://docs.opensearch.org/latest/tuning-your-cluster/availability-and-recovery/replica-shards) works and design the infrastructure so that losing a node does not mean losing the only copy of its data.

For more information about performance, see these publicly available benchmarks and case studies:

- [Tuning Your Cluster for Indexing Speed (by OpenSearch)](https://docs.opensearch.org/latest/tuning-your-cluster/performance): Official OpenSearch guidance on indexing performance, including recommendations for SSD-backed Instance Store and storage configuration.
- [Postgres Isn't Slow. Your Storage Is (by ClickHouse)](https://clickhouse.com/blog/posette-talk-recap-postgres-isnt-slow-your-storage-is): Benchmark comparing EBS gp3 and local NVMe Instance Store using PostgreSQL workloads. Reports significant improvements in transaction throughput and latency with local NVMe.
- [Amazon EC2 i3.metal Review (by StorageReview)](https://www.storagereview.com/review/amazon-ec2-i3-metal-review): Storage benchmark comparing EBS and local NVMe on EC2 i3.metal instances, including random read/write IOPS and sequential throughput.

## EC2 Instance Store vs. EBS

The choice between EBS and Instance Store comes down to physical location and how your application accesses storage. EBS volumes operate as network-attached block devices that exist independently of any individual EC2 instance. Instance Store, by contrast, relies on NVMe SSDs plugged directly into the host server’s PCIe bus, completely cutting out the network layer.

Local NVMe is not universally faster. For large-block, sequential workloads where a significant portion of the active dataset resides in RAM, a modern `gp3` volume running on a high-bandwidth Nitro instance can comfortably match or even edge out local drives on sustained throughput. In those scenarios, the performance bottleneck shifts away from the underlying storage media and lands squarely on the instance's allocated EBS network bandwidth.

Where local NVMe establishes an un-closable gap is small-block random read latency. Because EBS must traverse the virtualized network stack, it inevitably introduces microsecond-level overhead. Direct PCIe access bypasses that entirely, delivering sub-millisecond access times. This latency differential becomes the single most critical factor for search engines like OpenSearch. When an OpenSearch hot tier serves queries against indices that exceed available RAM, [Lucene index traversals](https://lucene.apache.org/core/9_12_0/core/org/apache/lucene/search/package-summary.html) trigger relentless random small-block reads, making local storage substantially more responsive.

The trade-off for that raw speed is persistence. An EBS volume acts as a stable baseline: it survives instance stops, can be detached, and scales its baseline 3,000 IOPS and 125 MiB/s up to specific operational needs. Instance Store storage, like the 1,875 GB NVMe drive baked into an `i8g.2xlarge`, is strictly ephemeral. If the host stops, hibernates, or fails, the local data vanishes.

For traditional stateful applications, EBS remains the sensible default. But in distributed search systems where application-level shard replication already handles node failure, local NVMe transforms storage latency from a persistent bottleneck into a solved problem.

## Why Instance Store Works for OpenSearch

OpenSearch distributes index data across shards and can maintain [replica copies](https://docs.opensearch.org/latest/tuning-your-cluster/availability-and-recovery/replica-shards) of each shard on different data nodes. This means a node failure does not necessarily result in data loss: if another node holds a valid copy of the affected shard, OpenSearch can promote that replica to primary and create new replicas to restore the configured redundancy.

This replication model makes it possible to treat Instance Store disks as disposable, provided that every shard has another valid copy on a different node. For example, when a hot data node fails, its local NVMe data is lost along with the instance. OpenSearch detects that the node is unavailable, promotes available replica shards to primary, and allocates new replicas across the remaining nodes. Once a replacement node joins the cluster, it can receive shard copies and restore the desired redundancy.

The important part is ensuring that shard copies are distributed across independent failure domains and that node replacement is controlled. If multiple nodes holding copies of the same shard fail before OpenSearch can recover, the remaining copies may be insufficient to prevent data loss. Instance Store is therefore viable when replication, placement, and disruption management are designed together.

## Running Instance Store Safely on Kubernetes

The following six mechanisms combine OpenSearch capabilities with Kubernetes and Karpenter features to reduce the risk of data loss. They address three important areas: shard redundancy, workload placement, and controlled node replacement.

It is important reinforce that these mechanisms mitigate risks under controlled failure scenarios, but they cannot guarantee durability. If multiple nodes fail before OpenSearch can recover their shard copies, data loss is still possible. Using Instance Store means accepting this durability trade-off in exchange for performance. EBS remains the safer choice when data durability is the priority.

### 1. Ensure All Indices Have Replicas

Every index stored on Instance Store nodes should have at least one replica. Without replicas, a node failure can permanently remove the only copy of a shard. An [index template](https://docs.opensearch.org/latest/im-plugin/index-templates) can establish a default replica count for newly created indices, ensuring that indices matching the configured pattern are created with the expected redundancy.

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

This template only sets the default for new matching indices. Existing indices must be checked and updated separately, and explicit index settings can override the template. For that reason, replica configuration should also be validated and monitored to ensure that no index is left without the required redundancy.

### 2. Use StatefulSets for Hot Data Nodes

StatefulSets provide stable pod identities and predictable names, which are useful when managing OpenSearch nodes that use local storage. Unlike Deployments, StatefulSets maintain an ordinal identity for each pod and, by default, use the [OrderedReady](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) pod management policy. During a rolling update, Kubernetes updates or replaces pods one at a time and waits for each pod to become ready before proceeding. This behavior helps prevent multiple hot data nodes from being replaced simultaneously.

Stable pod names are also useful when decommissioning or migrating nodes. For example, before removing `opensearch-hot-3`, you can ask OpenSearch to relocate its shards to other nodes by excluding it from shard allocation:

```{code-block} json
:caption: PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.exclude._name": "opensearch-hot-3"
  }
}
```

OpenSearch will then relocate the shards away from the excluded node. Once relocation is complete, the node can be safely removed from the cluster. This requires the OpenSearch `node.name` to match the pod identity used in the exclusion setting. After the decommissioning operation, remember to clear the exclusion setting so that the node can participate in shard allocation again.

### 3. One Node per Pod

Running one OpenSearch hot data node per Kubernetes pod makes node placement and lifecycle management easier to reason about. It also ensures that a single worker node failure does not take down multiple OpenSearch nodes, potentially affecting both copies of the same shard. By enforcing one hot data pod per worker node, Kubernetes provides an additional layer of failure isolation.

The following configuration uses [node affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) to select dedicated hot-tier workers, [pod anti-affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) to keep hot pods on separate Kubernetes nodes, and [topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints) to distribute them across Availability Zones.

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

OpenSearch also supports [index shard allocation awareness](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-awareness), which allows nodes to be assigned attributes representing their failure domains, such as Availability Zones. This gives OpenSearch additional context when distributing shard copies across zones. However, cross-AZ traffic can increase AWS VPC data transfer costs, so the trade-off should be considered when designing multi-AZ deployments.

### 4. Use a Readiness Probe to Wait for Cluster Green

A process responding to HTTP requests does not necessarily mean that an OpenSearch node is ready to handle workloads safely. The local service may become available before the cluster has recovered its shards and restored replica redundancy. A [readiness probe](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes) that only checks whether the HTTP endpoint responds can therefore allow Kubernetes to proceed with the next pod replacement too early.

Instead, the probe can use the [Cluster Health API](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-health) to wait until the cluster reaches a green state. Combined with the StatefulSet's [OrderedReady](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) policy, this makes Kubernetes wait for shard recovery before moving on to the next pod during a rolling update. Check following example:

```{code-block} yaml
:caption: opensearch-data-hot-statefulset.yaml
readinessProbe:
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

### 5. Use a PodDisruptionBudget (PDB)

A PodDisruptionBudget limits how many pods can be voluntarily evicted at the same time. This is particularly useful during node draining, when Kubernetes needs to move workloads away from a worker node. For example, the following PDB allows at most one hot data pod to be unavailable due to voluntary disruptions:

```{code-block} yaml
:caption: opensearch-data-hot-statefulset.yaml
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

The value of `maxUnavailable` must be chosen according to the cluster size, replica configuration, and failure tolerance. A limit of one may be reasonable for some clusters, but it is not universally safe. Also, a PDB only protects against voluntary evictions performed through Kubernetes' [Eviction API](https://kubernetes.io/docs/concepts/scheduling-eviction/api-eviction). It does not prevent involuntary failures, such as an EC2 instance interruption, or directly control pod replacements initiated by a StatefulSet rolling update.

### 6. Control Node Disruptions with Karpenter

> I'll use Karpenter as an example. However, the logic behind it remains the same for any node scheduling.

Karpenter can replace nodes for several reasons, including [consolidation](https://karpenter.sh/docs/concepts/disruption/) and [drift](https://karpenter.sh/docs/concepts/disruption/) from the desired [NodePool](https://karpenter.sh/docs/concepts/nodepools) configuration. For workloads using Instance Store, these operations require special attention because terminating a node permanently destroys its local data. Karpenter provides mechanisms to control voluntary disruptions, allowing node replacement to be coordinated with OpenSearch shard recovery.

One option is to add the `karpenter.sh/do-not-disrupt` annotation to the pod template. This tells Karpenter not to voluntarily disrupt the annotated pod, subject to documented exceptions. See [Pod-level Disruption Controls](https://karpenter.sh/docs/concepts/disruption/).

```{code-block} yaml
:caption: opensearch-data-hot-statefulset.yaml
spec:
  template:
    metadata:
      annotations:
        karpenter.sh/do-not-disrupt: "true"
```

Another concern is drift. When a node no longer matches its NodePool configuration, Karpenter may replace it to bring the infrastructure back in line with the desired state. For hot data nodes using Instance Store, automatic drift replacement can result in unnecessary data movement and local data loss. A [NodePool Disruption Budget](https://karpenter.sh/docs/concepts/disruption/) can prevent Karpenter from voluntarily replacing drifted nodes while the budget is set to zero:

```{code-block} yaml
:caption: opensearch-karpenter-nodepool.yaml
spec:
  disruption:
    budgets:
      - nodes: "0"
        reasons:
          - Drifted
```

This blocks voluntary drift-related replacements while the budget is active. When a node needs to be updated, the budget can be adjusted to allow a controlled replacement process. The `do-not-disrupt` annotation and NodePool disruption budgets serve different purposes and should be configured with an understanding of [Karpenter's disruption rules and exceptions](https://karpenter.sh/docs/concepts/disruption).

These mechanisms protect against different types of disruption. The readiness probe, combined with the StatefulSet's [OrderedReady](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) policy, controls the sequence of pod replacements during a StatefulSet rolling update. The [PodDisruptionBudget](https://kubernetes.io/docs/tasks/run-application/configure-pdb) limits voluntary evictions, such as those performed during Karpenter node draining, but does not prevent StatefulSet-initiated pod replacements. The `karpenter.sh/do-not-disrupt` annotation blocks voluntary Karpenter disruptions for the annotated pod, subject to [Karpenter's documented exceptions](https://karpenter.sh/docs/concepts/disruption/). None of these mechanisms protects against unexpected infrastructure failures, such as an EC2 instance interruption.

## Takeaways

The blog post presented several technical considerations and disruptive approaches. Let's summarize the main points:

- Instance Store is neither better nor faster than EBS, nor is EBS inherently better than Instance Store. Each has its own use cases.
- For the OpenSearch Hot Data Tier, Instance Store delivers better performance.
- Instance Store is lost when the EC2 node fails, making it a riskier approach.
- The risks of using Instance Store can be controlled through application-level data replication mechanisms and Kubernetes guardrails.

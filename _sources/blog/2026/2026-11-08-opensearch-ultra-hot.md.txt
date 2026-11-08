---
tags: opensearch, aws, kubernetes, performance
date: "2026-11-08"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/11/08*

---

# OpenSearch + EC2 Instance Store: A Disruptive Approach to Hot Tier Storage

This blog post covers how to run OpenSearch on EC2 Instance Store, from storage performance and shard replication to multi-AZ placement, safe rollouts, data migration, and disruption control with Kubernetes and Karpenter.

## Why Instance Store?

I've been managing OpenSearch clusters running on EKS for over five years, handling ingestion rates of around 70K–100K documents per second. Throughout this experience, I've worked on improving indexing throughput, query latency, and infrastructure costs.

One of the strategies I introduced was storage tiering, separating hot, warm, and cold data according to access patterns. This helped reduce costs, but the hot tier eventually became a performance bottleneck.

I tried different EC2 families, increasing CPU and memory, but the results were disappointing. After investigating the cluster metrics, I identified storage I/O as the main bottleneck.

At that point, I decided to try something different: using storage-optimized EC2 instances with local NVMe Instance Store instead of EBS for hot data nodes.

The results were very good. I achieved the performance I was looking for while reducing storage costs compared to my previous EBS-based configuration.

There was one concern, though: Instance Store is ephemeral. If an instance is terminated or its underlying host fails, its local data is lost. For a stateful system like OpenSearch, this introduces an important operational challenge.

This article explains why I chose this approach and how OpenSearch replication and Kubernetes configurations can make it a viable strategy.

## EC2 Instance Store vs. EBS

The main difference between these storage options is where the data physically resides. EBS is network-attached block storage. Instance Store uses local NVMe SSDs physically attached to the EC2 host. This difference affects both performance and data durability.

With EBS, performance depends on the volume configuration and the instance's available EBS bandwidth. For example, a `gp3` volume starts with 3,000 IOPS and 125 MiB/s, with higher limits available at additional cost. For more, see [AWS EBS documentation](https://docs.aws.amazon.com/ebs/latest/userguide/general-purpose.html).

Instance Store provides local storage without a separate EBS volume or provisioned IOPS charge. Its performance depends on the instance family and local SSD capabilities. For example, an `i8g.2xlarge` provides 8 vCPUs, 64 GiB of memory, and 1,875 GB of local NVMe storage. For more, see [AWS I8g specifications](https://aws.amazon.com/ec2/instance-types/i8g/).

For I/O-intensive workloads, this can be an interesting cost-performance advantage. Local NVMe is particularly attractive when the hot dataset generates frequent disk reads and writes.

However, there is an important trade-off: EBS volumes persist independently of the EC2 instance, while Instance Store data is lost when the instance is stopped, terminated, or hibernated. Instance Store volumes cannot be detached and attached to another instance. [AWS Instance Store documentation](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-store-lifetime.html).

Therefore, the choice depends on the workload. EBS provides persistence and operational flexibility. Instance Store prioritizes local storage performance and can reduce the need for expensive EBS configurations.

## Why Instance Store Works for OpenSearch

OpenSearch already has a mechanism that makes this architecture possible: shard replication. Each index is divided into primary shards, with replica shards providing additional copies of the data. OpenSearch distributes a primary shard and its replicas across different nodes, allowing the cluster to recover when a node becomes unavailable. [OpenSearch replication documentation](https://docs.opensearch.org/latest/getting-started/intro/).

For hot data nodes using Instance Store, this means local disks can be treated as disposable storage, provided that another valid copy of every shard is available elsewhere.

For example, with one replica configured:

1. A data node fails and its local NVMe data is lost.
2. OpenSearch detects the node failure.
3. The replica shards on surviving nodes can be promoted to primaries.
4. OpenSearch creates new replicas to restore redundancy.

This is the foundation of the architecture: instead of relying on persistent local storage, we rely on OpenSearch's distributed storage model to recover from node failures.

However, replication alone is not enough. Shard copies must be distributed across independent failure domains, and node replacement must be controlled to give the cluster enough time to recover.

## Running Instance Store Safely on Kubernetes

The following six mechanisms combine OpenSearch capabilities with Kubernetes and Karpenter features to reduce the risk of data loss. They address three important areas: shard redundancy, workload placement, and controlled node replacement.

__NOTE:__ It is important to understand that these mechanisms only mitigate the risks under controlled failure scenarios. If multiple nodes fail before OpenSearch can recover their shard copies, data loss is still possible. Using Instance Store means accepting this durability trade-off in exchange for performance. EBS remains the safer choice when data durability is the priority.

### 1. Ensure All Indices Have Replicas

Every index must have at least one replica. Without replicas, losing a node also means permanently losing the shard copies stored on its local disk. You can define the default number of replicas for newly created indices using an index template:

```json
PUT /_index_template/default-replicas
{
  "index_patterns": ["*"],
  "template": {
    "settings": {
      "number_of_replicas": 1
    }
  }
}
```

This sets one replica as the default for matching indices. Existing indices must be checked and updated separately. Replicas provide protection only while another healthy copy exists. Replacing multiple nodes before recovery completes can still result in data loss.

### 2. One Node per Pod, Across Availability Zones

Run one OpenSearch Data Hot node per Pod. This provides a clear mapping between Kubernetes pods and OpenSearch nodes, making node-level operations and failure recovery easier to manage.

Whenever possible, distribute these pods across different Availability Zones using Kubernetes topology spread constraints or pod anti-affinity. This reduces the chance of losing multiple shard copies due to a single AZ failure.

OpenSearch replicas should also be allocated across different nodes. With awareness of the cluster's AZ topology, shard allocation can keep primary and replica copies in separate failure domains. This way, losing a node or an entire AZ does not necessarily mean losing access to the shard's data.

However, this protection depends on having enough nodes and replicas distributed across independent failure domains. If another copy is lost before OpenSearch completes recovery, data loss is still possible.

The following Kubernetes configuration combines node affinity, pod anti-affinity, taints, tolerations, and topology spread constraints to control pod placement:

```yaml
# opensearch-data-hot-statufulset.yaml

spec:
  template:
    metadata:
      labels:
        app: opensearch-hot
    spec:
      affinity:
        # Schedule only on dedicated OpenSearch hot nodes
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: workload
                    operator: In
                    values:
                      - opensearch-hot

        # Ensure only one OpenSearch hot pod per Kubernetes node
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: opensearch-hot
              topologyKey: kubernetes.io/hostname

      # Allow pods to run on nodes tainted for OpenSearch
      tolerations:
        - key: workload
          operator: Equal
          value: opensearch-hot
          effect: NoSchedule

      # Spread pods evenly across Availability Zones
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: opensearch-hot
```

Kubernetes handles pod placement, while OpenSearch shard allocation awareness must be configured separately to distribute primary and replica shards across Availability Zones.

For example, configure the AZ as an allocation awareness attribute:

```yaml
# opensearch.yml
cluster.routing.allocation.awareness.attributes: zone
```

Each OpenSearch node must also expose its Availability Zone:

```yaml
# Example for a node in us-east-1a
node.attr.zone: us-east-1a
```

The attribute value must match the actual AZ of each node.

### 3. Use StatefulSets for Hot Data Nodes

StatefulSets are a good fit for OpenSearch hot data nodes. Unlike Deployments, they provide stable pod identities and predictable names. Their default `OrderedReady` policy also allows pods to be updated or replaced one at a time, waiting for each pod to become ready before proceeding.

Predictable node names are useful for data management operations as well. For example, when decommissioning nodes or migrating data to a new StatefulSet, you can use the OpenSearch `cluster.routing.allocation.exclude._name` cluster setting to prevent shards from being allocated to specific nodes.

```json
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.exclude._name": "opensearch-hot-3"
  }
}
```

This tells OpenSearch to relocate shards away from the specified node before it is removed. To make this work reliably, configure `node.name` to match the predictable pod identity.

### 4. Use a Readiness Probe to Wait for Cluster Green

A pod can become responsive before OpenSearch has recovered its shards or completed replication. A readiness probe that only checks whether the local HTTP endpoint responds is therefore insufficient.

Instead, the readiness probe should verify that the OpenSearch cluster has reached green before reporting the pod as ready. Combined with a StatefulSet using the `OrderedReady` policy, this gives OpenSearch time to restore shard redundancy before Kubernetes proceeds with the next pod replacement.

OpenSearch provides the [Cluster Health API](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-health/#query-parameters), which supports the `wait_for_status` parameter. You can use it to wait for the cluster to reach green:

```yaml
readinessProbe:
  exec:
    command:
      - sh
      - -c
      - curl -s -k -f -u "$OPENSEARCH_USER:$OPENSEARCH_PASS" "$OPENSEARCH_URL/_cluster/health?wait_for_status=green&timeout=5s") | grep -q '"status":"green"'
```

Green cluster health means that all primary and replica shards are allocated. Waiting for this state before continuing a rollout gives OpenSearch time to restore redundancy after each replacement, reducing the risk of losing the last available copy of a shard if another node fails during the process.

> __NOTE__: An `OrderedReady` StatefulSet combined with a green readiness probe can prevent subsequent pods from being created during initial cluster bootstrap. If the first pod cannot reach green without additional nodes, Kubernetes will wait indefinitely before creating the next pod. The initial bootstrap process must account for this dependency.

### 5. Use a PodDisruptionBudget (PDB)

A PodDisruptionBudget provides an additional limit on voluntary pod evictions during node draining. For example, setting `maxUnavailable: 1` prevents the eviction API from voluntarily disrupting more than one available pod at a time.

```yaml
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

This adds another layer of protection during node maintenance and replacement.

> __NOTE__: PDBs only protect against voluntary disruptions handled through the Kubernetes Eviction API. They do not prevent involuntary disruptions, such as instance failures, or directly control rolling updates performed by workload controllers.

### 6. Control Node Disruptions with Karpenter

Pod-level readiness is only part of the solution. The node manager must also avoid replacing nodes while OpenSearch is still recovering data.

In this article, I'll use __Karpenter__ as the node manager because it is the technology I have hands-on experience with. The same principles apply to other node-management solutions: avoid replacing nodes too aggressively, and allow the workload to recover before starting another disruption.

For Karpenter, two mechanisms are particularly relevant.

__Prevent voluntary disruptions:__ The `karpenter.sh/do-not-disrupt: "true"` annotation prevents Karpenter from voluntarily disrupting a pod, subject to its documented exceptions.

Add it to the pod template:

```yaml
spec:
  template:
    metadata:
      annotations:
        karpenter.sh/do-not-disrupt: "true"
```

This helps prevent Karpenter from removing nodes hosting OpenSearch pods during voluntary disruption operations.

> NOTE: The `do-not-disrupt` annotation does not protect against forceful disruptions, such as instance interruptions or node failures.

__Prevent automatic rotation on drift:__ Karpenter can replace nodes when they drift from the desired NodePool configuration. With Instance Store, this means that a configuration change can trigger the termination of a node and permanently destroy its local data.

A disruption budget can block voluntary drift-related replacements:

```yaml
spec:
  disruption:
    budgets:
      - nodes: "0"
        reasons:
          - Drifted
```

This prevents Karpenter from voluntarily replacing drifted nodes while the budget is active. When a rotation is needed, the budget can be adjusted to allow a controlled replacement process.

## Takeaways

Running OpenSearch on EC2 Instance Store can deliver significant performance and cost benefits for I/O-intensive hot tiers. However, it requires a different approach to storage durability and node lifecycle management.

The key takeaways are:

- __Replication is essential:__ Every index must have replicas, and shard copies should be distributed across independent Availability Zones.
- __Kubernetes controls placement:__ Running one OpenSearch node per Pod and spreading pods across AZs helps reduce the impact of node and AZ failures.
- __Recovery must precede replacement:__ StatefulSets, readiness probes, and PodDisruptionBudgets help control how quickly nodes are replaced and give OpenSearch time to restore redundancy.
- __Node disruptions require coordination:__ Karpenter must be configured to avoid unnecessary voluntary replacements, especially when drift could trigger the termination of nodes holding local data.
- __Data loss is still possible:__ These mechanisms reduce operational risks but cannot guarantee durability when multiple nodes or failure domains are lost before replication completes.

Ultimately, Instance Store is a trade-off. You exchange the durability and flexibility of EBS for higher local storage performance and potentially lower costs. For workloads where hot-tier I/O is a major bottleneck, that trade-off can make sense, provided the architecture and operational procedures are designed around the ephemeral nature of the storage.

---
tags: opensearch, kubernetes, aws, observability
date: "2026-10-17"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# The Readiness Probe That Saves Your Data: Gating OpenSearch Pods on a Green Cluster

Here is a failure mode that bites teams running OpenSearch on Kubernetes, and it is especially vicious when your data nodes use ephemeral local storage. Kubernetes thinks a pod is "ready" the moment the process answers HTTP, so the orchestrator happily moves on to the next node, draining it, rotating it, scaling it down, while shards are still copying. Do that fast enough and you can delete the last surviving copy of a shard before its replica has finished rebuilding.

The fix is small but critical: a readiness probe that refuses to report ready until the cluster is green. This blog post explains why that one check prevents data loss during scale-up and scale-down, and walks through a probe script I have relied on in production.

## The Problem: "Running" Is Not "Safe to Rotate"

Kubernetes uses the readiness probe to decide two things: whether a pod should receive traffic, and (crucially for StatefulSets and node autoscalers) whether a rolling operation can proceed to the next pod.

A naive OpenSearch readiness probe just checks that the HTTP API responds:

```bash
# Naive probe: DANGEROUS for data nodes
curl -s -o /dev/null http://localhost:9200/
```

The OpenSearch process answers that call within seconds of starting, long before:

- it has recovered its shards from disk or peers,
- the cluster has re-replicated shards that were on a node you just replaced,
- the cluster has finished relocating shards during a rebalance.

So the pod flips to `Ready`, the StatefulSet controller (or Karpenter, or the cluster autoscaler) sees a green light, and it proceeds to disrupt the next node, while the cluster is still `yellow` (replicas missing) or `red` (primaries missing). Each disruption races ahead of recovery. Eventually two operations overlap on the two nodes holding the only copies of a shard.

With network-attached storage (EBS), a terminated node's disk survives, so you usually get away with it. With ephemeral instance storage (local NVMe), the disk is wiped the instant the node terminates. There is no recovering it. If the probe let the rotation outrun re-replication, that data is simply gone.

## Why Ephemeral Hot Nodes Raise the Stakes

Hot data nodes are frequently built on EC2 instance types with locally-attached NVMe SSDs (the `i`-family, for example) because that storage is dramatically faster than network-attached EBS, ideal for high-throughput indexing and near-real-time search. The trade-off is that instance storage is ephemeral: terminate or rotate the instance and the data on it is destroyed.

OpenSearch is designed to tolerate this through replication. Every shard has a copy on another node, so losing one node is survivable. But that guarantee only holds if you give the cluster time to rebuild the lost copy before you take down the node that holds the surviving one.

That timing guarantee is exactly what the readiness probe enforces. On ephemeral hot nodes it is not a nicety. It is the mechanism that turns "a node died" from a data-loss event into a non-event.

## The Solution: Gate the First Readiness on `wait_for_status=green`

The key insight is that a data node has two very different "ready" questions depending on its lifecycle phase:

1. During startup / after joining: "Is the whole cluster healthy enough that it is safe to continue the rolling operation?" Wait for green.
2. During steady-state: "Is this node still responding?" A simple liveness-style check is enough.

A good probe handles both. Here is a script (forked from the well-known Elasticsearch Helm chart pattern) that does exactly this:

```bash
#!/usr/bin/env bash -e

# If the node is starting up, wait for the cluster to be ready
# (wait_for_status=green). Once it has started, only check that the
# node itself is responding.

START_FILE=/tmp/.es_start_file
export NSS_SDB_USE_CACHE=no

http () {
  local path="${1}"
  local args="${2}"
  set -- -XGET -s
  if [ "$args" != "" ]; then
    set -- "$@" $args
  fi
  if [ -n "${OPENSEARCH_HEALTHCHECK_USERNAME}" ] && [ -n "${OPENSEARCH_HEALTHCHECK_PASSWORD}" ]; then
    set -- "$@" -u "${OPENSEARCH_HEALTHCHECK_USERNAME}:${OPENSEARCH_HEALTHCHECK_PASSWORD}"
  fi
  curl --output /dev/null -k "$@" "${OPENSEARCH_HEALTHCHECK_URL}${path}"
}

if [ -f "${START_FILE}" ]; then
  # Steady state: just confirm the node is answering.
  echo 'OpenSearch is already running, lets check the node is healthy'
  HTTP_CODE=$(http "/" "-w %{http_code}")
  RC=$?
  if [[ ${RC} -ne 0 ]]; then
    echo "healthcheck failed with RC ${RC}"
    exit ${RC}
  fi
  if [[ ${HTTP_CODE} == "200" ]]; then
    exit 0
  elif [[ ${HTTP_CODE} == "503" ]]; then
    exit 0
  else
    echo "healthcheck failed with HTTP code ${HTTP_CODE}"
    exit 1
  fi
else
  # First readiness: block until the CLUSTER is green.
  echo 'Waiting for cluster to become ready (wait_for_status=green&timeout=1s)'
  if http "/_cluster/health?wait_for_status=green&timeout=1s" "--fail" ; then
    touch ${START_FILE}
    exit 0
  else
    echo 'Cluster is not yet ready (wait_for_status=green)'
    exit 1
  fi
fi
```

### How it works

- __The sentinel file (`START_FILE`).__ The first time the probe sees a green cluster, it creates `/tmp/.es_start_file`. On every subsequent call, the file exists, so the probe switches to the lightweight "is this node answering?" check. This prevents the green-gate from blocking the node forever. Once it has safely joined a healthy cluster, you do not want transient yellow states (normal during indexing) to flap the pod out of service.
- __`wait_for_status=green&timeout=1s`.__ This is the heart of it. The OpenSearch health endpoint blocks for up to one second waiting for the cluster to reach green. If it is not green, the probe fails, the pod stays `NotReady`, and, critically, the rolling operation does not advance to the next node.
- __Steady-state tolerance of 503.__ Once started, a `503` can still mean "node is up but cluster is briefly unhealthy", which is acceptable for keeping an already-joined node in rotation.

## Wiring It Into the StatefulSet

The probe only helps if it is configured to actually gate the rollout. A representative data-hot StatefulSet readiness probe:

```yaml
readinessProbe:
  exec:
    command:
      - sh
      - /usr/share/opensearch/readiness-probe.sh
  failureThreshold: 3
  initialDelaySeconds: 10
  periodSeconds: 10
  successThreshold: 3
  timeoutSeconds: 5
```

Combine it with two more safeguards and the whole system becomes robust:

```yaml
# PodDisruptionBudget: never let more than one data node be down at once
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: os-data-hot
spec:
  maxUnavailable: 1
  selector:
    matchLabels:
      app: opensearch
      role: data
      category: hot
```

```yaml
# On the pod template: tell the autoscaler not to voluntarily evict this pod
metadata:
  annotations:
    karpenter.sh/do-not-disrupt: "true"
```

Together these form a layered defense:

| Layer | What it guarantees |
| --- | --- |
| `readinessProbe` with `wait_for_status=green` | A pod is only "ready" (and the rollout only advances) once the cluster has fully recovered. |
| `PodDisruptionBudget` (`maxUnavailable: 1`) | At most one data node is ever voluntarily disrupted at a time. |
| `karpenter.sh/do-not-disrupt` | The node autoscaler will not rotate these pods out from under you unexpectedly. |

## How This Plays Out During Scale Operations

Scale-down / node rotation. The StatefulSet controller takes down pod N. The replacement pod starts, and its readiness probe blocks on `wait_for_status=green`. While shards re-replicate onto the new (empty, ephemeral) node, the pod stays `NotReady`. The controller will not touch pod N-1 because, respecting the PDB of `maxUnavailable: 1`, only one pod may be unavailable. Only when the cluster goes green (meaning every shard has its full set of copies again) does the probe pass and the rollout proceed. The surviving copy of every shard is never deleted before its replacement exists.

Scale-up. A new data node joins. Its probe waits for green before advertising ready, so the cluster finishes allocating and balancing shards onto it before anything downstream assumes it is fully in service. No half-initialized node gets pulled into a subsequent operation.

Without the green gate, both of these scenarios can race recovery and, on ephemeral storage, destroy the only remaining copy of a shard.

## Conclusion (Author Opinion)

The probe is a dozen lines of bash, and the data it protects is irreplaceable. That gap is exactly why I treat the green gate as non-negotiable on any OpenSearch cluster backed by ephemeral storage. It is not the kind of optional hardening you get to the next quarter. It is the difference between a routine node rotation and an outage with permanent data loss.

My recommendation: gate the first readiness on `wait_for_status=green`, switch to a lightweight check after the first green via a sentinel file, and layer it with a PodDisruptionBudget of `maxUnavailable: 1` plus a do-not-disrupt annotation so only one node is ever in flight, and never unexpectedly. Set that up once and you can rotate nodes without holding your breath.

## References

- <https://opensearch.org/docs/latest/api-reference/cluster-api/cluster-health/>
- <https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/>
- <https://kubernetes.io/docs/tasks/run-application/configure-pdb/>

---
tags: kubernetes, scheduling
date: ""
category: Kubernetes
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---

# Node Scheduling in Kubernetes: nodeName, nodeSelector, nodeAffinity, and Taints

This blog post explains the four main ways to control where your Pods land in a Kubernetes cluster: `nodeName`, `nodeSelector`, node affinity, and taints with tolerations. It covers what each one does, how they differ, when to reach for which, and the one trap that trips people up: tolerations attract nothing, they only permit.

## Who Decides Where a Pod Runs?

By default, you do not pick the node your Pod runs on. The Kubernetes scheduler does. It looks at every Pod that needs a home, filters out the nodes that cannot take it, scores the ones that can, and places the Pod on the best fit. Most of the time this is exactly what you want. You should not care which node runs your stateless web app.

But sometimes you do care. You have GPU nodes and only the ML workloads should touch them. You have a licensed database that must run on a specific machine. You want to spread Pods across availability zones. You want to reserve a pool of nodes for one team. These are all scheduling constraints, and Kubernetes gives you four tools to express them.

The tricky part is that they work at different levels and in different directions. Three of them pull a Pod toward nodes. One of them pushes Pods away. Mixing them up is where the confusion starts, so let me go through each.

## nodeName: The Blunt Instrument

`nodeName` is the most direct option and the one you should almost never use. It is a field in the Pod spec that names a node outright.

```{code-block} yaml
:caption: pod-nodename.yaml

apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
  nodeName: kube-01
```

When `nodeName` is set, the scheduler is skipped entirely. The kubelet on `kube-01` just tries to run the Pod. That sounds convenient, but it throws away everything the scheduler does for you:

- If `kube-01` does not exist, the Pod never runs, and in some cases gets deleted.
- If `kube-01` has no room, the Pod fails with `OutOfcpu` or `OutOfmemory`. Nothing reschedules it elsewhere.
- Node names in cloud environments are rarely stable or predictable, so hardcoding one is fragile.

The Kubernetes docs are blunt about it: `nodeName` is meant for custom schedulers and advanced edge cases where you deliberately want to bypass scheduling. For everyday "pin this Pod to a specific kind of node", use one of the next three instead.

## nodeSelector: The Simple One

`nodeSelector` is the simplest way to constrain scheduling, and it covers a surprising number of real cases. You label your nodes, then tell the Pod to only run where those labels match.

First, label a node:

```{code-block} bash
:caption: label a node

kubectl label nodes kube-02 disktype=ssd
```

Then ask for it in the Pod spec:

```{code-block} yaml
:caption: pod-nodeselector.yaml

apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
  - name: nginx
    image: nginx
  nodeSelector:
    disktype: ssd
```

The scheduler will only consider nodes that carry the label `disktype=ssd`. If you list several labels, all of them must match (they are ANDed). Unlike `nodeName`, the scheduler still runs, so you keep bin-packing, resource checks, and rescheduling. This is the right default when your rule is a plain "must have these labels".

## nodeAffinity: nodeSelector With a Brain

Node affinity is `nodeSelector` with a richer grammar. It lives under `.spec.affinity.nodeAffinity` and comes in two flavors:

- __`requiredDuringSchedulingIgnoredDuringExecution`__: a hard rule. The scheduler will not place the Pod unless a node matches. This behaves like `nodeSelector`, just more expressive.
- __`preferredDuringSchedulingIgnoredDuringExecution`__: a soft rule with a weight. The scheduler tries to honor it, but if no matching node is available, it schedules the Pod anyway.

```{code-block} yaml
:caption: pod-nodeaffinity.yaml

apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values:
            - antarctica-east1
            - antarctica-west1
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 1
        preference:
          matchExpressions:
          - key: another-node-label-key
            operator: In
            values:
            - another-node-label-value
  containers:
  - name: with-node-affinity
    image: registry.k8s.io/pause:3.8
```

Two things make affinity more powerful than `nodeSelector`. First, operators: besides `In`, you get `NotIn`, `Exists`, `DoesNotExist`, `Gt`, and `Lt`, so you can match on absence or ranges, not just equality. Second, the soft `preferred` rules, which let you express "I'd rather run here, but do not block me if you cannot".

A few rules on how the matching combines, because they are easy to get wrong:

- If you set both `nodeSelector` and `nodeAffinity`, both must be satisfied.
- Multiple `nodeSelectorTerms` are ORed: matching any one term is enough.
- Multiple expressions inside a single `matchExpressions` are ANDed: all must match.

> <i class="fa-solid fa-circle-info"></i> `IgnoredDuringExecution` means the rule is checked only at scheduling time. If a node's labels change after the Pod is already running, the Pod stays put. It is not re-evaluated and evicted.

## Taints and Tolerations: Pushing Pods Away

Here is the one that works in the opposite direction, and the source of most confusion. The three tools above attract Pods to nodes. Taints repel Pods from nodes.

A **taint** is applied to a node and says "keep Pods off me unless they explicitly put up with this". A **toleration** is applied to a Pod and says "I can put up with that taint". No toleration, no scheduling on that node.

Taint a node like this:

```{code-block} bash
:caption: taint a node

kubectl taint nodes node1 key1=value1:NoSchedule
```

And let a Pod tolerate it:

```{code-block} yaml
:caption: toleration in a Pod spec

tolerations:
- key: "key1"
  operator: "Equal"
  value: "value1"
  effect: "NoSchedule"
```

The `operator` can be `Equal` (key and value must match) or `Exists` (only the key must be present, no value needed). The `effect` is where the real behavior lives:

- __`NoSchedule`__: no new Pod schedules here without a matching toleration. Pods already running stay.
- __`PreferNoSchedule`__: the soft version. The scheduler tries to avoid the node, but will use it if it has to.
- __`NoExecute`__: the strict one. New Pods without a toleration will not schedule, and Pods already running that do not tolerate it are evicted.

With `NoExecute` you can also set `tolerationSeconds`, which keeps a tolerating Pod on the node for a grace period before eviction. Kubernetes itself uses this for node problems:

```{code-block} yaml
:caption: tolerate an unreachable node for 100 minutes

tolerations:
- key: "node.kubernetes.io/unreachable"
  operator: "Exists"
  effect: "NoExecute"
  tolerationSeconds: 6000
```

## The Trap: A Toleration Does Not Attract

This is the mistake I see most often, so it gets its own section. People taint their GPU nodes, add a matching toleration to the GPU Pods, and assume the GPU Pods will now run on the GPU nodes.

They will not. Or rather, they _might_, but nothing guarantees it.

A toleration only removes a barrier. It says "this Pod is allowed on the tainted node". It does not say "this Pod wants the tainted node". A Pod that tolerates the GPU taint is now free to land on the GPU nodes, but it is equally free to land on any untainted node in the cluster, and the scheduler may well put it there.

To actually dedicate nodes to a workload, you need both halves:

- __Taint__ the special nodes so random Pods stay off them.
- __Toleration + nodeAffinity (or nodeSelector)__ on the special Pods, so they are both allowed on those nodes _and_ pulled toward them.

```{code-block} yaml
:caption: dedicate GPU nodes properly

apiVersion: v1
kind: Pod
metadata:
  name: gpu-job
spec:
  # allowed onto the tainted GPU nodes
  tolerations:
  - key: "gpu"
    operator: "Equal"
    value: "true"
    effect: "NoSchedule"
  # and actively steered toward them
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: hardware
            operator: In
            values:
            - gpu
  containers:
  - name: trainer
    image: my-ml-image
```

The taint keeps everyone else off the GPU nodes. The toleration lets this Pod in. The affinity makes sure it goes there and not somewhere else. All three jobs are needed, and leaving one out is the usual reason a "dedicated node" setup quietly misbehaves.

## Which One Should I Use?

A short decision guide, from how I reach for them:

- __`nodeSelector`__: your rule is a simple label match and nothing more. Start here.
- __`nodeAffinity`__: you need soft preferences, negation, ranges, or OR logic. The grown-up version of `nodeSelector`.
- __Taints + tolerations__: you want to keep most Pods _off_ a set of nodes (dedicated pools, special hardware, control-plane nodes). Pair it with affinity to also pull the right Pods in.
- __`nodeName`__: almost never. Only for custom schedulers or a deliberate bypass, and accept the fragility.

## Conclusion (Author Opinion)

When I first learned these, I lumped them all together as "node scheduling stuff" and kept getting surprised. The thing that finally made it click was the direction. Three of them are magnets pulling Pods toward nodes, and taints are a fence keeping Pods out. Once I held that picture in my head, the behavior stopped being mysterious.

My advice is to keep it as simple as the problem allows. Reach for `nodeSelector` first, graduate to `nodeAffinity` when you actually need its expressiveness, and only bring in taints when you genuinely need to reserve nodes. And please do not pin Pods with `nodeName` unless you know exactly why you are bypassing the scheduler.

The one rule I would tattoo on a new cluster admin: a toleration permits, it never attracts. Remember that and most of the "why did my Pod end up there" questions answer themselves.

## References

- Assigning Pods to Nodes: <https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/>
- Taints and Tolerations: <https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/>
- Assign Pods using Node Affinity: <https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-nodes-using-node-affinity/>
- Well-Known Labels, Annotations and Taints: <https://kubernetes.io/docs/reference/labels-annotations-taints/>

---
tags: kubernetes, kubectl, secrets
date: "2026-10-17"
category: Kubernetes
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# The kubectl apply Trap: Removed Secret Keys That Refuse to Die

This blog post explains a behavior that caught me off guard: when you remove a key from a Secret manifest and run `kubectl apply`, the key can survive in `etcd` with an empty string instead of being deleted. It covers why this happens, how the `kubectl apply` three-way merge works behind the scenes, and what you should do to actually remove the key.

## The Problem: I Removed a Key, but It Is Still There

Let me describe the exact scenario, because the details matter.

I created a Secret named `foobar` with two keys, `x` and `y`. I applied it:

```{code-block} yaml
:caption: secret.yaml

apiVersion: v1
kind: Secret
metadata:
  name: foobar
type: Opaque
stringData:
  x: "value-x"
  y: "value-y"
```

```bash
kubectl apply -f secret.yaml
```

Later, I edited the local YAML, removed the `y` key entirely, and applied again:

```{code-block} yaml
:caption: secret.yaml (y removed)

apiVersion: v1
kind: Secret
metadata:
  name: foobar
type: Opaque
stringData:
  x: "value-x"
```

```bash
kubectl apply -f secret.yaml
```

I expected `y` to be gone. It was not. When I inspected the Secret, `y` was still there, holding an empty string:

```bash
kubectl get secret foobar -o jsonpath='{.data}'

# » output
#
# {"x":"dmFsdWUteA==","y":""}
```

The key did not go away. It just emptied out. This is the "bad trick" behavior, and it bites you when you assume that removing a line from the manifest is the same as deleting the field from the object.

## Why This Happens: The Three-Way Merge

The root cause is how `kubectl apply` decides what to change. It does not blindly replace the object in the cluster with your file. If it did, two people editing the same resource would constantly overwrite each other. Instead, client-side apply performs a __three-way merge__ using three inputs:

- __1__: The manifest you are applying now (the local file).

- __2__: The live object currently stored in the cluster.

- __3__: The last configuration you applied, saved by kubectl in the `kubectl.kubernetes.io/last-applied-configuration` annotation.

That third input is the one everybody forgets. kubectl compares your new file against the previous `last-applied-configuration` to figure out what you intended to delete. A field is removed only when it was present in the last applied config and is now absent from your new file.

You can see the annotation yourself:

```bash
kubectl get secret foobar -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}'
```

So why did `y` survive as an empty string instead of being deleted? Because something broke that chain of intent. In my case the culprit was the first one, but all of these show up in practice:

- __The object was first created with `kubectl create` or `kubectl replace`__. Those commands do not write the `last-applied-configuration` annotation. When you later run `kubectl apply`, kubectl has no record that `y` ever existed from its point of view, so it cannot conclude that you meant to delete it. The merge falls back to patch semantics, and the field lingers.

- __The key stayed in the manifest with an empty value__. If the new file still has `y: ""`, then from kubectl's perspective you did not remove the key, you set it to empty. That is exactly what ends up in `etcd`.

- __Another tool manages the same Secret__. Helm, Kustomize, or a controller can reconcile the object with merge semantics and keep stale fields around.

The rule behind all of this is that `kubectl apply` deletes a field only when it can prove you removed it, and that proof lives in the `last-applied-configuration` annotation. Break the annotation chain, and removed keys turn into empty leftovers.

:::{note}
Empty string and absent are not the same thing in Kubernetes. A consumer that checks "is the key present?" will still find `y`. An application reading `y` will get an empty value instead of failing fast. Depending on your code, that silent empty value can be worse than a missing key.
:::

## The Solution: Make the Deletion Explicit

Here are the ways to actually get rid of the key, from the one I reach for most to the heavier options.

### Option 1: Keep the apply Chain Healthy

If the Secret was always managed with `kubectl apply`, removing the key from the manifest and applying again just works, because the `last-applied-configuration` annotation carries the intent. The trap appears when the object was bootstrapped with `create` or `replace`. The fix is to stop mixing commands. Pick `kubectl apply` and stay with it for the whole lifecycle of the resource.

If you are already stuck with a broken annotation, keep reading.

### Option 2: kubectl replace (Full Overwrite)

`kubectl replace` does not merge. It overwrites the whole object with your manifest, so any field missing from the file is gone:

```bash
kubectl replace -f secret.yaml
```

This removes `y` for real. The trade-off is that `replace` is destructive by design. It ignores the three-way merge entirely, so you lose the collaborative-edit protection. Use it when you know your manifest is the full source of truth for that object.

### Option 3: Server-Side Apply

Server-Side Apply moves the merge logic from your laptop to the API server and tracks ownership through managed fields instead of an annotation. It handles field removal more predictably:

```bash
kubectl apply --server-side -f secret.yaml
```

When a field you own disappears from your manifest, the API server drops it. This is the direction kubectl is heading, and it avoids the whole `last-applied-configuration` fragility. Be aware that if multiple managers touch the same object, you may need `--force-conflicts` to take ownership.

### Option 4: Delete and Recreate

When the Secret is small and nothing depends on it staying continuously available, just recreate it:

```bash
kubectl delete secret foobar
kubectl apply -f secret.yaml
```

This guarantees a clean state with no stale fields. I avoid it for Secrets that are actively mounted by running Pods, since recreation can cause a brief window where the Secret does not exist.

### Patch a Single Key

If you only need to drop one field without touching the rest, a strategic patch does the job:

```bash
kubectl patch secret foobar --type=json -p='[{"op": "remove", "path": "/data/y"}]'
```

This removes `y` directly from the object. Handy for a quick fix, though for day-to-day management I prefer keeping the manifest as the source of truth.

## Conclusion (Author Opinion)

This one got on my nerves the first time I hit it, because the mental model felt obvious: remove the line, apply, done. The reality is that `kubectl apply` is smarter and more stateful than it looks, and that intelligence depends on an annotation that is easy to break without noticing.

My practical rule is to never mix `kubectl create`, `replace`, and `apply` on the same resource. If I manage something declaratively, I manage it with `apply` from the first command, so the `last-applied-configuration` chain stays intact. For new work, I lean on Server-Side Apply, since it sidesteps the annotation fragility and makes field ownership explicit. And when I find a Secret already stuck with an empty leftover key, a `kubectl replace` or a quick `kubectl patch` clears it out.

Every case is unique, but the lesson is the same. In Kubernetes, an empty string is not a deletion, and `apply` only deletes what it can prove you removed. Keep that in mind and the "bad trick" stops being a surprise.

## References

- <https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/>
- <https://kubernetes.io/docs/reference/using-api/server-side-apply/>
- <https://kubernetes.io/docs/concepts/configuration/secret/>
- <https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#apply>

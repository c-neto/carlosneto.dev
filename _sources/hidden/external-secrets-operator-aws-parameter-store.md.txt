---
tags: kubernetes, external-secrets, aws, vault, secrets
date: "2026-10-17"
category: Kubernetes
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# External Secrets Operator: Let New Parameters Sync Themselves with Wildcards

This blog post shows one specific way to use the External Secrets Operator that I really like: fetching secrets by path with a wildcard, so new parameters show up in your Kubernetes Secret on their own, without ever touching the `ExternalSecret` again. The same trick works with any path-based backend, like AWS Parameter Store or HashiCorp Vault.

## The Common Way, and Its Annoyance

Most `ExternalSecret` examples list each key explicitly. You name every parameter you want, one by one, under `data`. It works, but it means every time you add a new secret to the backend, you also have to edit the `ExternalSecret` manifest, commit it, and redeploy. The source of truth is split in two places: the backend and the manifest.

I wanted the manifest to stop caring about individual keys. Add a parameter in the backend, and it should just appear. That is what `dataFrom.find` gives you.

## The Idea: Fetch by Path, Not by Key

Instead of listing keys, point the `ExternalSecret` at a path and let it pull everything under it. Adopt a naming convention for your parameters so each Secret maps to a path prefix, for example:

```text
/kubernetes/<NAMESPACE>/<SECRET-NAME>/<PARAMETER-NAME>
```

Then the `ExternalSecret` fetches the whole `/kubernetes/demo/app-credentials/` path and rewrites the long parameter names down to just the last segment:

```{code-block} yaml
:caption: external-secret.yaml

apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: app-credentials
  namespace: default
spec:
  refreshInterval: "1m"
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-parameter-store
  target:
    name: app-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  dataFrom:
    - find:
        path: "/kubernetes/demo/app-credentials/"
      rewrite:
        - regexp:
            source: "/kubernetes/demo/app-credentials/(.*)"
            target: "$1"
```

The `find.path` is the wildcard. It matches every parameter under that prefix. The `rewrite` turns `/kubernetes/demo/app-credentials/username` into a clean `username` key in the resulting Secret.

## Why This Is Nice: New Parameters Sync Themselves

The payoff is that the `ExternalSecret` never mentions a single key by name. So when you add a new parameter under the same path:

```bash
aws ssm put-parameter \
    --name "/kubernetes/demo/app-credentials/api-token" \
    --value "abc123" \
    --type "SecureString"
```

On the next `refreshInterval` poll, the operator finds it and adds `api-token` to the Secret automatically. No manifest edit, no commit, no redeploy. The backend is the single source of truth, and the `ExternalSecret` is just a standing instruction: "give me everything under this path."

The same goes the other way. Remove a parameter and, depending on your `deletionPolicy`, the key drops from the Secret. Managing secrets becomes plain CRUD on the backend, and the cluster tracks whatever is there.

If you do not want to wait for the poll, force an immediate sync:

```bash
kubectl annotate externalsecret app-credentials \
    force-sync=$(date +%s) --overwrite -n default
```

## It Works with Vault Too

This is not specific to AWS Parameter Store. Any path-based backend supports the same pattern. With HashiCorp Vault, you point `find.path` at a KV path and get the same behavior:

```{code-block} yaml
:caption: external-secret-vault.yaml

apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: app-credentials
  namespace: default
spec:
  refreshInterval: "1m"
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: app-credentials
    creationPolicy: Owner
  dataFrom:
    - find:
        path: "kubernetes/demo/app-credentials"
```

Add a key under that Vault path and it lands in the Secret on the next sync, exactly like with Parameter Store. The backend changes, the technique does not.

## Conclusion (Author Opinion)

I reach for `dataFrom.find` whenever a Secret groups several related parameters, because it kills the busywork of editing a manifest every time a key changes. The backend becomes the only place you edit secrets, and the `ExternalSecret` becomes a one-time wildcard rule you forget about.

It is not the right fit for every case. If a Secret has exactly one well-known key that never changes, listing it explicitly is clearer. But for anything that grows over time, fetching by path is the approach I recommend. Pick a sane naming convention, write the wildcard once, and let new parameters sync themselves.

## References

- <https://external-secrets.io/latest/guides/getallsecrets/>
- <https://external-secrets.io/latest/provider/aws-parameter-store/>
- <https://external-secrets.io/latest/provider/hashicorp-vault/>

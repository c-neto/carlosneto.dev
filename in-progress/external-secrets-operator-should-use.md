---
tags: kubernetes, eso, secrets, aws
date: "2026-10-17"
category: Kubernetes
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# You Should Use External Secrets Operator

If you still manage Kubernetes Secrets by hand, this blog post is for you. I spent a good part of the last years dealing with manual secret management on growing clusters, and it became one of those recurring pains that shows up in every DevOps retro under the "to improve" column. This post explains what External Secrets Operator is, the problem it solves, and why I recommend adopting it, with an honest look at the drawbacks too.

## The Problem: Manual Secrets Do Not Scale

Our infrastructure grew a lot over three years. New application modules, new tool stacks, and the way we handled Kubernetes Secrets stayed the same: entirely manual.

Manual secret management is a trap. Someone edits a Secret Object, forgets to update the shared note that documents it, and now the source of truth is wrong. Two people touch the same secret file and you get a race condition. Every one of these steps is unsafe, and worse, it blocks automation and makes multi-cluster scenarios painful. When you have more than one cluster running the same applications, keeping their secrets in sync by hand is a recipe for drift and mistakes.

The core issue is simple: the whole process depends on humans not making errors, and humans make errors.

## What is External Secrets Operator?

[External Secrets Operator](https://external-secrets.io/latest/), or ESO, is a Kubernetes operator that injects values into Secret Objects from an external Secret Management System. Instead of creating and editing Secrets by hand, you keep the real values in a system like AWS Parameter Store, AWS Secrets Manager, HashiCorp Vault, or Google Secret Manager, and ESO syncs them into the cluster automatically.

It is an open-source project under the Apache-2.0 license, started by GoDaddy and sponsored by payment companies like Pento and Form3. It gets recurring updates and bug fixes, and it has a solid [list of adopters](https://github.com/external-secrets/external-secrets/blob/main/ADOPTERS.md), including Mercedes-Benz and VMware. For something that sits this central in your stack, that track record gave me confidence to adopt it.

ESO works through two main CRDs:

- `ClusterSecretStore`: provides access to the external Secret Management System.
- `ExternalSecret`: reads from a `ClusterSecretStore`, fetches parameters by a pattern, and creates the Secret Object in the cluster.

In my case I chose [AWS Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html) as the backend. I will come back to why in the alternatives section.

## How it Works

Once the ESO stack is deployed, your whole workflow reduces to two things: writing `ExternalSecret` manifests and managing parameters in AWS Parameter Store.

In the `ExternalSecret` manifest you specify the Secret Object name to generate, the parameters to fetch (wildcards are supported), and the origin of the secrets, which here is the Parameter Store.

To make this dynamic, we defined a naming pattern for the parameters in AWS Parameter Store:

```{code-block} text
:caption: Wildcard Parameter Name Pattern

/kubernetes/<NAMESPACE>/<SECRET-NAME>/<PARAMETER-NAME>
```

- `NAMESPACE`: the namespace of the `ExternalSecret`.
- `SECRET-NAME`: the `ExternalSecret` name (by convention, the same name as the Secret Object).
- `PARAMETER-NAME`: each parameter from the `stringData` of the Secret Object.

Combine this pattern with wildcard retrieval in the `ExternalSecret`, and you get a fully dynamic process. Any CRUD operation on a parameter in AWS Parameter Store is reflected in the cluster automatically, with no manual editing of Secrets.

On the architecture side, we install ESO via Helm Chart managed by ArgoCD. The base stack and the `ClusterSecretStore` live in a dedicated `eso` namespace, and the `ClusterSecretStore` is visible to `ExternalSecrets` in every namespace. Access to AWS Parameter Store is granted through IRSA, created by Terraform with read-only permissions for the ESO pods. The Secret Objects become visible in ArgoCD through the ownership of their `ExternalSecrets`, with the values hidden.

## Why You Should Use It

Here is what adopting ESO actually gave us, grouped the way I think about it.

On the operations side:

- __Fewer human errors__: Secret Objects sync automatically from changes in AWS Parameter Store, which removes the manual steps that used to cause mistakes.
- __Visibility__: Secret Objects show up in ArgoCD through their `ExternalSecrets` ownership, and errors get reported instead of hiding.
- __Abstraction layer__: ESO abstracts access to different Secret Management Systems, so migrating to another backend later is realistic instead of a rewrite.

On the security and compliance side:

- __Integrity__: each parameter lives as its own entry in AWS Parameter Store, edited through the AWS Console, which avoids the race conditions of shared files and makes restoring values simple.
- __Authenticity__: access is restricted with IAM policies, so you can actually follow the least privilege principle.
- __Availability__: AWS Parameter Store is serverless, so AWS carries the availability burden, not your DevOps team.
- __Confidentiality__: values are encrypted with AWS KMS in `SecureString` format and are not exposed in CloudTrail logs.
- __Auditing__: every change is versioned with author and date, recorded in CloudTrail.

And the use cases that pushed us over the line:

- __Multi-cluster__: a single source of truth for secrets across clusters, which is exactly what you want during migrations and upgrades.
- __GitOps__: `ExternalSecret` manifests get committed to the ops repository, so the creation of Secret Objects is explicit and visible in ArgoCD.
- __Automation__: committing the `ExternalSecrets` to the repository makes stack provisioning much easier to automate.

## Drawbacks (Being Honest)

No tool is a silver bullet, and ESO is not an exception.

It introduces a new stack that needs attention and maintenance. ESO ships CRDs, and you have to test version compatibility carefully to avoid downtime during upgrades. It is also an open-source project, which means its maintainability is not guaranteed and nobody is handing you an operational SLA. You are taking on that responsibility.

AWS Parameter Store, the backend I picked, has its own quirks worth knowing before you commit:

- It does not allow parameters with empty string values.
- There is no automatic backup for the parameters.
- An AWS region incident can cause downtime.
- In a disaster recovery setup, the DR cluster mixes production parameters with its own, so the sync needs care.

None of these outweighed the benefits for us, but you should go in with your eyes open.

## Why AWS Parameter Store and Not Vault or Secrets Manager

ESO supports many backends, so the real decision was which Secret Management System to use. My mainline was the balance between simplicity and available features.

I tested [HashiCorp Vault](https://www.vaultproject.io/) with ESO and it worked, but the stack was heavy: Vault, Okta, Terraform, cross-account RBAC in Kubernetes, and the ESO integration on top. It validated fine, but then HashiCorp changed its product licenses and that pushed Vault to the backlog.

I also looked at AWS Secrets Manager, and for our needs there was nothing relevant enough to justify the extra pricing.

AWS Parameter Store won because it had everything we actually needed: versioning, audit logs, IAM-based access control already in place, and availability handled by AWS. It is also cheaper than Vault and Secrets Manager for our use case.

## Conclusion (Author Opinion)

I have been running External Secrets Operator with AWS Parameter Store in production, and it removed a whole class of manual, error-prone work from the team. The secrets have a single source of truth, changes sync automatically, and everything is auditable. The pain that used to show up in every retro is gone.

Is it free of cost? No. You maintain a new operator, you test CRD compatibility on upgrades, and you accept the limits of whatever backend you choose. But compared to editing Kubernetes Secrets by hand across multiple clusters, that trade is easy to make.

If you are still managing Secrets manually, you should use External Secrets Operator. Give it a try, and start with a backend you already operate well.

## References

- https://external-secrets.io/latest/
- https://github.com/external-secrets/external-secrets/blob/main/ADOPTERS.md
- https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html

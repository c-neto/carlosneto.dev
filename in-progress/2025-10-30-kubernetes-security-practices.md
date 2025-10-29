---
tags: fluentbit, logs, observability
date: "2025-06-22"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/06/22*

---

# Kubernetes Security Practices

## Supply-chain Protection in Kubernetes

Protecting the Kubernetes supply chain is essential. Use immutable identifiers (SHAs) for all external dependencies, including container images and cloud resources like AMIs, so builds are reproducible and tampering is harder.

Automate dependency management with tools such as Dependabot or Renovate to track, audit, and open PRs for outdated or vulnerable dependencies. In CI/CD, apply least-privilege to tokens (for example, GITHUB_TOKEN) so systems only have the permissions they need.

Sign artifacts and images to create a verifiable chain of trust. Tools like Cosign and policy-controller can help ensure only trusted artifacts are deployed.

- Use SHAs or other immutable identifiers for everything you download (images, AMIs, libs).
- Automate audits and PRs for outdated or vulnerable dependencies.
- Apply least privilege to CI/CD tokens (e.g., GITHUB_TOKEN).
- Sign images and artifacts.
- Tooling: Dependabot, Renovate, Cosign, policy-controller

## RBAC

Favor reusable Roles and ClusterRoles for common capabilities to reduce duplication and simplify audits. Balance reuse with least privilege: prefer composing narrow roles when an operation needs fewer permissions.

Scope access to namespaces when possible. For multi-team clusters, isolate workloads per namespace and grant developers only the namespace-scoped permissions they need. If a workload does not need the Kubernetes API, run it under the default service account without adding extra bindings. Never bind elevated Roles or ClusterRoles to the default service account—create specific service accounts with minimal permissions instead.

When workloads need cloud APIs, use provider-native identity (for example, IAM Roles for Service Accounts on EKS, Pod Identity, or Workload Identity on GKE) instead of long-lived credentials.

- Share Roles/ClusterRoles where appropriate
- Balance reusability vs least privilege
- If a workload doesn't need the Kubernetes API, use the default service account (no extra bindings)
- Never bind elevated roles to the default service account
- For shared clusters, use namespaces and limit developer access by namespace
- Use cloud-native identity mechanisms for cloud API access (IRSA, Pod Identity, Workload Identity)

## Secrets Management

Kubernetes Secrets are base64-encoded, not encrypted. Treat them as sensitive: restrict access with RBAC and grant minimal permissions. Use a secrets controller to fetch and sync values from an external vault so short-lived, centrally managed credentials are delivered to the cluster.

Never commit secrets to version control. Mounting a Secret as an env var or file is not fully secure—compromised pods or nodes can expose them. The safer pattern is having the application fetch secrets at runtime and keep them in memory, using short-lived credentials when possible. For Git-backed workflows, prefer encrypted approaches like Sealed Secrets or external secrets controllers matched to your threat model.

- Secrets are base64-encoded, not encrypted
- Limit access to secrets via RBAC
- Use a secrets controller to sync secrets from an external vault
- Never commit secrets to VCS (GitHub, GitLab, etc.)
- Mounting env vars or files is not 100% secure
- Prefer app-runtime secret retrieval and short-lived credentials
- Tooling: External Secrets, Sealed Secrets, cloud provider secret integrations

## Hardening

Bake security into your delivery pipeline and deployment tooling. Use your deployment wrappers (Helm, operators, kustomize) to codify organization-wide best practices and sane defaults so every release inherits the same protections.

Make image and build pipelines a security gate: scan for misconfigurations, embedded secrets, SAST findings, and known vulnerabilities, and fail the pipeline when scans do not meet policy. Enforce the same checks at runtime with an admission controller evaluated by the API server to reject non-compliant workloads.

For OS/host hardening, prefer pre-built, hardened images that are versioned and tested rather than installing packages at startup. Complement with automated checks like kube-bench and image scanners such as trivy and docker scout to keep images and hosts continuously validated.

- Use deployment wrappers (Helm, kustomize, operators) to enforce best practices
- Scan builds for misconfigurations, secrets, SAST, and vulnerabilities
- Fail pipelines that don't meet policy
- Enforce checks via admission controllers evaluated by the API server
- Prefer pre-built hardened images over runtime configuration
- Tooling: kube-bench, trivy, docker scout

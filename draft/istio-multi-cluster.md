---
tags: istio, kubernetes, servicemesh, mtls
date: "2026-10-17"
category: Kubernetes
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# How to Set Up Istio Multi-Cluster: Mesh, Control Planes, and Certificates

Setting up Istio inside a single cluster is one thing. Extending the mesh across several Kubernetes clusters is where most of the questions show up: which deployment model to pick, how the clusters actually find each other, and how to make the certificates work across cluster boundaries. The certificate part in particular trips people up, especially the question of whether you need a common root CA.

This blog post is a guide on how to set up Istio multi-cluster. It walks through the deployment model to choose, the control plane and data plane pieces you need in place, and how to wire up the certificate chain so the clusters trust each other. To keep it concrete, I will use a real implementation as the running example: a multi-primary mesh across several clusters, with AWS Private CA as the shared root of trust.

## Step 1: Understand What Multi-Cluster Gives You

Before configuring anything, it is worth being clear on what you are buying. A service mesh usually lives inside a single Kubernetes cluster. Multi-cluster extends one mesh across several clusters, so services in different clusters discover and talk to each other as if they were in the same place, with the same security and routing rules applied end to end.

The reasons to set this up:

- __Improved availability__: if one control plane fails, only the workloads it manages are affected. The blast radius is limited instead of taking the whole mesh down.
- __Configuration isolation__: you can apply configurations to specific clusters, zones, or regions without touching the others.
- __Canary and blue-green deployments__: you can roll out updates gradually to a part of the mesh, which gives you much better control over the rollout.

If none of these matter to your case, a single cluster mesh is simpler and you should stay there. Multi-cluster is worth the extra setup when you need a mesh that survives a cluster failure, scoped configuration changes, and rollouts you can target at a slice of your infrastructure.

## Step 2: Choose the Deployment Model

Istio can be set up in several ways. The model used in this example, and a common choice, is the **multi-primary** model.

In this configuration, each cluster has its own Istio control plane, and every control plane watches the API Servers of all clusters for endpoints. The result is that every cluster is aware of every other cluster, and service workloads communicate directly, pod to pod, across cluster boundaries. There is no single central brain that, if it dies, takes everything with it.

One decision to make early: **sidecar mode or ambient mode.** This guide uses sidecar mode, where an Envoy proxy is injected into each pod. Istio also has ambient mode, and the two can run in parallel per namespace, but ambient mode does not support multi-cluster. If multi-cluster is your goal, sidecar mode is the path.

## Step 3: Get the Control Plane and Data Plane in Place

Multi-cluster builds on top of Istio's two halves, so you need both working in every cluster before you connect them.

### Control Plane: istiod

The control plane is `istiod`, a single daemon that unified functions that used to be split across separate components:

- __Pilot__: configures the Envoy proxies at runtime and propagates new configuration to them.
- __Citadel__: the internal Certificate Authority. It signs certificate signing requests (CSRs) and issues the TLS certificates that secure traffic between services.
- __Galley__: validates configuration and hands it to Pilot for distribution.

The control plane decides how services should communicate, centralizes policy and routing, and coordinates service discovery, identity, and security. It generates the configuration; it does not move the traffic.

### Data Plane: Envoy

The data plane is where the traffic actually flows. It is made of Envoy proxies injected as sidecars into the pods. Envoy intercepts the calls between services, applies the rules the control plane defined, and collects telemetry along the way.

In the multi-primary model, each cluster runs this full stack, and the control planes connect to each other. That connection is secured with mutual TLS, which is where the certificates come in.

## Step 4: Set Up the Certificates (and Yes, You Need a Common Root CA)

This is the part that generates the most doubt, so let me answer it directly: **in a multi-cluster mesh the control planes must share a common root of trust.** The certificates used by the different control planes have to be issued by a common Certificate Authority. In this example that shared CA is AWS Private CA (AWSPCA).

The reason is straightforward. In a multi-cluster scenario, control planes exchange information like service configuration and policies, and they do it over mutual TLS (mTLS). For one control plane to trust a certificate presented by another, both certificates have to chain up to the same root. Without a shared root CA, the clusters would not trust each other, and the mesh would not span them.

### The Two Certificates to Keep Straight

Istio has two certificates that are easy to confuse:

- __istiod certificate__: used by the `istiod` service itself. It lets the Envoy sidecars authenticate `istiod`, so a sidecar knows it is talking to the legitimate control plane and not an imposter.
- __istio-ca certificate__: the root certificate of the Istio Certificate Authority. It verifies the chain of trust for every certificate issued by `istio-ca`, including the istiod certificate. Sidecars use it to validate the istiod certificate before establishing a secure connection.

### The Components That Wire the Chain Together

To connect Istio to a real CA without a lot of manual pain, this setup uses a few helper components:

- __cert-manager__: handles obtaining, renewing, and using certificates, and integrates with private key infrastructures like AWS Private CA.
- __istio-csr__: the agent that connects cert-manager to Istio, so the control plane and workloads can be secured with cert-manager with minimal work.
- __AWS Private CA (AWSPCA)__: the shared root that sits at the top of the chain.

The control plane certificate flow works like this. When Istio is deployed on a cluster, the `istio-ca` certificate is created, and it is validated against AWSPCA in the shared-services account. When `istiod` starts, it generates a CSR to `istio-csr` asking for its own istiod certificate, and `istio-csr` uses cert-manager together with the `istio-ca` certificate to issue it.

### Workload mTLS and Certificate Rotation

For the workloads themselves, Istio provisions a strong identity to every pod with an X.509 certificate. The flow is automated:

1. When a pod starts, the Istio agent in the pod creates the private key and a CSR and sends it, with its credentials, to `istiod`.
2. `istiod` offers a gRPC service that takes CSRs. It validates the credentials in the CSR and, on success, signs it. Here `istio-csr` uses cert-manager and an intermediate cluster issuer to generate the proxy certificate. That intermediate issuer is backed by the `istio-ca` certificate acting as an intermediate CA, which avoids hammering AWSPCA with every request.
3. Envoy requests the certificate and key from the Istio agent in the same pod through the Secret Discovery Service (SDS) API, mounts them, and uses them to talk to the other proxies in the mesh.

The Istio agent watches the certificate expiration and repeats this process to rotate keys and certificates. By default, a pod's identity certificate expires in 24 hours, and Istio rotates it every 12 hours. The logic is damage control: if a certificate or a private key is ever compromised, it only stays valid for a short window before it expires, which limits what an attacker can do with it.

## Conclusion (Author Opinion)

Configuring Istio multi-cluster looks intimidating from the outside, but once you break it into steps it gets much more manageable. Decide you actually need a mesh spanning clusters, pick the multi-primary model so there is no single point of failure, get a full control plane and data plane running in each cluster, and then tie everything together with a shared certificate chain.

If I had to leave one thing with you, it is the certificate answer: you do need a common root CA, because the whole multi-cluster trust model depends on every cluster chaining up to the same authority. In the example here, AWS Private CA plays that role, with cert-manager and istio-csr doing the heavy lifting and an intermediate CA keeping the calls to AWSPCA under control. It is a lot of moving parts, but each one earns its place.

## References

- https://istio.io/latest/docs/ops/deployment/deployment-models/
- https://istio.io/latest/docs/setup/install/multicluster/
- https://istio.io/latest/docs/concepts/security/
- https://cert-manager.io/docs/
- https://docs.aws.amazon.com/privateca/latest/userguide/PcaWelcome.html

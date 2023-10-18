---
tags: tips, best-practices
date: "2023-02-02"
category: kubernetes
---

*__Blog Post Publish Date:__ 2023/02/02*

---

# Kubernetes Security Tips and Best Practices

This post is a set of tips in the Kubernetes manifests configuration.

## Use of RBAC

Role-Based Access Control (RBAC) is a way to manage access control in a Kubernetes cluster. Make sure to use RBAC to manage access control and to ensure that users and services have the least privilege necessary.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-role
  namespace: my-namespace
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "watch", "list"]

---

apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-role-binding
  namespace: my-namespace
subjects:
  - kind: ServiceAccount
    name: my-service-account
    namespace: my-namespace
roleRef:
  kind: Role
  name: my-role
  apiGroup: rbac.authorization.k8s.io

---

apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-service-account
  namespace: my-namespace
```

## Use of Network Policies

Network Policies are a way to manage network traffic in a Kubernetes cluster. Make sure to use Network Policies to restrict network traffic and to secure communication between resources in a cluster.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-network-policy
  namespace: my-namespace
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              team: dev-team
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              team: prod-team
```

## Use of Pod Security Policies

Pod Security Policies are a way to manage security of Pods in a Kubernetes cluster. Make sure to use Pod Security Policies to enforce security controls and to protect the security of Pods and the resources they access.
Example:

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: my-pod-security-policy
spec:
  privileged: false
  seLinux:
    rule: RunAsAny
  supplementalGroups:
    rule: RunAsAny
  runAsUser:
    rule: RunAsAny
  fsGroup:
    rule: RunAsAny
  volumes:
    - configMap
    - emptyDir
    - projected
    - secret
    - downwardAPI
    - persistentVolumeClaim
  hostNetwork: false
  hostIPC: false
  hostPID: false
  allowPrivilegeEscalation: false
```

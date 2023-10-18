---
tags: tips, best-practices
date: "2023-02-01"
category: kubernetes
---

*__Blog Post Publish Date:__ 2023/02/01*

---

# Kubernetes Deployment: Basic Tips and Best Practices

This post is a set of tips and best practices in `Deployment` and `Pod` Kind configuration.

## Using Liveness and Readiness Probes

Liveness and Readiness Probes are checks performed by the `kubelet` to determine if a container is running correctly. Make sure to use these probes to ensure that your containers are healthy and ready to serve traffic.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app
spec:
  containers:
    - name: my-container
      image: my-image:latest
      ports:
        - containerPort: 80
      livenessProbe:
        httpGet:
          path: /healthz
          port: 80
      readinessProbe:
        httpGet:
          path: /readyz
          port: 80
```

## Use of Health Checks

Health Checks are a way to monitor the health of a Pod. Make sure to use Health Checks to monitor the health of a Pod and to detect and respond to failures.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  namespace: my-namespace
  labels:
    app: my-app
spec:
  containers:
    - name: my-container
      image: my-image:latest
      ports:
        - containerPort: 80
```

## Using Resource Requests and Limits

Resource Requests and Limits are values that you set to indicate how much CPU and memory a container needs to run. Make sure to set these values to ensure that your containers have the resources they need to run correctly.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app
spec:
  containers:
    - name: my-container
      image: my-image:latest
      ports:
```

## Using Rolling Updates

Rolling Updates allow you to update your resources with zero downtime. Make sure to use Rolling Updates to deploy changes to your resources in a controlled manner.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
  labels:
    app: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-container
          image: my-image:latest
          ports:
            - containerPort: 80
```

## Using Init Containers

Init Containers are containers that run before the main containers in a Pod. Make sure to use Init Containers to perform setup tasks that need to be completed before the main containers start.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app
spec:
  initContainers:
    - name: my-init-container
      image: my-init-image:latest
      command: ["/bin/sh", "-c", "echo 'Init Container Running...'"]
  containers:
    - name: my-container
      image: my-image:latest
      ports:
        - containerPort: 80
```

---

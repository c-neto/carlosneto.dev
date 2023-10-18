---
tags: tips, best-practices
date: "2023-02-03"
category: kubernetes
---

*__Blog Post Publish Date:__ 2023/02/03*

---

# Kubernetes Manifests Example Configuration

This post is a set of tips in the Kubernetes manifests configuration.

### Using Config Maps

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-configmap
data:
  # The API URL for the app to use
  API_URL: "https://api.example.com"
  # The number of seconds to wait before retrying a request
  RETRY_DELAY: "5"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
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
          envFrom:
            - configMapRef:
                name: my-configmap
```

### Using Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
type: Opaque
data:
  # Base64 encoded database password
  db-password: cGFzc3dvcmQ=
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
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
          env:
            # Use an environment variable to specify the API URL
            - name: API_URL
              value: "https://api.example.com"
            # Use a secret to retrieve the database password
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: my-secret
                  key: db-password
```

### Using Namespaces

Namespaces are a way to divide a cluster into multiple virtual clusters. It's best to use namespaces to organize your resources and ensure that resources are isolated from each other.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-namespace
---
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

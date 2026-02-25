---
tags: python
date: "2026-02-25"
category: helm
---

*__Blog Post Publish Date:__ 2026/02/25*

---

# Helm Tips: Inspect Your Chart Context with JSON

Debugging Helm charts can be frustrating when starting out, especially if you come from programming languages with debuggers and IDE auto-completion that provide a smoother development experience. It is common to face issues when you create a template that tries to access a parameter defined in the `.Values` files, and for any reason, whether a syntax error or typo, the `$ helm template` command fails, and the stack trace shows confusing messages that don't point to the root cause. This blog post provides an alternative approach to inspect the Helm Chart context with JSON, helping you understand how to access chart properties for use in your templates.

## Are There IDEs for Helm Charts?

Unfortunately, there is no definitive IDE specifically for Helm. There are plugins for VSCode and JetBrains IDEA that provide some tooling for auto-completion, but they don't come close to the code experience available with popular programming languages like Python and Java. I use VSCode's [Kubernetes (by Microsoft)](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools) + [YAML (by Red Hat)](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml), which helps avoid typos in `.Values` usage and checks available Go template functions. However, there are limitations, some variables are omitted in auto-complete, which diminishes the experience. I tried the [JetBrains Helm Plugin](https://www.jetbrains.com/help/idea/helm.html), but it doesn't work as simply as the _.gif_ present in the Plugin shows. Additionally, the Kubernetes plugin is not available in IntelliJ IDEA without an Ultimate subscription.

## Debug the Right Way!

As an alternative to lacks a robust auto-completion, you can dump the entire Helm Chart context in JSON format to understand the Values references, Chart and Subchart metadata, and available static files.

Let's get started. First, create a Helm Chart called `foobar`.

```bash
helm create foobar
```

Now, create a template named `debug.yaml`:

```bash
vim templates/debug.yaml
```

The `debug.yaml` file should contain:

```yaml
{{ . | toPrettyJson }}
```

Now, render only the `debug.yaml` template:

```bash
helm template -s templates/debug.yaml . | tail -n +3 | jq
```

The output shows the Helm Chart context with all variables available in your templates.

```json
{
  "Capabilities": {
    "KubeVersion": {
      "Version": "v1.34.0",
      "Major": "1",
      "Minor": "34"
    },
    "APIVersions": [
      "v1",
      "admissionregistration.k8s.io/v1",
      "admissionregistration.k8s.io/v1alpha1",
      "admissionregistration.k8s.io/v1beta1",
      "internal.apiserver.k8s.io/v1alpha1",
      "apps/v1",
      "apps/v1beta1",
      "apps/v1beta2",
      "authentication.k8s.io/v1",
      "authentication.k8s.io/v1alpha1",
      "authentication.k8s.io/v1beta1",
      "authorization.k8s.io/v1",
      "authorization.k8s.io/v1beta1",
      "autoscaling/v1",
      "autoscaling/v2",
      "autoscaling/v2beta1",
      "autoscaling/v2beta2",
      "batch/v1",
      "batch/v1beta1",
      "certificates.k8s.io/v1",
      "certificates.k8s.io/v1beta1",
      "certificates.k8s.io/v1alpha1",
      "coordination.k8s.io/v1alpha2",
      "coordination.k8s.io/v1beta1",
      "coordination.k8s.io/v1",
      "discovery.k8s.io/v1",
      "discovery.k8s.io/v1beta1",
      "events.k8s.io/v1",
      "events.k8s.io/v1beta1",
      "extensions/v1beta1",
      "flowcontrol.apiserver.k8s.io/v1",
      "flowcontrol.apiserver.k8s.io/v1beta1",
      "flowcontrol.apiserver.k8s.io/v1beta2",
      "flowcontrol.apiserver.k8s.io/v1beta3",
      "networking.k8s.io/v1",
      "networking.k8s.io/v1beta1",
      "node.k8s.io/v1",
      "node.k8s.io/v1alpha1",
      "node.k8s.io/v1beta1",
      "policy/v1",
      "policy/v1beta1",
      "rbac.authorization.k8s.io/v1",
      "rbac.authorization.k8s.io/v1beta1",
      "rbac.authorization.k8s.io/v1alpha1",
      "resource.k8s.io/v1",
      "resource.k8s.io/v1beta2",
      "resource.k8s.io/v1beta1",
      "resource.k8s.io/v1alpha3",
      "scheduling.k8s.io/v1alpha1",
      "scheduling.k8s.io/v1beta1",
      "scheduling.k8s.io/v1",
      "storage.k8s.io/v1beta1",
      "storage.k8s.io/v1",
      "storage.k8s.io/v1alpha1",
      "storagemigration.k8s.io/v1alpha1",
      "apiextensions.k8s.io/v1beta1",
      "apiextensions.k8s.io/v1"
    ],
    "HelmVersion": {
      "version": "v4.0.5",
      "git_commit": "1b6053d48b51673c5581973f5ae7e104f627fcf5",
      "git_tree_state": "clean",
      "go_version": "go1.25.5",
      "kube_client_version": "v1.34"
    }
  },
  "Chart": {
    "APIVersion": "v2",
    "Annotations": null,
    "AppVersion": "1.16.0",
    "Condition": "",
    "Dependencies": [],
    "Deprecated": false,
    "Description": "A Helm chart for Kubernetes",
    "Home": "",
    "Icon": "",
    "IsRoot": true,
    "Keywords": [],
    "KubeVersion": "",
    "Maintainers": [],
    "Name": "foobar",
    "Sources": [],
    "Tags": "",
    "Type": "application",
    "Version": "0.1.0"
  },
  "Files": {
    ".helmignore": "IyBQYXR0ZXJucyB0by...",
    "output.yaml": "LS0tCiMgU291cmNlOi..."
  },
  "Release": {
    "IsInstall": true,
    "IsUpgrade": false,
    "Name": "release-name",
    "Namespace": "default",
    "Revision": 1,
    "Service": "Helm"
  },
  "Subcharts": {},
  "Template": {
    "BasePath": "foobar/templates",
    "Name": "foobar/templates/debug.yaml"
  },
  "Values": {
    "affinity": {},
    "autoscaling": {
      "enabled": false,
      "maxReplicas": 100,
      "minReplicas": 1,
      "targetCPUUtilizationPercentage": 80
    },
    "fullnameOverride": "",
    "httpRoute": {
      "annotations": {},
      "enabled": false,
      "hostnames": [
        "chart-example.local"
      ],
      "parentRefs": [
        {
          "name": "gateway",
          "sectionName": "http"
        }
      ],
      "rules": [
        {
          "matches": [
            {
              "path": {
                "type": "PathPrefix",
                "value": "/headers"
              }
            }
          ]
        }
      ]
    },
    "image": {
      "pullPolicy": "IfNotPresent",
      "repository": "nginx",
      "tag": ""
    },
    "imagePullSecrets": [],
    "ingress": {
      "annotations": {},
      "className": "",
      "enabled": false,
      "hosts": [
        {
          "host": "chart-example.local",
          "paths": [
            {
              "path": "/",
              "pathType": "ImplementationSpecific"
            }
          ]
        }
      ],
      "tls": []
    },
    "livenessProbe": {
      "httpGet": {
        "path": "/",
        "port": "http"
      }
    },
    "nameOverride": "",
    "nodeSelector": {},
    "podAnnotations": {},
    "podLabels": {},
    "podSecurityContext": {},
    "readinessProbe": {
      "httpGet": {
        "path": "/",
        "port": "http"
      }
    },
    "replicaCount": 1,
    "resources": {},
    "securityContext": {},
    "service": {
      "port": 80,
      "type": "ClusterIP"
    },
    "serviceAccount": {
      "annotations": {},
      "automount": true,
      "create": true,
      "name": ""
    },
    "tolerations": [],
    "volumeMounts": [],
    "volumes": []
  }
}
```

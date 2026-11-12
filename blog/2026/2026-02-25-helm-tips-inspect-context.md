---
tags: helm
date: "2026-02-25"
category: Kubernetes
author: Carlos Neto
title: "Helm Tips: Inspect Your Chart Context with JSON"
description: "Helm has no real debugger, so dump the whole chart context (Values, Chart, Release, Capabilities, Files) as JSON with toPrettyJson and helm template to see exactly what your templates can access."
myst:
  html_meta:
    description: "Helm has no real debugger, so dump the whole chart context (Values, Chart, Release, Capabilities, Files) as JSON with toPrettyJson and helm template to see exactly what your templates can access."
og:title: "Helm Tips: Inspect Your Chart Context with JSON"
og:description: "Helm has no real debugger, so dump the whole chart context (Values, Chart, Release, Capabilities, Files) as JSON with toPrettyJson and helm template to see exactly what your templates can access."
---

*__Blog Post Publish Date:__ 2026/02/25*

---

# Helm Tips: Inspect Your Chart Context with JSON

This blog post shows a simple way to debug Helm charts: dump the entire chart context as JSON and look at exactly what your templates can access. It helps most when `$ helm template` fails with a message that doesn't point to the real problem, such as a typo in a `.Values` path.

Debugging Helm charts is frustrating at first, especially if you come from programming languages with debuggers and IDE auto-completion. A template that reads a wrong `.Values` key, because of a typo or a wrong nesting level, often fails with an error far from the root cause.

## Are There IDEs for Helm Charts?

Unfortunately, there is no IDE built for Helm. VS Code and JetBrains IDEA have plugins with some auto-completion, but nothing close to what you get with languages such as Python and Java.

I use VS Code with [Kubernetes (by Microsoft)](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools) and [YAML (by Red Hat)](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml). They help avoid typos in `.Values` and show the available Go template functions, but some variables are missing from auto-completion. I also tried the [JetBrains Helm plugin](https://www.jetbrains.com/help/idea/helm.html), but it didn't work as smoothly as the animation on its page suggests, and the Kubernetes plugin requires an IntelliJ IDEA Ultimate subscription.

## Dump the Chart Context as JSON

Since the tooling falls short, I use another approach: render the whole Helm chart context as JSON. The **chart context** is the root object (`.`) that every template receives. It holds `.Values`, the chart and subchart metadata, release information, cluster capabilities, and the chart's files.

First, create a chart called `foobar` and enter its directory:

```bash
helm create foobar
cd foobar
```

Then create a template named `debug.yaml`:

```bash
vim templates/debug.yaml
```

With this content. [`toPrettyJson`](https://helm.sh/docs/chart_template_guide/function_list/#toprettyjson) is a template function that converts any object to indented JSON:

```yaml
{{ . | toPrettyJson }}
```

Now render only that template. [`helm template`](https://helm.sh/docs/helm/helm_template/) with `-s` (`--show-only`) renders a single file, `tail -n +3` drops the `---` separator and the `# Source:` comment that Helm adds, and `jq` formats the result:

```bash
helm template -s templates/debug.yaml . | tail -n +3 | jq
```

The output is the full context, with every variable your templates can use. The [built-in objects](https://helm.sh/docs/chart_template_guide/builtin_objects/) page documents each one:

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

A few things stand out in this output. For example, `Capabilities.APIVersions` lists the APIs you can check with `.Capabilities.APIVersions.Has`, `Chart` shows the metadata from `Chart.yaml` with Go-style capitalized names, and `Files` holds the content of every non-template file in the chart, base64-encoded in this dump.

## Inspect Only What You Need

The full context is long. To focus on one part, pipe only that object to `toPrettyJson`. For example, to see the merged values after applying a values file:

```yaml
{{ .Values | toPrettyJson }}
```

```bash
helm template -s templates/debug.yaml . -f values-prod.yaml | tail -n +3 | jq
```

This is the fastest way I know to check what a chart actually receives after values files, `--set` flags, and subchart values are merged.

## Remove the Debug Template When You Are Done

`debug.yaml` is a regular template, so `helm install` and `helm upgrade` would render it too, and its JSON is not a valid Kubernetes manifest. Delete it after debugging, or keep it out of the release with a condition such as `{{- if .Values.debug }}`.

If you're designing a chart from scratch, [Helm Charts: Development Practices from a Programmer's Perspective](/blog/2025/2025-02-25-helm-best-practices.md) covers how I decide what to template and what not to. I also template Logstash pipelines with Helm, as I show in [Logstash DB Enrichment](/blog/2025/2025-02-16-logstash-db-enrichment.md).

## Key Takeaways

- Helm has no real debugger, and IDE plugins only partly auto-complete chart variables.
- `{{ . | toPrettyJson }}` in a template renders the whole chart context as JSON.
- `helm template -s templates/debug.yaml . | tail -n +3 | jq` renders only that template and formats the output.
- The context has `Values`, `Chart`, `Release`, `Capabilities`, `Files`, `Subcharts`, and `Template`.
- Dump `.Values` alone to check the final merged values after values files and `--set`.
- Delete the debug template, or guard it with a condition, before installing the chart.

## References

- [Built-in objects (Helm)](https://helm.sh/docs/chart_template_guide/builtin_objects/)
- [Template function list: toPrettyJson (Helm)](https://helm.sh/docs/chart_template_guide/function_list/#toprettyjson)
- [helm template (Helm)](https://helm.sh/docs/helm/helm_template/)
- [Kubernetes extension for VS Code (Microsoft)](https://marketplace.visualstudio.com/items?itemName=ms-kubernetes-tools.vscode-kubernetes-tools)
- [YAML extension for VS Code (Red Hat)](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
- [Helm plugin (JetBrains)](https://www.jetbrains.com/help/idea/helm.html)

*I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Helm Tips: Inspect Your Chart Context with JSON",
      "description": "Helm has no real debugger, so dump the whole chart context (Values, Chart, Release, Capabilities, Files) as JSON with toPrettyJson and helm template to see exactly what your templates can access.",
      "datePublished": "2026-02-25",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-02-25-helm-tips-inspect-context/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-02-25-helm-tips-inspect-context/",
      "keywords": ["Helm", "Helm template", "toPrettyJson", "debugging", "Kubernetes"],
      "author": {"@id": "https://carlosneto.dev/#person"}
    },
    {
      "@type": "Person",
      "@id": "https://carlosneto.dev/#person",
      "name": "Carlos Neto",
      "url": "https://carlosneto.dev/",
      "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
        {"@type": "ListItem", "position": 3, "name": "Helm Tips: Inspect Your Chart Context with JSON"}
      ]
    }
  ]
}
</script>
```

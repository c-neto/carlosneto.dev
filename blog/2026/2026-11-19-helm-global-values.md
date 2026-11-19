---
tags: helm, kubernetes
date: "2026-11-19"
category: Kubernetes
author: Carlos Neto
title: "Helm Global Values: The Right Way to Share Values in an Umbrella Chart"
description: "How the global key in Helm values works, why it only matters with subcharts, and how I used it to share one image tag across two modules of an umbrella chart."
myst:
  html_meta:
    description: "How the global key in Helm values works, why it only matters with subcharts, and how I used it to share one image tag across two modules of an umbrella chart."
og:title: "Helm Global Values: The Right Way to Share Values in an Umbrella Chart"
og:description: "How the global key in Helm values works, why it only matters with subcharts, and how I used it to share one image tag across two modules of an umbrella chart."
---

*__Blog Post Publish Date:__ 2026/11/19*

---

# Helm Global Values: The Right Way to Share Values in an Umbrella Chart

This blog post covers how Helm's `global` key passes values from a parent chart to its subcharts, including a hands-on example with an umbrella chart that sets one image tag for two modules in a single place.

## Global Values Reach Every Subchart

In Helm, **global values** are the values under the reserved `global` key, and every chart and subchart can read them. I first saw the key in the [External Secrets Operator chart](https://github.com/external-secrets/external-secrets/blob/main/deploy/charts/external-secrets/values.yaml) and in Bitnami charts such as [Fluent Bit](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/values.yaml#L15), and took it for a naming convention. It isn't one, although inside a single chart it behaves like any other key. The difference shows up when a chart has subcharts.

A parent chart, or umbrella chart, declares other charts as dependencies and configures each one in its `values.yaml` under a key with the subchart's name. Helm passes each subchart only its own block, without the prefix, so a subchart template reads `.Values.replicaCount`, not `.Values.mysubchart.replicaCount`. In the words of the [Helm documentation on subcharts and globals](https://helm.sh/docs/chart_template_guide/subcharts_and_globals/#global-chart-values), "a subchart cannot access the values of its parent."

`global` is the exception to that scoping. Helm reserves `Values.global` for values that "can be accessed from any chart or subchart by exactly the same name". A value under `global` in the parent therefore reaches every subchart as `.Values.global.<name>`. Any other key in the parent stays invisible to the subchart unless it sits in the subchart's block.

__NOTE__: Setting `global` in the umbrella chart's values is not enough. The imported subchart must be written to read those values. `global` is a mechanism for the chart developer, who decides which values are worth reading from the parent chart and templates them from `.Values.global`. To use an image tag set in the parent's `global`, the subchart template has to read `.Values.global.image.tag`. A template that reads only `.Values.image.tag` keeps using the subchart's own value, even when the parent defines `global.image.tag`. The External Secrets Operator [deployment template](https://github.com/external-secrets/external-secrets/blob/390b0456d8be8b02f6d015f7795e735301cca5fe/deploy/charts/external-secrets/templates/deployment.yaml#L41-L47) does this with `imagePullSecrets`, reading `.Values.imagePullSecrets` first and falling back to `.Values.global.imagePullSecrets`. The Bitnami Fluent Bit chart passes `.Values.global` to its image helper in [`_helpers.tpl`](https://github.com/bitnami/charts/blob/2aac71a990b7e7c9a882bdce59855022894ac361/bitnami/fluent-bit/templates/_helpers.tpl#L12-L14), so a `global.imageRegistry` set in the parent replaces the image registry.

The [charts reference](https://helm.sh/docs/topics/charts/#global-values) adds three rules. Globals also reach the subcharts of subcharts. When the parent and a subchart define the same global, the parent wins. And globals must be declared explicitly, so you can't use an existing non-global key as a global.

To see the three cases side by side, take an umbrella chart that imports a subchart as `billing`, with these values:

```yaml
# umbrella/values.yaml
replicaCount: 1

billing:
  replicaCount: 2

global:
  image:
    tag: "2.3.1"
```

Each key reaches the templates of the two charts in a different way:

| Key in the umbrella `values.yaml` | How the umbrella templates read it | How the `billing` templates read it |
| --- | --- | --- |
| `replicaCount` | `.Values.replicaCount` (`1`) | No access |
| `billing.replicaCount` | `.Values.billing.replicaCount` (`2`) | `.Values.replicaCount` (`2`) |
| `global.image.tag` | `.Values.global.image.tag` (`"2.3.1"`) | `.Values.global.image.tag` (`"2.3.1"`) |

## One Global Image Tag for Two Modules

`global` clicked for me with an internal application at work. I wrote a chart for it and an umbrella chart that imports that chart twice, once per application module, each with its own values. The umbrella works like a bounded context for the modules. Both run the same container image, and I didn't want to repeat the tag in each module's values.

<img src="/_static/2026/2026-11-19/helm-global-values.gif" alt="Animated diagram of an umbrella chart values.yaml with a global block and two module blocks, billing and orders. Each module block reaches only its own aliased subchart, charts/billing or charts/orders, without the prefix. The global block reaches both subcharts as .Values.global, so both render the image tag 2.3.1. When global.image.tag changes to 2.4.0, both modules render 2.4.0." loading="lazy">

The umbrella chart imports the application chart once per module with [`alias`](https://helm.sh/docs/topics/charts/#alias-field-in-dependencies), the dependency field for adding the same chart more than once. The module names are examples:

```yaml
# umbrella/Chart.yaml
apiVersion: v2
name: my-app-bundle
version: 0.1.0
dependencies:
  - name: app
    alias: billing
    version: 0.1.0
  - name: app
    alias: orders
    version: 0.1.0
```

The tag lives once, under `global` at the root of the umbrella values. Each module block only has its own settings:

```yaml
# umbrella/values.yaml
global:
  image:
    tag: "2.3.1"

billing:
  module: billing

orders:
  module: orders
```

The application template uses the global tag when it is set and falls back to the chart's own value:

```yaml
# app/templates/deployment.yaml
image: "{{ .Values.image.repository }}:{{ .Values.global.image.tag | default .Values.image.tag }}"
```

The application chart also declares the global key in its `values.yaml`, with an empty default:

```yaml
# app/values.yaml
global:
  image:
    tag: ""

module: ""

image:
  repository: registry.example.com/my-app
  tag: "1.0.0"
```

`helm template` renders both modules with the global tag:

```bash
helm template rel ./umbrella | grep image:
```

```yaml
image: "registry.example.com/my-app:2.3.1"
image: "registry.example.com/my-app:2.3.1"
```

Bumping every module now takes one value, such as `--set global.image.tag=2.4.0`, and the application chart still works standalone with its own `image.tag`. To check which values each subchart receives after the merge, the JSON dump from [Helm Tips: Inspect Your Chart Context with JSON](/blog/2026/2026-02-25-helm-tips-inspect-context.md) shows `global` inside each subchart's `.Values`. For how I decide what to template in the application chart, see [Helm Charts: Development Practices from a Programmer's Perspective](/blog/2025/2025-02-25-helm-best-practices.md).

## YAML Anchors Break Across Values Files

Before `global`, I shared parameters across module blocks with [YAML anchors](https://yaml.org/spec/1.2.2/#anchors-and-aliases), defining the tag once with `&tag` and referencing it with `*tag`. Anchors only resolve inside the file being parsed. When I split the umbrella values into more than one file, a file passed with `-f` couldn't reference an anchor from another one. `global` doesn't have that limit, because Helm merges all values files before passing the global block to the subcharts.

## Key Takeaways

- `global` is a reserved key that any chart or subchart reads as `.Values.global.<name>`.
- Subcharts see only their own block of the parent's values, except for `global`.
- Inside a single chart, `global` is a regular value that reaches only the templates that read it.
- When the parent and a subchart define the same global, the parent's value wins.
- An umbrella chart that imports the same chart several times with `alias` can set a shared value, such as the image tag, once under `global`.
- A subchart that reads a global should declare it with an empty default, so it still renders on its own.
- YAML anchors only resolve inside one file and break when values are split across files.

## References

- [Subcharts and Global Values (Helm)](https://helm.sh/docs/chart_template_guide/subcharts_and_globals/)
- [Charts: Global Values (Helm)](https://helm.sh/docs/topics/charts/#global-values)
- [Charts: Scope, Dependencies, and Values (Helm)](https://helm.sh/docs/topics/charts/#scope-dependencies-and-values)
- [Charts: Alias field in dependencies (Helm)](https://helm.sh/docs/topics/charts/#alias-field-in-dependencies)
- [YAML 1.2.2: Anchors and Aliases (YAML)](https://yaml.org/spec/1.2.2/#anchors-and-aliases)
- [External Secrets Operator chart values (External Secrets)](https://github.com/external-secrets/external-secrets/blob/main/deploy/charts/external-secrets/values.yaml)
- [Fluent Bit chart values (Bitnami)](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/values.yaml#L15)

---

> *I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Helm Global Values: The Right Way to Share Values in an Umbrella Chart",
      "description": "How the global key in Helm values works, why it only matters with subcharts, and how I used it to share one image tag across two modules of an umbrella chart.",
      "datePublished": "2026-11-19",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-11-19-helm-global-values/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-11-19-helm-global-values/",
      "image": "https://carlosneto.dev/_static/2026/2026-11-19/helm-global-values.gif",
      "keywords": ["Helm", "global values", "subcharts", "umbrella chart", "Kubernetes"],
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
        {"@type": "ListItem", "position": 3, "name": "Helm Global Values: The Right Way to Share Values in an Umbrella Chart"}
      ]
    }
  ]
}
</script>
```

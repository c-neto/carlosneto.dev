---
tags: helm
date: "2025-02-25"
category: Kubernetes
author: Carlos Neto
title: "Helm Charts: Development Practices from a Programmer's Perspective"
description: "How programming principles such as Simple Made Easy, DRY, YAGNI, and reusable libraries apply to Helm chart development, and when the complexity of Helm pays for itself."
myst:
  html_meta:
    description: "How programming principles such as Simple Made Easy, DRY, YAGNI, and reusable libraries apply to Helm chart development, and when the complexity of Helm pays for itself."
og:title: "Helm Charts: Development Practices from a Programmer's Perspective"
og:description: "How programming principles such as Simple Made Easy, DRY, YAGNI, and reusable libraries apply to Helm chart development, and when the complexity of Helm pays for itself."
---

*__Blog Post Publish Date:__ 2025/02/25*

---

# Helm Charts: Development Practices from a Programmer's Perspective

This blog post applies programming principles to Helm chart development. It covers when Helm's complexity pays for itself, how it removes duplicated manifests (DRY), why over-templating hurts (YAGNI), and how library charts keep patterns reusable.

In the last quarter of 2024, I went deep into Helm charts and hit several challenges. At first, creating a new chart felt like added complexity, and I didn't see a clear advantage over Kustomize. After days of reading about Helm, studying existing projects, and thinking it through, I started to see Helm as an ally instead of an overcomplicated tool. These are the main lessons.

## Why Helm Charts Are a Good Tool for IaC

**Helm** is a package manager for Kubernetes, and a **Helm chart** is a package of templated Kubernetes manifests plus the default values that fill them. Helm renders the templates with Go templates, so a chart can abstract a workload behind a small set of parameters. That makes it a strong tool for Infrastructure as Code (IaC).

One of Helm's main advantages is that charts are distributed as versioned artifacts, much like programming language packages or RPM and DEB packages. A chart can declare other charts as dependencies, so new solutions can be built on top of proven components.

Charts can be stored as OCI artifacts in registries such as AWS Elastic Container Registry (ECR), or as tarball files, which makes deployments reproducible. CD tools such as Spinnaker and Argo CD deploy Helm charts natively.

Helm is most useful for reusable infrastructure components deployed to several clusters with environment-specific configuration. It reduces duplicated manifests in Git and makes them easier to maintain.

## Simple Made Easy: Is Helm Overengineering?

> "_Complexity has to pay for itself. It has to buy you something._"  
> Rich Hickey, _Simple Made Easy_ (2011)

My first reaction to Helm was: "_Oh my God, this is so complex. Am I just adding complexity?_" Like any new tool, Helm has a learning curve. The way past it is to understand the problem Helm solves. If you think Helm is complex, try maintaining several nearly identical Kubernetes manifests that differ by a few parameters per cluster. That is a recipe for chaos.

Helm is overengineering only if it solves a problem you don't have. Its complexity pays for itself when it removes a bigger problem, such as the same manifests duplicated across environments. When you manage workloads across several clusters, Helm isn't overhead, it's the trade-off that keeps them maintainable.

## DRY: Removing Duplicated Kubernetes Manifests

> "_DRY (Don't Repeat Yourself) is about the duplication of knowledge, of intent. It's about expressing the same thing in two different places, possibly in two totally different ways._"  
> Andrew Hunt and David Thomas, _The Pragmatic Programmer_

Most companies keep separate environments for each stage of development: a development environment for internal testing, a staging environment for validation, and a production environment for real users.

In that setup, you usually run the same applications on several Kubernetes clusters with small differences, such as Ingress settings, resource requests, and environment variables. The simplest approach is one set of manifests per environment, with the same structure and different values. It works, but it creates __duplicated code__.

Duplicated manifests increase the risk of errors and drift. With one or two environments, it's manageable. With three or more, it stops scaling: a single fix has to be applied to several files.

Helm avoids that with templates. The structure of the manifests lives in the chart, and each environment has its own values file with only the parameters that change. For example:

```{code-block} yaml
:caption: templates/deployment.yaml (excerpt)

spec:
  replicas: {{ .Values.replicaCount }}
  template:
    spec:
      containers:
        - name: app
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

::::{grid}

:::{grid-item-card}
```{code-block} yaml
:caption: values-dev.yaml

replicaCount: 1
resources:
  requests:
    cpu: 100m
```
:::

:::{grid-item-card}
```{code-block} yaml
:caption: values-prod.yaml

replicaCount: 3
resources:
  requests:
    cpu: "1"
```
:::

::::

```{code-block} bash
$ helm upgrade --install my-app ./my-app -f values-prod.yaml
```

One chart renders the manifests for every environment from its values file. That keeps environments consistent, makes fixes a one-place change, and reduces errors.

## YAGNI: Avoid Over-Templating

> _"Always implement things when you actually need them, never when you just foresee that you need them."_  
> Ron Jeffries, on the XP principle _"You aren't gonna need it" (YAGNI)_

**YAGNI** (You Aren't Gonna Need It) is the principle that you should not build features or abstractions before you actually need them. In Helm, it means creating templates only for structures that are well defined and actually repeated. A common mistake is over-templating: so many parameters that the chart is flexible on paper but hard to maintain.

If you're writing many template functions to handle every possible variation in `values.yaml`, the template probably lacks a clear structure. Instead of simplifying deployments, it adds complexity that makes debugging and maintenance harder.

Worse than having no template is maintaining template functions that are never used. Every extra function, conditional, or parameter adds cognitive load. A team that inherits a chart full of unused logic has to understand and maintain complexity that adds nothing. Solve the problems you have now, not hypothetical future ones.

## Library Charts: Reusable Patterns

Helm has two [chart types](https://helm.sh/docs/topics/library_charts/): __application__ and __library__. An application chart is a complete package that you deploy, with all the Kubernetes resources an application needs. A library chart holds reusable templates and functions that other charts use, and it is never deployed on its own. It works as an abstraction layer for components that many charts share.

A good example is the Bitnami Common library chart. Its functions and patterns are used across the whole Bitnami charts repository, which keeps their charts consistent and easier to maintain:

- [Bitnami Common library chart](https://github.com/bitnami/charts/tree/main/bitnami/common)
- [How the Bitnami Fluent Bit chart uses it](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/templates/configmap.yaml#L11)

## Helm as a Way to Think About Infrastructure

Programming principles such as DRY, YAGNI, and modular design make Helm charts much better. Helm is more than a templating tool for Kubernetes manifests: it's a way to think about infrastructure as modular, reusable components, something any developer can appreciate. Applied with care, these practices let teams scale their deployments with less overhead and keep them easy to maintain.

When a chart grows, debugging what the templates receive becomes the hard part. I wrote about a trick for that in [Helm Tips: Inspect Your Chart Context with JSON](/blog/2026/2026-02-25-helm-tips-inspect-context.md). I also use Helm to template Logstash pipelines, as I describe in [Logstash DB Enrichment](/blog/2025/2025-02-16-logstash-db-enrichment.md).

## Key Takeaways

- Helm renders Kubernetes manifests from Go templates and values, and distributes charts as versioned packages, including OCI artifacts.
- Helm's complexity pays for itself when it removes a bigger problem, such as near-identical manifests across several clusters.
- Keep one chart and one values file per environment instead of one copy of every manifest per environment.
- Don't over-template. Parameterize only what really changes, and remove functions and options nobody uses.
- Use library charts, such as Bitnami Common, to share templates and functions across charts.

## References

- [Chart best practices (Helm)](https://helm.sh/docs/chart_best_practices/)
- [Library charts (Helm)](https://helm.sh/docs/topics/library_charts/)
- [Yagni (Martin Fowler)](https://martinfowler.com/bliki/Yagni.html)
- [Don't repeat yourself (Wikipedia)](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [Anti-pattern (Wikipedia)](https://en.wikipedia.org/wiki/Anti-pattern)
- [The Twelve-Factor App (12factor.net)](https://12factor.net/)
- [Bitnami Common library chart (GitHub)](https://github.com/bitnami/charts/tree/main/bitnami/common)

*I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Helm Charts: Development Practices from a Programmer's Perspective",
      "description": "How programming principles such as Simple Made Easy, DRY, YAGNI, and reusable libraries apply to Helm chart development, and when the complexity of Helm pays for itself.",
      "datePublished": "2025-02-25",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2025/2025-02-25-helm-best-practices/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2025/2025-02-25-helm-best-practices/",
      "keywords": ["Helm", "Kubernetes", "DRY", "YAGNI", "library charts"],
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
        {"@type": "ListItem", "position": 3, "name": "Helm Charts: Development Practices from a Programmer's Perspective"}
      ]
    }
  ]
}
</script>
```

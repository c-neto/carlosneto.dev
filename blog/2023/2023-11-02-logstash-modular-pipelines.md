---
tags: logstash, logs
date: "2023-11-12"
category: Observability
author: Carlos Neto
title: "Logstash Modular Pipelines: Reusing Inputs, Filters, and Outputs Without Duplication"
description: "How to split Logstash pipelines into input, filter, and output modules and compose them per application with glob patterns and environment variables, so pipelines stop duplicating code."
myst:
  html_meta:
    description: "How to split Logstash pipelines into input, filter, and output modules and compose them per application with glob patterns and environment variables, so pipelines stop duplicating code."
og:title: "Logstash Modular Pipelines: Reusing Inputs, Filters, and Outputs Without Duplication"
og:description: "How to split Logstash pipelines into input, filter, and output modules and compose them per application with glob patterns and environment variables, so pipelines stop duplicating code."
---

*__Blog Post Publish Date:__ 2023/11/12*

---

# Logstash Modular Pipelines: Reusing Inputs, Filters, and Outputs Without Duplication

This blog post covers a Logstash pipeline structure that removes duplicated code. Each `input`, `filter`, and `output` lives in its own file, and every application's pipeline is composed from those modules with a glob pattern and an environment variable. It includes an example configuration, a Docker Compose lab to try it, and my opinion on when the structure is worth it.

## How a Logstash Pipeline Is Structured

Logstash is a great tool for building log pipelines. Its plugins cover ingestion, processing, enrichment, and delivery to other systems. A **Logstash pipeline** is a configuration written in the Logstash configuration DSL (_Domain-Specific Language_), a high-level language designed for log processing.

According to the [configuration file structure](https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure) documentation, a pipeline has three main sections:

- `input`: where the logs come from.
- `filter`: how they are parsed, processed, and enriched.
- `output`: where the processed logs are sent.

## The Problem: More Pipelines, More Duplicated Code

As the number of pipelines grows, so does the duplicated code. For simple needs, one file with `input`, `filter`, and `output` together is enough. With large applications, such as distributed services on Kubernetes, avoiding duplication becomes one of the main challenges.

When several applications need different processing logic, there are two common approaches, and both have a cost:

- __One shared pipeline with conditionals__. The `filter` section checks a field such as a tag to decide which logic to apply. This avoids duplicating `input` and `output`, but it adds overhead to the `filter` section and makes it harder to find which application has a problem in the Logstash API metrics.
- __One pipeline per application__. Each application gets its own configuration file. This removes the `filter` overhead, but every pipeline repeats the same `input` and `output` configuration.

## The Solution: Modular Pipelines

The structure I use takes the good part of both approaches: __split the pipeline sections (`input`, `filter`, `output`) into separate files, and load only the ones each application needs into its own dedicated pipeline__.

Two Logstash features make this possible. [Glob pattern support](https://www.elastic.co/guide/en/logstash/current/glob-support.html) lets `path.config` load several files at once, and [environment variables](https://www.elastic.co/guide/en/logstash/current/environment-variables.html) let you choose those files outside the configuration.

## Configuration Example

The first step is to create the modules: each `input`, `filter`, and `output` goes in its own file, focused on one job.

```{code-block} bash
:caption: $ tree /usr/share/logstash/pipeline/

├── filter-app-a.cfg        # filter of the application-a logic parser
├── filter-app-b.cfg        # filter of the application-b logic parser
├── input-http.cfg          # input to receive logs from http protocol
├── input-rabbitmq.cfg      # input to receive logs from rabbitmq queue
├── output-opensearch.cfg   # output to forward logs processed to opensearch server 
└── output-http.cfg         # output to forward logs processed to http server
```

Next, define one pipeline per application, with `path.config` pointing to an environment variable:

```{code-block} yaml
:caption: $ cat /usr/share/logstash/config/pipeline.yml

- pipeline.id: application-a-pipeline
  path.config: "/usr/share/logstash/pipeline/${LOGSTASH_PIPELINE_APPLICATION_A}.cfg"

- pipeline.id: application-b-pipeline
  path.config: "/usr/share/logstash/pipeline/${LOGSTASH_PIPELINE_APPLICATION_B}.cfg"
```

Finally, set each variable to a glob pattern that lists the modules for that pipeline:

```{code-block} bash
:caption: $ env

LOGSTASH_PIPELINE_APPLICATION_A="{input-http,input-rabbitmq,filter-app-a,output-opensearch,output-http}"
LOGSTASH_PIPELINE_APPLICATION_B="{input-http,filter-app-b,output-opensearch}"
```

With these values, `application-a-pipeline` receives logs from HTTP and RabbitMQ, parses them with `filter-app-a.cfg`, and sends them to both OpenSearch and an HTTP server. `application-b-pipeline` receives logs only from HTTP, parses them with `filter-app-b.cfg`, and sends them only to OpenSearch.

## Advantages of the Modular Structure

- __No duplicated code__. The same module can be used by many pipelines, for example one `input` and one `output` shared by all of them.
- __Flexible composition__. A pipeline can load several modules of the same type, such as two outputs and three inputs.
- __Simpler filters__. Each `filter` file holds only one application's parsing logic, with no conditionals on tags to decide which logic to run.
- __Easier troubleshooting__. Each application keeps its own pipeline, so the Logstash metrics API still shows which one is slow or failing.
- __Easier tests__. Because inputs and outputs are chosen by an environment variable, you can test a `filter` with a mock `input` and `stdout` as the `output`, and check that the logic works before deploying it.

I created a Docker Compose lab to try this structure. You can find it on my GitHub: <i class="fa-brands fa-github"></i> [c-neto/my-devops-labs/blog/2023-11-12](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/).

## When the Modular Structure Is Worth It

Logstash handles both small and large workloads, and this structure is one way, not the only way, to deal with pipelines that keep growing. With only a few applications, it can add complexity you don't need.

I have used this structure and seen a big improvement in maintainability, especially in testing: I can test my `filter` logic by changing a single environment variable. My main goal is always to make pipelines easier to maintain, but every context has its own challenges. I recommend this structure when pipeline maintenance is getting hard, duplicated code is growing, and the Logstash configuration has become error-prone.

If you are sending these logs to OpenSearch, two related posts may help: [Logstash Sniffing](/blog/2024/2024-06-08-logstash-sniffing.md) for spreading ingestion across a scalable cluster, and [Logstash DB Enrichment](/blog/2025/2025-02-16-logstash-db-enrichment.md) for adding database data to events inside a `filter`.

## Key Takeaways

- A Logstash pipeline has three sections: `input`, `filter`, and `output`.
- One shared pipeline with conditionals overloads the `filter` section. One file per application duplicates `input` and `output`.
- Split each section into its own file, and compose each application's pipeline from those modules.
- `path.config` with an environment variable and a glob pattern such as `{input-http,filter-app-a,output-opensearch}` selects the modules per pipeline.
- Separate pipelines keep the Logstash metrics API useful for troubleshooting each application.
- Swapping inputs and outputs through an environment variable makes it easy to test `filter` logic with mock data and `stdout`.
- With only a few applications, a single simple pipeline may be enough.

## References

- [Structure of a pipeline (Logstash)](https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure)
- [Glob pattern support (Logstash)](https://www.elastic.co/guide/en/logstash/current/glob-support.html)
- [Using environment variables (Logstash)](https://www.elastic.co/guide/en/logstash/current/environment-variables.html)
- [Docker Compose lab for this post (GitHub)](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/)

---

> *I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Logstash Modular Pipelines: Reusing Inputs, Filters, and Outputs Without Duplication",
      "description": "How to split Logstash pipelines into input, filter, and output modules and compose them per application with glob patterns and environment variables, so pipelines stop duplicating code.",
      "datePublished": "2023-11-12",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2023/2023-11-02-logstash-modular-pipelines/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2023/2023-11-02-logstash-modular-pipelines/",
      "keywords": ["Logstash", "log pipelines", "pipelines.yml", "observability"],
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
        {"@type": "ListItem", "position": 3, "name": "Logstash Modular Pipelines: Reusing Inputs, Filters, and Outputs Without Duplication"}
      ]
    }
  ]
}
</script>
```

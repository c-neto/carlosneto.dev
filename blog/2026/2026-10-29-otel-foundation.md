---
tags: opentelemetry, prometheus, fluent-bit
date: "2026-10-29"
category: Observability
author: Carlos Neto
title: "OpenTelemetry: A Framework for Decoupling Your Observability"
description: "OpenTelemetry is not a database and doesn't compete with Fluent Bit, Logstash, or Jaeger. It standardizes how metrics, traces, and logs are structured, so you avoid vendor lock-in."
myst:
  html_meta:
    description: "OpenTelemetry is not a database and doesn't compete with Fluent Bit, Logstash, or Jaeger. It standardizes how metrics, traces, and logs are structured, so you avoid vendor lock-in."
og:title: "OpenTelemetry: A Framework for Decoupling Your Observability"
og:description: "OpenTelemetry is not a database and doesn't compete with Fluent Bit, Logstash, or Jaeger. It standardizes how metrics, traces, and logs are structured, so you avoid vendor lock-in."
---

*__Blog Post Publish Date:__ 2026/10/29*

---

# OpenTelemetry: A Framework for Decoupling Your Observability

OpenTelemetry is not a database, and it doesn't compete with Fluent Bit, Logstash, or Jaeger. It defines how metrics, traces, and logs are structured and transported, so your telemetry isn't tied to any vendor. The tools you already know can be the backends that receive it. This post explains that idea, the one component OpenTelemetry runs on its own, and where it fits.

## What It Is

When I started studying OpenTelemetry, I struggled to understand what it actually was. The [official definition](https://opentelemetry.io/docs/what-is-opentelemetry/) calls it _"an open-source, vendor-neutral observability framework"_, which didn't help me. I kept asking whether it was a database, a log shipper, or a replacement for Prometheus. It's none of them.

The problem it solves is vendor lock-in. Before it, each backend came with its own library, agent, and data format. If fifty services are instrumented with the Datadog library and the company moves to another tool, every service has to be changed and redeployed. OpenTelemetry fixes that with a standard. It defines the data model of each signal, the attribute names (such as `service.name` or `http.request.method`), an API your code calls, and OTLP, the protocol that carries the data.

The best comparison I know is SQLAlchemy in Python. Your code talks to SQLAlchemy, and the database behind it can be PostgreSQL, MySQL, or SQLite, so switching is mostly a matter of changing the connection URL. OpenTelemetry does the same for telemetry. Your code talks to the OpenTelemetry API, and the backend becomes a configuration choice.

<img src="/_static/2026/2026-10-29/opentelemetry-pieces.svg" alt="Diagram of OpenTelemetry's pieces. The application code calls the OTel API, the OTel SDK sends data over OTLP to an optional OTel Collector, which exports it to backends such as Prometheus, Datadog, Jaeger, and OpenSearch, which are not part of OpenTelemetry" loading="lazy">

Storage, queries, dashboards, and alerts stay with the backends. Jaeger [receives OTLP natively](https://www.jaegertracing.io/sdk-migration/) and stores traces, Prometheus 3 can [receive OTLP metrics](https://prometheus.io/docs/guides/opentelemetry/), and Fluent Bit has [OpenTelemetry input and output plugins](https://docs.fluentbit.io/manual/data-pipeline/outputs/opentelemetry), so it can take OTLP and forward it to OpenSearch or any other output. Commercial platforms accept OTLP too. What OpenTelemetry replaces is the vendor-specific instrumentation inside your code, not the tools that store and analyze the data. It doesn't replace your logging library either. Your code keeps using Python's `logging` or Log4j, and OpenTelemetry adds the trace ID to each log line.

## The Collector

Besides the API and SDK that live inside your application, the only component OpenTelemetry runs on its own is the Collector, and it's optional. The SDK can send data straight to a backend.

The Collector is a service that receives traces, metrics, and logs, processes them, and sends them to one or more backends. The processing is what makes it useful. It can change attributes, such as removing sensitive data or adding Kubernetes metadata, drop telemetry based on its metadata, and sample traces, either by keeping a percentage of them or by keeping only the ones with errors or high latency. It can also send the same data to two backends during a migration.

This is the part that overlaps with Fluent Bit and Logstash, since all three receive, transform, and forward data. Fluent Bit and Logstash were built around logs. The Collector is built around the OpenTelemetry data model for all three signals, so it understands traces. If your pipeline only moves logs and works well, there's no reason to swap it. If your applications send traces over OTLP, the Collector is the natural receiver, and it can run next to the log pipeline you already have.

## Where It Fits

OpenTelemetry pays off most in distributed systems, where a request crosses services written in different languages and owned by different teams, and one trace has to follow it through all of them. It also helps when you need to send the same data to more than one backend, or move from one vendor to another gradually, since services already instrumented with OpenTelemetry can coexist with ones that still use a vendor agent.

It also covers software you don't own, from two sides. Auto-instrumentation turns your application's calls to a database or cache, such as PostgreSQL or Redis, into spans without code changes. The Collector's receivers collect from the outside, by scraping Prometheus endpoints, reading log files and syslog, or querying the Kubernetes API.

That comes at a cost. There are new concepts to learn, SDKs to configure in every service, and possibly a Collector to deploy, scale, and monitor.

My take is that OpenTelemetry isn't a default. It's the right tool when there are many services and teams, and what I value most is the separation it brings. The application team decides what to measure, and the platform team decides where the data goes.

## Key Takeaways

- OpenTelemetry is not a database and doesn't store, query, or alert.
- It defines how metrics, traces, and logs are structured and transported, which removes vendor lock-in.
- Like SQLAlchemy for databases, the code talks to one API and the backend becomes configuration.
- Jaeger, Prometheus, Fluent Bit, and commercial platforms can receive OpenTelemetry data as backends or pipelines.
- The Collector is the only component OpenTelemetry runs on its own, and it is optional.
- The Collector receives all three signals and can mutate, filter by metadata, and sample them.
- The benefits grow with the number of services, languages, teams, and backends, and so does the operational cost.

## References

- [What is OpenTelemetry? (OpenTelemetry)](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [OpenTelemetry Collector (OpenTelemetry)](https://opentelemetry.io/docs/collector/)
- [Collector receivers (OpenTelemetry)](https://opentelemetry.io/docs/collector/components/receiver/)
- [Using Prometheus as your OpenTelemetry backend (Prometheus)](https://prometheus.io/docs/guides/opentelemetry/)
- [OpenTelemetry output plugin (Fluent Bit)](https://docs.fluentbit.io/manual/data-pipeline/outputs/opentelemetry)
- [OpenTelemetry Certified Associate prep course (KodeKloud)](https://notes.kodekloud.com/docs/Prep-Course-OpenTelemetry-Certified-Associate-OTCA-Certification/index)

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
      "headline": "OpenTelemetry: A Framework for Decoupling Your Observability",
      "description": "OpenTelemetry is not a database and doesn't compete with Fluent Bit, Logstash, or Jaeger. It standardizes how metrics, traces, and logs are structured, so you avoid vendor lock-in.",
      "datePublished": "2026-10-29",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-10-29-otel-foundation/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-10-29-otel-foundation/",
      "image": "https://carlosneto.dev/_static/2026/2026-10-29/opentelemetry-pieces.svg",
      "keywords": ["OpenTelemetry", "OpenTelemetry Collector", "vendor lock-in", "Fluent Bit", "Jaeger"],
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
        {"@type": "ListItem", "position": 3, "name": "OpenTelemetry: A Framework for Decoupling Your Observability"}
      ]
    }
  ]
}
</script>
```

---
tags: opensearch, prometheus, fluent-bit, metrics
date: "2026-11-03"
category: Observability
author: Carlos Neto
title: Stop Extracting Metrics from OpenSearch Logs
description: Why counting log lines in OpenSearch is an expensive way to get a metric, how a Prometheus counter answers the same question for almost nothing, and how Fluent Bit can extract the metric at ingestion when you cannot change the code.
myst:
  html_meta:
    description: Why counting log lines in OpenSearch is an expensive way to get a metric, how a Prometheus counter answers the same question for almost nothing, and how Fluent Bit can extract the metric at ingestion when you cannot change the code.
og:title: Stop Extracting Metrics from OpenSearch Logs
og:description: Why counting log lines in OpenSearch is an expensive way to get a metric, how a Prometheus counter answers the same question for almost nothing, and how Fluent Bit can extract the metric at ingestion when you cannot change the code.
---

*__Blog Post Publish Date:__ 2026/11/03*

---

# Stop Extracting Metrics from OpenSearch Logs

This blog post explains why counting log lines in OpenSearch is an expensive way to produce a metric. The same number captured as a Prometheus counter is stored once and read almost for free. When you cannot change the application, Fluent Bit can extract that metric while the logs are ingested, so OpenSearch never has to rebuild it at query time.

## How a Log Store Becomes a Metrics Database

For the past five years, I have worked on large OpenSearch deployments running on Kubernetes. One of the hardest problems was keeping query latency low while the volume of logs kept growing. I tried many performance optimizations, but the most useful step was a different question: how was the data actually being used?

In one case, the logs were not only stored for troubleshooting. Teams also queried them to find specific events and extract operational numbers, which made query latency critical and more expensive as ingestion grew. That taught me that tuning the infrastructure is only part of the answer. You also have to understand what the data is, how it is consumed, and which tool fits each use case.

It usually starts small. Someone needs a number, such as _"how many payments failed in the last hour?"_. The logs are already there, so they write a query that counts the matching log lines and pin it to a dashboard. It works. Then the dashboard gets slow, the log cluster runs hot, and the query that counts errors per minute starts timing out during an incident, when you need it most. The cause is rarely a bad query or an undersized cluster. Logs are being asked to do a metric's job.

## Logs and Metrics Are Different Shapes of Data

A **log** is a record of one event, written for a human (or an AI agent) to read. It is detailed, high-cardinality text:

```text
2026-02-14T10:32:11Z level=error service=payments txn_id=8f3c user_id=22190 msg="payment authorization failed" provider=acme code=INSUFFICIENT_FUNDS latency_ms=812
```

The value of a log is its context. When something breaks, it tells you what happened, to whom, and often why. A log answers "walk me through this specific event."

A **metric** is a number sampled over time. It is small, structured, and built to be aggregated:

```text
payment_failures_total{provider="acme", code="INSUFFICIENT_FUNDS"} 48213
```

This metric does not describe one payment. It counts all of them, so it can be summed, rated, and broken down cheaply across huge volumes. A metric answers "how many, how fast, how much, right now and over time."

| Signal | What it is | Primary question | Natural shape |
| --- | --- | --- | --- |
| Logs | Discrete event records | "What exactly happened here?" | High-cardinality text |
| Metrics | Numeric samples over time | "How many / how fast / how much?" | Small numeric time series |

When you ask a log store to answer the metric question, you force one shape of data to behave like the other. That is where the cost comes from.

## Why Counting Log Lines Doesn't Scale

OpenSearch is very good at full-text search. Its inverted index maps terms to the documents that contain them, so a question like "show me every error from `payments` mentioning `acme` yesterday" comes back fast. That is a search workload, and OpenSearch is the right tool for it.

Failed payments per minute is a different kind of question. As a log query, it looks like this:

```opensearch
GET my-app-logs-index-*/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "match": { "level": "error" } },
        { "match_phrase": { "msg": "payment authorization failed" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "per_minute": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1m"
      }
    }
  }
}
```

The query works, but look at what the cluster does to return one small time series:

- __The number is rebuilt on every read__. No `failures_per_minute` value is stored anywhere, only the raw events. OpenSearch scans the matching documents and builds the count again each time the dashboard refreshes.
- __The cost follows the raw volume__. To return 1,440 numbers (one per minute for a day), the cluster filters and buckets potentially millions of large text documents.
- __Breakdowns and long retention multiply the work__. Splitting failures by provider and error code over 90 days fans the aggregation out across even more documents. You also have to keep verbose logs for 90 days only to keep a counter alive, long after they stopped being useful for debugging.
- __It competes with the real workload__. These aggregations run on the same hot nodes that handle ingestion and incident searches, so the dashboard slows down the logging the cluster exists to serve.

OpenSearch has date histograms, aggregations, and dashboards, so it can do this. It is just not built for it. Counting term matches to produce a long-lived counter is a query-time reconstruction of data that was never stored as a measurement, and it gets worse as volume and retention grow.

## The Same Number as a Prometheus Counter

The fix is to capture the number in the right shape from the start. Instead of logging a line and counting it later, the application increments a counter when a payment fails and exposes it to Prometheus:

```python
from prometheus_client import Counter

payment_failures = Counter(
    "payment_failures_total",
    "Total number of failed payment authorizations",
    ["provider", "code"],
)

# in the failure path:
payment_failures.labels(provider="acme", code="INSUFFICIENT_FUNDS").inc()
```

The application serves this counter on a `/metrics` endpoint, and Prometheus scrapes it, every 15 seconds for example. The number is now the stored data: one running total per label combination. Because a [counter](https://prometheus.io/docs/concepts/metric_types/) only goes up, [`rate()`](https://prometheus.io/docs/prometheus/latest/querying/functions/#rate) turns it into failures per second over any window, grouped by any label, and it handles counter resets after a deploy. Failures per minute become a short, instant query:

```promql
# per-second rate of failures over the last 5 minutes, by provider and code
rate(payment_failures_total[5m])

# or per-minute, summed across providers
sum(rate(payment_failures_total[1m])) by (code) * 60
```

Here is what each system does for the same question:

| | Logs-as-metrics (OpenSearch) | Real metric (Prometheus) |
| --- | --- | --- |
| Where the number lives | Reconstructed at query time | Stored directly as a time series |
| Data scanned per read | Millions of text documents | A handful of pre-aggregated samples |
| Cost scales with | Raw log volume + retention | Number of time series (tiny) |
| Breakdown by labels | Expensive aggregation fan-out | Native, free (`by (code)`) |
| Retention for 90d of "rate" | Keep 90d of fat logs | Keep tiny numeric samples |
| Load during an incident | Heavy, competes with log search | Negligible |

OpenSearch pays for a full-volume scan to see that failures are spiking. Prometheus pays almost nothing, because it reads the number instead of rebuilding it. If you instrument with [OpenTelemetry](/blog/2026/2026-10-29-otel-foundation.md) instead of the Prometheus client, the idea is the same: the application emits the measurement.

## Workaround: Extract the Metric at Ingestion With Fluent Bit

The counter in the application is the right answer, but sometimes you cannot touch the code. It may be a legacy service nobody wants to rebuild, a closed-source component, or a third-party app that only writes logs and will never expose `/metrics`. You still need the number.

The middle ground is not counting log lines in OpenSearch. It is turning the event into a metric inside the log pipeline, before the log reaches storage. The log shipper already sees every line, so it can match the lines that represent the event and increment a real counter on the spot. The log still goes to OpenSearch for investigation, and the metric is emitted next to it.

Fluent Bit does this with the [`log_to_metrics`](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics) filter. It needs structured records, though. Without a parser, the [`tail`](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail) input stores each line as a single string under `log`, so fields like `msg`, `provider`, and `code` do not exist yet. The sample log above is in logfmt, so the input uses a [logfmt parser](https://docs.fluentbit.io/manual/data-pipeline/parsers/logfmt) first. The filter then matches the event with a `KEY REGEX` rule and turns fields into labels. The [`prometheus_exporter`](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter) output exposes the result:

```{code-block} yaml
:caption: fluent-bit.yaml

service:
  flush: 1
  log_level: info

parsers:
  - name: logfmt
    format: logfmt

pipeline:
  inputs:
    - name: tail
      path: /var/log/payments/*.log
      tag: payments.log
      # turn each logfmt line into a structured record (msg, provider, code, ...)
      parser: logfmt

  filters:
    # emit a counter every time a line denotes a failed payment
    - name: log_to_metrics
      match: payments.log
      tag: payment_metrics
      metric_mode: counter
      metric_name: payment_failures_total
      metric_description: "Total number of failed payment authorizations"
      # KEY REGEX: only the records that represent the event
      regex: 'msg ^payment authorization failed$'
      # turn record fields into metric labels, same breakdown you wanted
      label_field:
        - provider
        - code

  outputs:
    # logs still go to OpenSearch for investigation
    - name: opensearch
      match: payments.log
      host: opensearch
      port: 9200
      index: payments-logs

    # metrics are exposed for Prometheus to scrape
    - name: prometheus_exporter
      match: payment_metrics
      host: 0.0.0.0
      port: 9999
```

Prometheus scrapes the exporter and gets the same counter you would have written in the code. Fluent Bit prefixes the name with `log_metric_counter_` by default:

```{code-block} shell
:caption: $ curl -s http://127.0.0.1:9999/metrics

# HELP log_metric_counter_payment_failures_total Total number of failed payment authorizations
# TYPE log_metric_counter_payment_failures_total counter
log_metric_counter_payment_failures_total{provider="acme",code="INSUFFICIENT_FUNDS"} 48213
```

The number is computed once, as the log passes through, instead of on every dashboard refresh. OpenSearch keeps the raw logs for investigating a specific event, and the metric lives in a store that is cheap to query and cheap to retain. If you already run Fluent Bit in the cluster, this fits in the same pipeline that [collects pod logs](/blog/2025/2025-06-22-kubernetes-logs-simplified.md).

This is still a workaround. You are parsing text to decide what counts, so a change in the log format can silently break the counter, and the event has to be logged in the first place. A counter in the code carries business meaning that a regex on a log line can only approximate, so instrument the application whenever you can. When the source is out of reach, extracting the metric at ingestion is far better than hammering the log store with query-time aggregations.

## Right Tool for Each Signal

None of this makes OpenSearch the wrong choice. For logs, it is a great tool, and the inverted index makes event search and investigation fast. The mistake is using it for a signal it was not built to carry.

| Signal | Purpose-built tools | Why they fit |
| --- | --- | --- |
| Logs | OpenSearch / Elasticsearch, Loki | Inverted index / label index tuned for text search over events |
| Metrics | Prometheus, Mimir, VictoriaMetrics | Time-series storage with cheap aggregation and rate math |

You can force every signal into one system, but you end up with slow dashboards, bloated retention, and query-time hacks that approximate what a purpose-built engine does natively. There is no silver bullet in a telemetry architecture. The best architecture is the one where each signal lands in the tool shaped for it.

Part of getting there is organizational. Good observability is a partnership between teams. The application team instruments the code, because only the people who know the business logic know which events matter and which labels make a metric meaningful. The infrastructure team provides the pipelines that ingest, store, and expose each signal where it belongs. A `payment_failures_total{code=...}` counter carries business meaning that infrastructure cannot invent from the outside.

## Key Takeaways

- Logs describe individual events. Metrics are numbers sampled over time. Treat them as different kinds of data.
- Counting log lines in OpenSearch rebuilds the number on every read, so the cost grows with raw log volume and retention.
- Metric dashboards on the log cluster run on the same hot nodes that serve ingestion and incident searches.
- A Prometheus counter stores the number once. `rate()` turns it into any per-second or per-minute view, grouped by any label.
- When you cannot change the code, extract the metric at ingestion with Fluent Bit's `log_to_metrics` filter. Parse the line first so the fields exist.
- Ingestion-time metrics are a workaround: a log format change can break them silently. Instrument the application when you can.
- Keep each signal in a tool built for it, and let the application team decide which events and labels matter.

## References

- [Aggregations (OpenSearch)](https://docs.opensearch.org/latest/aggregations/)
- [Metric types (Prometheus)](https://prometheus.io/docs/concepts/metric_types/)
- [Query functions: rate() (Prometheus)](https://prometheus.io/docs/prometheus/latest/querying/functions/#rate)
- [Log to metrics filter (Fluent Bit)](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics)
- [Tail input (Fluent Bit)](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail)
- [Logfmt parser (Fluent Bit)](https://docs.fluentbit.io/manual/data-pipeline/parsers/logfmt)
- [Prometheus exporter output (Fluent Bit)](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter)

*I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Stop Extracting Metrics from OpenSearch Logs",
      "description": "Why counting log lines in OpenSearch is an expensive way to get a metric, how a Prometheus counter answers the same question for almost nothing, and how Fluent Bit can extract the metric at ingestion when you cannot change the code.",
      "datePublished": "2026-11-03",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-11-03-stop-extracting-metrics-from-opensearch-logs/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-11-03-stop-extracting-metrics-from-opensearch-logs/",
      "keywords": ["OpenSearch", "Prometheus", "Fluent Bit", "metrics", "logs", "observability"],
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
        {"@type": "ListItem", "position": 3, "name": "Stop Extracting Metrics from OpenSearch Logs"}
      ]
    }
  ]
}
</script>
```

---
tags: opensearch, prometheus, metrics, logs, observability
date: "2026-10-28"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/10/28*

---

# Stop Extracting Metrics from OpenSearch Logs

This blog post explains what metrics, APM, and logs each are, why they are fundamentally different kinds of data, why extracting metrics from logs does not scale, and how the same number captured as a real metric is dramatically cheaper and faster. The goal is simple: use the right tool for each signal.

## Introduction

One of the most common and most expensive mistakes in observability is quietly treating a log store as a metrics database. It usually starts innocently. Someone needs a number (_"how many payments failed in the last hour?"_), the logs are right there, so they write a query that counts matching log lines and pins it to a dashboard. It works. For a while.

Then the dashboard gets slow. The log cluster gets hot. The query that counts "errors per minute" starts timing out at exactly the moment you need it most, during an incident. The root cause is not a bad query or an undersized cluster. It is a category error: logs were asked to do a metric's job.


## The Three Pillars Are Three Different Data Shapes

"Observability" is an umbrella over three distinct signal types. They are not interchangeable, because the shape of the data underneath each one is different.

### Logs: Event Description

A log is a discrete record of something that happened, meant to be read and understood by a human (or searched by a machine). It is rich, high-cardinality, and textual:

```log
2026-02-14T10:32:11Z level=error service=payments txn_id=8f3c user_id=22190
  msg="payment authorization failed" provider=acme code=INSUFFICIENT_FUNDS latency_ms=812
```

The value of a log is in its detail and context. When something breaks, a log tells you what happened, to whom, where, and often why. Logs answer: "walk me through this specific event."

### Metrics: Event Quantification 

A metric is a numeric measurement sampled over time. It is small, structured, and aggregatable by design:

```json
payment_failures_total{provider="acme", code="INSUFFICIENT_FUNDS"} 48213
```

A metric does not describe one payment. It counts all of them. Its whole purpose is to be aggregated, rated, and summarized cheaply across huge volumes. Metrics answer: _"how many, how fast, how much, right now and over time." Metrics is always about number, and was perfectly desging and optmize to plot dashboards.

### APM: Follow a Request

Application Performance Monitoring, built on distributed tracing, follows a single request as it hops across services, recording timing and causality at each span:

```
trace 8f3c  ├─ api-gateway        12ms
            ├─ payments-service   820ms   <-- the slow one
            │   └─ provider-call  798ms
            └─ ledger-service     14ms
```

APM answers: "where did the time go, and which service in the chain caused it?"

Three questions, three data shapes:

| Signal | What it is | Primary question | Natural shape |
| --- | --- | --- | --- |
| Logs | Discrete event records | "What exactly happened here?" | High-cardinality text |
| Metrics | Numeric samples over time | "How many / how fast / how much?" | Small numeric time series |
| APM / Traces | Request-scoped spans | "Where did the time go?" | Causal span trees |

## Why Logs Make Bad Metrics

OpenSearch is genuinely excellent at what it is designed for: full-text search over an inverted index. Give it millions of log lines and ask "show me every error from `payments` mentioning `acme` yesterday", and it will answer fast, because the inverted index maps terms to the documents that contain them. That is a search workload, and it is the right tool.

The problem is what happens when you ask it to behave like a metrics engine. Consider the number we wanted earlier, failed payments per minute. As a log query it looks like this:

```json
GET my-app-logs-index-*/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        {
          "match": {
            "level": "error"
          }
        },
        {
          "match_phrase": {
            "msg": "payment authorization failed"
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "now-24h"
            }
          }
        }
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

This works. But look at what the cluster has to do to produce one small time series:

1. The number was never stored, it is computed on every read. There is no `failures_per_minute` value indexed anywhere. OpenSearch has to scan matching documents and build the count at query time, every single time the dashboard refreshes. The data you want was never indexed; only the raw events were.
2. It must touch enormous volumes to produce a tiny answer. To return 1,440 numbers (one per minute for a day), it filters and buckets potentially millions of fat text documents. The cost of the answer is proportional to the raw log volume, not to the size of the result.
3. It fights cardinality and retention. Want failures broken down by provider and error code over 90 days? Now the aggregation fans out across even more documents, and you are forced to retain verbose logs purely to keep a counter alive, long after the logs' diagnostic value has expired.
4. It competes with the real workload. These heavy aggregations run on the same hot nodes handling ingestion and incident-time searches. The "metric" dashboard becomes a source of load that slows down the logging the cluster actually exists to serve.

OpenSearch can do this. It has date histograms, aggregations, even dashboards. The tooling exists. But this is not what the tool is optimized for. A log line primarily exists to describe an event so a human can understand what is happening. Deriving a long-lived counter from term matches is a query-time reconstruction of data that was never stored as a measurement, and that is not sustainable as volume and retention grow.

## The Same Number, Done Right: A Counter in the Application

Now capture the exact same information as a real metric. Instead of logging a line and counting it later, you instrument the application to increment a counter the moment a payment fails, and expose it to Prometheus:

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

The application exposes this on a `/metrics` endpoint, Prometheus scrapes it every 15 seconds, and now the number is the stored data: a monotonically increasing counter per label combination. Getting "failures per minute" is now a trivial, instant query:

```promql
# per-second rate of failures over the last 5 minutes, by provider and code
rate(payment_failures_total[5m])

# or per-minute, summed across providers
sum(rate(payment_failures_total[1m])) by (code) * 60
```

Compare what the two systems do for the identical question:

| | Logs-as-metrics (OpenSearch) | Real metric (Prometheus) |
| --- | --- | --- |
| Where the number lives | Reconstructed at query time | Stored directly as a time series |
| Data scanned per read | Millions of text documents | A handful of pre-aggregated samples |
| Cost scales with | Raw log volume + retention | Number of time series (tiny) |
| Breakdown by labels | Expensive aggregation fan-out | Native, free (`by (code)`) |
| Retention for 90d of "rate" | Keep 90d of fat logs | Keep tiny numeric samples |
| Load during an incident | Heavy, competes with log search | Negligible |

### Why `rate()` on a counter is the elegant part

A counter only ever goes up, which feels unintuitive until you see `rate()`. Because the raw value is a running total, Prometheus can compute the per-second increase over any window, and it correctly handles counter resets (deploys, restarts) by treating a drop to zero as a reset rather than a negative value.

That means from one cheap, ever-incrementing number you get:

- __Rate__: `rate(payment_failures_total[5m])` gives failures per second, smoothed.
- __Any window__: swap `[5m]` for `[1h]`, no re-indexing, no re-scan.
- __Any grouping__: `sum(... ) by (provider)` instantly, because the labels were stored with the sample.
- __Alerting__: `rate(...) > 0.5` is a cheap, reliable alert expression that will not melt your log cluster at 3 a.m.

The same insight ("failures are spiking") costs OpenSearch a full-volume scan and costs Prometheus almost nothing, because one tool reconstructs the number and the other simply reads it.

## This Is Not "OpenSearch Bad", It Is "Right Tool, Right Signal"

None of this means OpenSearch is the wrong choice. For logs, it is an outstanding tool. The inverted index makes event search and investigation fast. The mistake is not using OpenSearch, it is using it for a signal it was not built to carry.

Each pillar has engines designed around its data shape:

| Signal | Purpose-built tools | Why they fit |
| --- | --- | --- |
| Logs | OpenSearch / Elasticsearch, Loki | Inverted index / label index tuned for text search over events |
| Metrics | Prometheus, Mimir, VictoriaMetrics | Time-series storage with cheap aggregation and rate math |
| APM / Traces | Tempo, Jaeger, Zipkin | Trace storage optimized for span trees and request causality |

You can force everything into one system. But a single tool stretched across all three signals ends up unoptimized: slow dashboards, bloated retention, and a pile of query-time hacks to approximate what a purpose-built engine does natively. There is no silver bullet in a telemetry architecture. The best architecture is the one where each signal lands in the tool shaped for it.

## Observability Is a Shared Responsibility

The last piece is organizational, not technical. Good observability is not something infrastructure can deliver alone by standing up clusters and dashboards. It is a partnership:

- __The application team instruments the code.__ Only the people who understand the business logic know which events matter, what to count, and which labels (provider, payment method, customer tier) make a metric meaningful. A `payment_failures_total{code=...}` counter encodes business meaning that infrastructure cannot invent from the outside.
- __The infrastructure team provides the pipes.__ Scalable, well-configured systems to ingest, store, and expose each signal, logs where logs belong, metrics where metrics belong, traces where traces belong, and to render it all legibly.

Observability is exactly that handshake: business-aware instrumentation from the inside, meeting solid, signal-appropriate infrastructure on the outside, so that what is happening within the application becomes clearly visible from without.

## Conclusion (Author Opinion)

I have cleaned up enough "count the log lines" dashboards to have strong feelings here. The ones that hurt most were never bad queries, they were the right number captured in the wrong system, and the fix was almost always a small counter in the application rather than a cleverer OpenSearch aggregation.

So before you add one more "count the log lines" panel to a dashboard, ask the real question: am I trying to understand an event, or measure one? If you are measuring, the answer is not a better log query, it is a metric. OpenSearch stays the tool I recommend for logs, and I just stop asking it to be a metrics database.

## References

- <https://opensearch.org/docs/latest/aggregations/>
- <https://prometheus.io/docs/concepts/metric_types/>
- <https://prometheus.io/docs/prometheus/latest/querying/functions/#rate>

---
tags: opensearch, prometheus, fluentbit, metrics, logs, observability
date: "2026-11-03"
category: opensearch
---

*__Blog Post Publish Date:__ 2026/11/03*

---

# Stop Extracting Metrics from OpenSearch Logs

This blog post explains why logs and metrics are fundamentally different kinds of data, why counting log lines to produce a metric does not scale, and how the same number captured as a real metric is dramatically cheaper and faster. It also shows a pragmatic workaround using Fluen Bit to expose metrics in log ingetion step for when you cannot instrumentalize metrics into the application.

## Understanding the Data Before the Infrastructure

Over the past five years, I have worked on optimizing large-scale OpenSearch deployments running on Kubernetes, facing several challenges in maintaining performance as data ingestion volumes grew. One of the main challenges was keeping query latency low while handling an increasingly large volume of logs. At some point, I started exploring different performance optimization strategies to keep the cluster efficient as ingestion rates increased.

However, this led me to a more fundamental question: **how was the data actually being used?** In this particular case, logs were not simply being stored for troubleshooting. They were also queried to identify specific events and extract operational insights. This made query latency particularly important. As ingestion volumes continued to grow, maintaining this performance also became increasingly expensive.

That experience led me to an important realization: optimizing infrastructure is not just about scaling resources or tuning configurations. It is equally important to understand the nature of the data, how it is consumed, and the requirements of each use case. There is no silve bullet solution. Different types of data and access patterns require different approaches, architectures, and specific and optmized tools.

I decided to write this article to share this perspective and explore why understanding data usage is just as important as choosing the right technology to process and store it.

## How the Log Store Becomes an Accidental Metrics Database

One of the most common and most expensive mistakes in observability is quietly treating a log store as a metrics database. It usually starts innocently. Someone needs a number such as _"how many payments failed in the last hour?"_, the logs are right there, so they write a query that counts matching log lines and pins it to a dashboard, and it works.

Then the dashboard gets slow. The log cluster gets hot. The query that counts "errors per minute" starts timing out at exactly the moment you need it most, during an incident. The root cause is usually not a bad query or an undersized cluster. It is a category error: logs were asked to do a metric's job.

The rest of this post walks three things, in order: why logs and metrics are different kinds of data in the first place, how to capture the number the right way, and a workaround for the real world, when the application is out of your reach and you still need that number.

## Logs and Metrics Are Different Shapes of Data

Before blaming the query, it helps to see that logs and metrics are not two flavors of the same thing. The shape of the data underneath each one is different, and that is what the whole argument rests on.

A log is a discrete record of something that happened, meant to be read and understood by a human (or AI agent). It is rich, high-cardinality, and textual:

```log
2026-02-14T10:32:11Z level=error service=payments txn_id=8f3c user_id=22190
  msg="payment authorization failed" provider=acme code=INSUFFICIENT_FUNDS latency_ms=812
```

The value of a log is in its detail and context. When something breaks, a log tells you what happened, to whom, where, and often why. Logs answer: "walk me through this specific event."

A metric is a numeric measurement sampled over time. It is small, structured, and aggregatable by design:

```prometheus
payment_failures_total{provider="acme", code="INSUFFICIENT_FUNDS"} 48213
```

A metric does not describe one payment. It counts all of them. Its whole purpose is to be aggregated, rated, and summarized cheaply across huge volumes. Metrics answer: "how many, how fast, how much, right now and over time."

| Signal | What it is | Primary question | Natural shape |
| --- | --- | --- | --- |
| Logs | Discrete event records | "What exactly happened here?" | High-cardinality text |
| Metrics | Numeric samples over time | "How many / how fast / how much?" | Small numeric time series |

The moment you ask a log store to answer the metric question, you are forcing one data shape to behave like the other, and that is where the cost comes from.

## Why Logs Make Bad Metrics

OpenSearch is really good at what it is designed for: full-text search over an inverted index. Give it millions of log lines and ask "show me every error from `payments` mentioning `acme` yesterday", and it will answer fast, because the inverted index maps terms to the documents that contain them. That is a search workload, and it is the right tool.

The problem is what happens when you ask it to behave like a metrics engine. Consider the number we wanted earlier, failed payments per minute. As a log query it looks like this:

```{code-block} json
:caption: GET my-app-logs-index-*/_search
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

This works. But look at what the cluster has to do to produce one small time series:

**Data not indexed**: The number was never stored, it is computed on every read. There is no `failures_per_minute` value indexed anywhere. OpenSearch has to scan matching documents and build the count at query time, every single time the dashboard refreshes. The data you want was never indexed; only the raw events were.

**High scan volume cost**: It must touch enormous volumes to produce a tiny answer. To return 1,440 numbers (one per minute for a day), it filters and buckets potentially millions of fat text documents. The cost of the answer is proportional to the raw log volume, not to the size of the result.

**Cardinality and retention struggles**: It fights cardinality and retention. Want failures broken down by provider and error code over 90 days? Now the aggregation fans out across even more documents, and you are forced to retain verbose logs purely to keep a counter alive, long after the logs' diagnostic value has expired.

**Competes with primary workload**: It competes with the real workload. These heavy aggregations run on the same hot nodes handling ingestion and incident-time searches. The "metric" dashboard becomes a source of load that slows down the logging the cluster actually exists to serve.

OpenSearch can do this. It has date histograms, aggregations, even dashboards. The tooling exists. But this is not what the tool is optimized for. A log line primarily exists to describe an event so a human can understand what is happening. Deriving a long-lived counter from term matches is a query-time reconstruction of data that was never stored as a measurement, and that is not sustainable as volume and retention grow.

## The Same Number, Done Right: A Counter in the Application

If logs are the wrong shape for this job, the fix is to capture the number in the right shape from the start. Now capture the exact same information as a real metric. Instead of logging a line and counting it later, you instrument the application to increment a counter the moment a payment fails, and expose it to Prometheus:

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

The application exposes this on a `/metrics` endpoint, Prometheus scrapes it every 15 seconds, and now the number is the stored data: a monotonically increasing counter per label combination. Because a counter only ever goes up, `rate()` turns that running total into failures per second over any window you want (`[5m]`, `[1h]`), grouped by any label, and it even handles counter resets from deploys. Getting "failures per minute" is now a trivial, instant query:

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

The same insight ("failures are spiking") costs OpenSearch a full-volume scan and costs Prometheus almost nothing, because one tool reconstructs the number and the other simply reads it.

## Workaround: Extract Metrics From Logs When You Can't Touch the Code

The counter in the application is the right answer. But sometimes you simply cannot touch the source code. Maybe it is a legacy service nobody wants to rebuild, a closed-source component, or a third-party app that only emits logs and will never expose a `/metrics` endpoint. In those cases you still need the number, and instrumenting the code is off the table.

There is a middle-ground workaround here, and it is not "count log lines in OpenSearch". The idea is to turn the event into a metric at ingestion time, inside the log pipeline itself, before the log ever reaches the storage. Your log shipper already sees every single line as it flows through. So instead of storing fat logs and reconstructing the count later, you let the shipper match the line that denotes the event and increment a real counter right there. The log still goes to OpenSearch for investigation, and a proper metric is emitted in parallel.

Fluent Bit does this with the [log_to_metrics](https://docs.fluentbit.io/manual/data-pipeline/filters/log_to_metrics) filter. It watches the stream, matches the lines that represent the event (via regex), and emits a Prometheus metric that you expose through the [prometheus_exporter](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-exporter) output. Back to our failed payments, the config looks like this:

```{code-block} yaml
:caption: fluent-bit.yaml

service:
  flush: 1
  log_level: info

pipeline:
  inputs:
    - name: tail
      path: /var/log/payments/*.log
      tag: payments.log

  filters:
    # emit a counter every time a line denotes a failed payment
    - name: log_to_metrics
      match: payments.log
      tag: payment_metrics
      metric_mode: counter
      metric_name: payment_failures_total
      metric_description: "Total number of failed payment authorizations"
      # only the lines that actually represent the event
      regex: 'msg "payment authorization failed"'
      # turn log fields into metric labels, same breakdown you wanted
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

Prometheus scrapes the exporter and you get the exact same counter you would have instrumented in the code, without touching the code:

```{code-block} shell
:caption: $ curl -s http://127.0.0.1:9999/metrics

# HELP log_metric_counter_payment_failures_total Total number of failed payment authorizations
# TYPE log_metric_counter_payment_failures_total counter
log_metric_counter_payment_failures_total{provider="acme",code="INSUFFICIENT_FUNDS"} 48213
```

Notice the difference from the OpenSearch aggregation. The number is computed once, as the log passes through, not reconstructed on every dashboard refresh. OpenSearch keeps the raw logs for when you need to investigate a specific event, and the metric lives where metrics belong, cheap to query and cheap to retain.

I want to be clear about what this is: a workaround, not the ideal. You are still parsing text to decide what counts, so a change in the log format can silently break the counter, and you depend on the event being logged in the first place. If you can instrument the application, do that. The in-code counter encodes business meaning that a regex on a log line is only approximating. But when the source is out of reach, extracting the metric at ingestion is far better than hammering your log store with query-time aggregations.

Notice that even in the workaround, OpenSearch keeps doing what it is good at. The logs still land there for investigation, and the metric goes somewhere else, which is the principle worth zooming out on now.

## Conclusion: Right Tool for Right Signal

None of this means OpenSearch is the wrong choice. For logs, it is a great tool. The inverted index makes event search and investigation fast. The mistake is using it for a signal it was not built to carry.

Each signal has engines designed around its data shape:

| Signal | Purpose-built tools | Why they fit |
| --- | --- | --- |
| Logs | OpenSearch / Elasticsearch, Loki | Inverted index / label index tuned for text search over events |
| Metrics | Prometheus, Mimir, VictoriaMetrics | Time-series storage with cheap aggregation and rate math |

You can force everything into one system. But a single tool stretched across signals it was not built for ends up unoptimized: slow dashboards, bloated retention, and a pile of query-time hacks to approximate what a purpose-built engine does natively. There is no silver bullet in a telemetry architecture. The best architecture is the one where each signal lands in the tool shaped for it.

And part of getting there is organizational, not just technical. Good observability is a partnership: the application team instruments the code, because only the people who understand the business logic know which events matter and which labels make a metric meaningful, while the infrastructure team provides the pipes that ingest, store, and expose each signal where it belongs. A `payment_failures_total{code=...}` counter encodes business meaning that infrastructure cannot invent from the outside.

## References

- <https://opensearch.org/docs/latest/aggregations/>
- <https://prometheus.io/docs/concepts/metric_types/>
- <https://prometheus.io/docs/prometheus/latest/querying/functions/#rate>
- <https://docs.fluentbit.io/manual/pipeline/filters/log_to_metrics>

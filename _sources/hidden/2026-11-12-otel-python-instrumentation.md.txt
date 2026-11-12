---
tags: opentelemetry, python, prometheus
date: "2026-11-12"
category: Observability
author: Carlos Neto
title: "Instrumenting a Python Application with OpenTelemetry"
description: "A step-by-step OpenTelemetry example in Python: instrument a payment service with the API, turn on the SDK with environment variables, route metrics through the Collector to Prometheus, then switch to Datadog without touching the code."
myst:
  html_meta:
    description: "A step-by-step OpenTelemetry example in Python: instrument a payment service with the API, turn on the SDK with environment variables, route metrics through the Collector to Prometheus, then switch to Datadog without touching the code."
og:title: "Instrumenting a Python Application with OpenTelemetry"
og:description: "A step-by-step OpenTelemetry example in Python: instrument a payment service with the API, turn on the SDK with environment variables, route metrics through the Collector to Prometheus, then switch to Datadog without touching the code."
---

*__Blog Post Publish Date:__ 2026/11/12*

---

# Instrumenting a Python Application with OpenTelemetry

This blog post builds a small Python service instrumented with OpenTelemetry, one piece at a time. It starts with the API only, turns on the SDK without changing the code, routes the metrics through the OpenTelemetry Collector to Prometheus, and finally switches to Datadog by changing only the Collector configuration.

It's the hands-on companion to [OpenTelemetry: A Framework for Decoupling Your Observability](/blog/2026/2026-10-29-otel-foundation.md), which explains what OpenTelemetry is and when it's worth using. If you're not sure you need it yet, start there.

## The Example

The example is a small payment service. We want to know how many payments it processes and how long each one takes. The application code is written once, in step 1, and never changes after that. Each step adds one OpenTelemetry piece around it:

| Step | Piece added | What it does |
| --- | --- | --- |
| 1 | API | Describes what to measure, inside the code |
| 2 | SDK | Processes the measurements and sends them over OTLP |
| 3 | Collector | Receives OTLP and exports it to Prometheus |
| Payoff | Collector config | Switches the backend to Datadog |

## Step 1: Instrument the Code With the API Only

`app.py` holds the business logic and the instrumentation. It imports only the OpenTelemetry API: no SDK, no exporter, no vendor library.

```python
import random
import time
from time import perf_counter

# it is the API library
from opentelemetry import metrics


# Get a meter from the OpenTelemetry API.
meter = metrics.get_meter("payment-api")

# Create instruments.
payments_processed = meter.create_counter(
    "payments_processed",
    description="Number of processed payments"
)

payment_duration = meter.create_histogram(
    "payment_processing_duration",
    unit="s",
    description="Payment processing duration",
    # bucket boundaries in seconds; the defaults are sized for milliseconds
    explicit_bucket_boundaries_advisory=[0.1, 0.2, 0.3, 0.4, 0.5, 1.0],
)


def process_payment():
    start = perf_counter()

    # Simulate payment processing.
    time.sleep(random.uniform(0.1, 0.5))
    
    if random.random() > 0.1:
        status = "success" 
    else:
        status = "failure"

    # Record the number of processed payments.
    payments_processed.add(1, {"status": status})

    # Record how long the operation took.
    payment_duration.record(
        perf_counter() - start,
        {"status": status}
    )

    print(f"Payment processed: {status}")


if __name__ == "__main__":
    while True:
        process_payment()
```

In short:

1. `metrics.get_meter()` returns a **meter**, the object that creates instruments.
2. The code creates a **counter**, for a total that only goes up (processed payments), and a **histogram**, for a distribution of values (processing durations).
3. Each payment records one measurement in each instrument, with a `status` attribute.

The `explicit_bucket_boundaries_advisory` argument matters. A histogram counts values in buckets, and the SDK's default boundaries are `0, 5, 10, 25, 50, 75, 100, …`, sized for milliseconds. Our durations are between 0.1 and 0.5 seconds, so with the defaults every payment would land in the first bucket (0 to 5) and percentiles such as p95 would be useless. The advisory boundaries are part of the API, so `app.py` still doesn't depend on the SDK.

Install the API and run it:

```bash
pip install opentelemetry-api
python app.py
```

It works, and nothing is exported anywhere. That's on purpose: without an SDK, every API call is a no-op. A library author can instrument their code with the API, and it costs nothing for users who don't use OpenTelemetry. This is the first idea to keep: **the API describes what to measure, not where it goes.**

## Step 2: Turn On the SDK Without Touching the Code

Now we want the data to leave the process. That's the SDK's job. The simplest way to add it is the `opentelemetry-instrument` launcher, which loads the SDK before your code runs and configures it from environment variables:

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp

export OTEL_SERVICE_NAME=payment-api
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_TRACES_EXPORTER=none
export OTEL_LOGS_EXPORTER=none
export OTEL_METRICS_EXPORTER=otlp

opentelemetry-instrument python app.py
```

`app.py` is exactly the same file as in step 1. The [environment variables](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/) tell the SDK the service name, a semantic convention that backends use to identify the service, and to send metrics over OTLP to `localhost:4317`. In Python, the `otlp` exporter uses gRPC, which listens on port 4317 by default. OTLP over HTTP uses port 4318, and it's the default in some other languages.

If the application used Flask or `requests`, the [zero-code instrumentation](https://opentelemetry.io/docs/zero-code/python/) would also record HTTP metrics and traces for them, with no code changes. For that, first run `opentelemetry-bootstrap -a install`, which installs the instrumentation packages for the libraries it finds in your environment.

If you prefer to configure the SDK in code, the same setup looks like this. It lives in its own file, separate from `app.py`:

```{code-block} python
:caption: telemetry.py

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Who is sending the data (semantic convention: service.name).
resource = Resource.create({"service.name": "payment-api"})

# Where and how to send it: OTLP over gRPC, pushed periodically.
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)
)

# Register the SDK implementation behind the API.
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
```

In this case, `telemetry.py` has to be imported before the application runs, so you need a small entry point. `app.py` still doesn't change:

```{code-block} python
:caption: main.py

import telemetry  # registers the SDK before any measurement
from app import process_payment

while True:
    process_payment()
```

Run it with `python main.py`. The `opentelemetry-instrument` approach avoids this extra file, which is one reason I prefer it.

Either way, the application now speaks **OTLP**. It doesn't know or care whether Prometheus, Datadog, or anything else is at the end of the line. Something has to receive that OTLP, though, and that's the Collector's job.

## Step 3: Route the Data With the Collector

The **OpenTelemetry Collector** is a service that receives telemetry, optionally processes it, and exports it to one or more backends. Its configuration is a pipeline with three parts, the same ones in the diagram:

- **receivers**: how data comes in, here OTLP on port 4317.
- **processors**: what to do with it on the way, here batching.
- **exporters**: where it goes, here a Prometheus endpoint and the console.

```{code-block} yaml
:caption: collector.yaml

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch: {}

exporters:
  # expose the metrics for Prometheus to scrape
  prometheus:
    endpoint: 0.0.0.0:8889
  # also print a summary to the Collector's console
  debug:
    verbosity: basic

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, debug]
```

Run the Collector with Docker. The `contrib` distribution includes vendor exporters such as Prometheus and Datadog:

```bash
docker run --rm \
  -p 4317:4317 -p 8889:8889 \
  -v "$(pwd)/collector.yaml:/etc/otelcol-contrib/config.yaml" \
  otel/opentelemetry-collector-contrib:0.114.0
```

With the application from step 2 running, the metrics show up in the Prometheus format, ready for a Prometheus server to scrape. The output looks like this, trimmed (your numbers will differ):

```bash
$ curl -s http://localhost:8889/metrics | grep payments_processed

payments_processed_total{job="payment-api",status="success"} 412
payments_processed_total{job="payment-api",status="failure"} 47
```

The counter gets the `_total` suffix that Prometheus expects for counters, and `service.name` became the `job` label. Depending on the Collector version, you'll also see extra labels such as `instance` and `otel_scope_name`, and a `target_info` metric with the resource attributes. The histogram appears as `payment_processing_duration_seconds_bucket`, with one series per bucket boundary from step 1.

## The Payoff: Switching Backends

Now the company decides to send metrics to Datadog. With OpenTelemetry, you change one block in `collector.yaml`:

```{code-block} yaml
:caption: collector.yaml (exporters changed)

exporters:
  datadog:
    api:
      key: ${env:DD_API_KEY}

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]
```

Then restart the Collector, passing the API key as an environment variable:

```bash
docker run --rm \
  -p 4317:4317 \
  -e DD_API_KEY=<your-api-key> \
  -v "$(pwd)/collector.yaml:/etc/otelcol-contrib/config.yaml" \
  otel/opentelemetry-collector-contrib:0.114.0
```

If your Datadog account isn't on the default US site, also set `site` in the exporter, for example `site: datadoghq.eu`.

`app.py` didn't change. The SDK configuration didn't change. No service was redeployed. With fifty services, that's the difference between one configuration change and fifty pull requests. You can also list both exporters during a migration and send the same data to Prometheus and Datadog at the same time.

## Key Takeaways

- The application code depends only on the OpenTelemetry API. Without an SDK, API calls do nothing, so instrumented code is always safe to run.
- A **meter** creates instruments: a **counter** for totals that only go up, and a **histogram** for distributions such as durations.
- `opentelemetry-instrument` and `OTEL_*` environment variables turn on and configure the SDK without changing the code. A separate `telemetry.py` does the same in code.
- `service.name` identifies the service in the backends. Prometheus shows it as the `job` label.
- Set histogram bucket boundaries that match your unit. The defaults are sized for milliseconds.
- The Collector pipeline has receivers, processors, and exporters. Switching from Prometheus to Datadog means changing the exporters.
- During a migration, the Collector can export the same data to both backends at once.

## References

- [Python getting started (OpenTelemetry)](https://opentelemetry.io/docs/languages/python/getting-started/)
- [Python zero-code instrumentation (OpenTelemetry)](https://opentelemetry.io/docs/zero-code/python/)
- [SDK environment variables (OpenTelemetry)](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/)
- [Collector configuration (OpenTelemetry)](https://opentelemetry.io/docs/collector/configuration/)
- [OpenTelemetry Collector Contrib (GitHub)](https://github.com/open-telemetry/opentelemetry-collector-contrib)
- [OpenTelemetry Python documentation (Read the Docs)](https://opentelemetry-python.readthedocs.io/)
- [OpenTelemetry in Datadog (Datadog)](https://docs.datadoghq.com/opentelemetry/)

*I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Instrumenting a Python Application with OpenTelemetry",
      "description": "A step-by-step OpenTelemetry example in Python: instrument a payment service with the API, turn on the SDK with environment variables, route metrics through the Collector to Prometheus, then switch to Datadog without touching the code.",
      "datePublished": "2026-11-12",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-11-12-otel-python-instrumentation/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-11-12-otel-python-instrumentation/",
      "image": "https://carlosneto.dev/_static/2026/2026-10-29/opentelemetry-pieces.svg",
      "keywords": ["OpenTelemetry", "Python", "OpenTelemetry Collector", "OTLP", "Prometheus", "Datadog"],
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
        {"@type": "ListItem", "position": 3, "name": "Instrumenting a Python Application with OpenTelemetry"}
      ]
    }
  ]
}
</script>
```

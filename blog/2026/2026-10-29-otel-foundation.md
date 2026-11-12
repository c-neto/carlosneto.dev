---
tags: opentelemetry
date: "2026-10-29"
category: Observability
author: Carlos Neto
title: "OpenTelemetry: A Framework for Decoupling Your Observability"
description: "What OpenTelemetry actually is, why separating the API from the SDK prevents vendor lock-in, and a Python example that records the same metrics and sends them to Prometheus or Datadog by changing only the SDK setup."
myst:
  html_meta:
    description: "What OpenTelemetry actually is, why separating the API from the SDK prevents vendor lock-in, and a Python example that records the same metrics and sends them to Prometheus or Datadog by changing only the SDK setup."
og:title: "OpenTelemetry: A Framework for Decoupling Your Observability"
og:description: "What OpenTelemetry actually is, why separating the API from the SDK prevents vendor lock-in, and a Python example that records the same metrics and sends them to Prometheus or Datadog by changing only the SDK setup."
---

*__Blog Post Publish Date:__ 2026/10/29*

---

# OpenTelemetry: A Framework for Decoupling Your Observability

This blog post explains what OpenTelemetry is and why its separation between API and SDK matters. It then walks through a Python application that records metrics once, through the OpenTelemetry API, and sends them to either Prometheus or Datadog by changing only the SDK configuration.

## What OpenTelemetry Actually Is

When I started studying OpenTelemetry, I struggled to understand what it was, what problem it solved, and how it related to tools such as Prometheus. This post walks through the reasoning that finally made it click for me.

The [official definition](https://opentelemetry.io/docs/what-is-opentelemetry/) says that **OpenTelemetry** is _"an open-source, vendor-neutral observability framework"_ for generating, collecting, and exporting telemetry data. It's accurate, but I found it abstract. I kept asking: _How do I actually use it? Do I install it in my application? Do I run it as a service? Is it something like Prometheus?_

The answer is that OpenTelemetry is neither just a library nor a standalone service like Prometheus or Logstash. It's a set of pieces:

- **API specifications**: the interfaces your code calls to create spans, metrics, and logs.
- **SDKs**: the implementations of those APIs for each language, which process and export the data.
- **The OpenTelemetry Collector**: an optional service that receives, processes, and forwards telemetry.

OpenTelemetry defines the standard. Tools such as Prometheus, Datadog, or Fluent Bit are backends and transports: interchangeable places to store, query, or move the data your application produces.

OpenTelemetry is complex. You instrument the application to produce traces, metrics, and logs, configure how that data is collected, and choose where to store and analyze it. That complexity pays for itself in modern distributed systems and microservice architectures, where you need the same telemetry from many services in many languages.

Then the obvious questions come up: _Which library should I use? Which collector should I run? Which database should store the data?_ This is where OpenTelemetry shines: __it strictly separates definitions from implementations.__ You pick the tools that fit your infrastructure without coupling the application to a vendor.

Your code calls the OpenTelemetry API, and it doesn't need to know where the telemetry goes. If you replace the collection agent or the backend later, you don't rewrite application code. You change the SDK configuration, or the destination in the Collector. That is what makes OpenTelemetry vendor-neutral and prevents vendor lock-in.

## Instrumenting a Python Application

Imagine a simple payment application. We want to measure how many payments it processes and how long each one takes. To show the vendor-neutral design, the example defines the metrics once with the API and sets up two different SDK configurations: one for Prometheus and one for Datadog.

The point is that the business logic contains no Prometheus or Datadog code. Switching from Prometheus to Datadog means changing only the SDK setup, such as the exporter, endpoint, credentials, or protocol.

### The Metric API

`app.py` holds the instrumentation. Notice that it imports only the OpenTelemetry API, with no SDK classes, exporters, or backend libraries:

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
    description="Payment processing duration"
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
```

Here is what happens:

1. `metrics.get_meter()` returns a **meter**, the object that creates instruments such as counters and histograms.
2. The code creates two instruments. A **counter** records a value that only goes up, such as the total number of processed payments. A **histogram** records a distribution of values, such as payment durations.
3. Each processed payment records one measurement in each instrument, with a `status` attribute.

This code only talks to the OpenTelemetry API. It doesn't know how the metrics are collected, processed, or exported, or whether they end up in Prometheus, Datadog, or another backend. Until an SDK is registered, the API calls simply do nothing, which also makes the code safe to run without any telemetry setup.

### The SDK Setup: Prometheus or Datadog

`telemetry.py` configures the OpenTelemetry SDK. Unlike `app.py`, it imports SDK classes and decides how the data is collected and exported. Here are two versions of it.

__Prometheus:__ this `telemetry.py` exposes the metrics in the Prometheus format:

```python
from prometheus_client import start_http_server

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader

# it is the SDK library
from opentelemetry.sdk.metrics import MeterProvider


# Expose the Prometheus metrics endpoint.
start_http_server(port=9464)

# Configure the Prometheus Metric Reader.
reader = PrometheusMetricReader()

# Configure the SDK.
provider = MeterProvider(
    metric_readers=[reader]
)

# Register the SDK implementation.
metrics.set_meter_provider(provider)
```

The [Prometheus exporter](https://opentelemetry-python.readthedocs.io/en/latest/exporter/prometheus/prometheus.html) serves the metrics at `http://localhost:9464/metrics`, and Prometheus scrapes that endpoint periodically. In the Prometheus format, the counter appears as `payments_processed_total`, following the Prometheus naming convention for counters.

__Datadog:__ now suppose the same metrics must go to Datadog. `app.py` doesn't change at all. Only `telemetry.py` does. This version uses the [OTLP exporter](https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html) to push the metrics to a Datadog Agent:

```python
from opentelemetry import metrics

# it is SDK library
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)


# Configure the OTLP exporter.
exporter = OTLPMetricExporter(
    endpoint="http://localhost:4317",
    insecure=True,
)

# Configure the metric reader.
reader = PeriodicExportingMetricReader(exporter)

# Configure the SDK.
provider = MeterProvider(
    metric_readers=[reader]
)

# Register the SDK implementation.
metrics.set_meter_provider(provider)

```

**OTLP** (OpenTelemetry Protocol) is the native protocol for sending telemetry between OpenTelemetry components. The Datadog Agent can receive OTLP on port 4317 once its [OTLP ingestion](https://docs.datadoghq.com/opentelemetry/) is enabled, and it forwards the metrics to Datadog.

The two setups also use different models. Prometheus pulls: it scrapes the application's endpoint. The OTLP exporter pushes: the `PeriodicExportingMetricReader` sends the metrics to the agent at a fixed interval.

### Wiring It Together

The application imports `telemetry.py` once at startup to register the SDK, then runs the business logic:

```python
# main.py
import telemetry  # registers the SDK (Prometheus or Datadog)
from app import process_payment

while True:
    process_payment()
```

Switching backends means switching the `telemetry.py` file, or its configuration. `app.py` stays the same.

## Why the Separation Matters

The API/SDK split is the idea that made OpenTelemetry click for me. The application declares what it measures, and the platform decides where the data goes. That lets the application team instrument the code without waiting on backend decisions, and lets the platform team change backends without touching every service.

It also forces you to emit metrics as metrics, instead of logging lines and counting them later in the log store. I explain why that matters in [Stop Extracting Metrics from OpenSearch Logs](/blog/2026/2026-11-03-stop-extracting-metrics-from-opensearch-logs.md). And if you're collecting the logs side of the picture on Kubernetes, see [Kubernetes Logs Simplified](/blog/2025/2025-06-22-kubernetes-logs-simplified.md).

## Key Takeaways

- OpenTelemetry is a standard, not a backend: API specifications, language SDKs, and an optional Collector.
- Application code calls only the API. The SDK, configured separately, decides how telemetry is processed and where it goes.
- Changing from Prometheus to Datadog changes only the SDK setup (`telemetry.py`), not the instrumented code (`app.py`).
- A meter creates instruments. A counter records totals that only go up, and a histogram records distributions such as durations.
- The Prometheus exporter exposes an endpoint for Prometheus to scrape (pull). The OTLP exporter sends metrics to an agent or Collector (push).
- Without a registered SDK, API calls do nothing, so instrumented code runs safely with no telemetry setup.

## References

- [What is OpenTelemetry? (OpenTelemetry)](https://opentelemetry.io/docs/what-is-opentelemetry/)
- [OpenTelemetry documentation (OpenTelemetry)](https://opentelemetry.io/docs/)
- [OpenTelemetry Python documentation (Read the Docs)](https://opentelemetry-python.readthedocs.io/)
- [Metrics SDK (OpenTelemetry Python)](https://opentelemetry-python.readthedocs.io/en/latest/sdk/metrics.html)
- [Prometheus exporter (OpenTelemetry Python)](https://opentelemetry-python.readthedocs.io/en/latest/exporter/prometheus/prometheus.html)
- [OTLP exporter (OpenTelemetry Python)](https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html)
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
      "headline": "OpenTelemetry: A Framework for Decoupling Your Observability",
      "description": "What OpenTelemetry actually is, why separating the API from the SDK prevents vendor lock-in, and a Python example that records the same metrics and sends them to Prometheus or Datadog by changing only the SDK setup.",
      "datePublished": "2026-10-29",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-10-29-otel-foundation/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-10-29-otel-foundation/",
      "keywords": ["OpenTelemetry", "observability", "Python", "Prometheus", "Datadog", "OTLP"],
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

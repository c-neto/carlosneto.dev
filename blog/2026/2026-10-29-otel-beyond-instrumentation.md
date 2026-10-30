---
tags: opentelemetry, observability
date: "2026-10-29"
category: observability
---

*__Blog Post Publish Date:__ 2026/10/29*

---

# OpenTelemetry: A Framework to Decoupling Your Observability

This blog post explains the foundation of OpenTelemetry and walks through a practical example of instrumenting a Python application. It demonstrates OpenTelemetry's single API definition paired with multiple SDK implementations for Prometheus and Datadog.

## Demystifying OpenTelemetry

While studying OpenTelemetry, I found it difficult to fully understand what it actually was, what problem it solved, and how it differed from and related to tools like Prometheus. I decided to create this blog post to share this challenge, as well as the line of reasoning I followed to truly understand what OpenTelemetry is.

The official definition of OpenTelemetry is: *"An open-source, vendor-neutral observability framework designed to standardize how software generates, collects, and exports telemetry data."* As accurate as this definition is, I found it rather abstract. I kept asking myself: *How do I actually use this framework? Do I install it in my application? Do I run it as a service? Is it something like Prometheus?*

The answer is that OpenTelemetry is neither just a library you add to your code nor a standalone service like Prometheus or Logstash. OpenTelemetry encompassing API specifications, instrumentation SDKs, and data collection infrastructure (the OpenTelemetry Collector). OpenTelemetry defines the universal standard, while tools like Prometheus or Fluent Bit are simply execution backends, interchangeable mechanisms used to store, query, or transport the data your framework generates.

Using OpenTelemetry involves instrumenting your application to generate telemetry data (traces, metrics, and logs), configuring components to collect that data, and choosing where to store and analyze it. This can introduce some complexity, especially in modern distributed systems and microservice architectures.

Naturally, questions arise: *Which library should you use? Which collector should you run? Which database should store your telemetry?* This is where OpenTelemetry really shines: **the strict separation between definitions and implementations.** You can choose the tools that best fit your infrastructure without coupling your application to a specific vendor or backend.

When instrumenting your application, you write code against the OpenTelemetry API (the specification). Your application does not need to know where the telemetry data is going. If you decide to replace your collection agent or backend later, you do not need to rewrite application code. You simply update the SDK configuration or the destination defined in the OpenTelemetry Collector. This approach ensures vendor neutrality and prevents vendor lock-in.

## A Practical Python Example

Imagine we have a simple payment application. We want to measure the total number of processed payments, and how long each payment takes to process.

To demonstrate OpenTelemetry's vendor-neutral metric implementation, we will define a metric API once and set up two different backend SDK implementations: Prometheus and Datadog.

The key takeaway is that we aren't writing code specific to Prometheus or Datadog inside our business logic. We instrument the Python application using the OpenTelemetry API. If we decide to switch from Prometheus to Datadog, we don't touch the application domain code—we only update the SDK configuration parameters (such as the exporter endpoint, credentials, or protocol) to send metrics to Datadog.

### 1. The API: Instrumenting the Application

Let's start with `app.py`.

This file contains the application instrumentation. Notice that it imports only the OpenTelemetry API. It does not import SDK classes, exporters, or backend-specific libraries.

```python
import random
import time
from time import perf_counter

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

    status = "success" if random.random() > 0.1 else "failure"

    # Record the number of processed payments.
    payments_processed.add(1, {"status": status})

    # Record how long the operation took.
    payment_duration.record(
        perf_counter() - start,
        {"status": status}
    )

    print(f"Payment processed: {status}")

```

Let's break down what happens here:

1. We call `metrics.get_meter()` to obtain a `Meter`. The `Meter` is responsible for creating instruments such as Counters and Histograms.
2. We create two instruments: **Counter:** Records cumulative values, such as the total number of processed payments; and **Histogram:** Records distributions of values, such as payment processing durations.
3. We use these instruments to record measurements whenever a payment is processed.

The crucial detail is that this code only interacts with the OpenTelemetry API. It does not know or care how metrics are collected, processed, or exported, nor whether they end up in Prometheus, Datadog, or another observability backend.

That is the power of this architectural separation.

### 2. The SDK: Choosing the Implementation

Now let's look at `telemetry.py`.

This file configures the OpenTelemetry SDK. Unlike `app.py`, it imports SDK classes and defines how telemetry data will be collected and exported.

Let's compare two different backend configurations: Prometheus and Datadog.

#### Option A: Prometheus

First, let's configure the SDK to expose metrics in Prometheus format.

Install the required packages:

```bash
pip install opentelemetry-api \
            opentelemetry-sdk \
            opentelemetry-exporter-prometheus \
            prometheus-client

```

Configure `telemetry.py`:

```python
from prometheus_client import start_http_server

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
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

In this setup, `PrometheusMetricReader` exposes an HTTP endpoint containing the application's metrics. Prometheus periodically scrapes this endpoint to collect data.

The endpoint is available at:
`http://localhost:9464/metrics`

#### Option B: Datadog

Now suppose we want to send those exact same metrics to Datadog instead.

We do not modify `app.py` at all. We only update the SDK setup in `telemetry.py`.

For this example, we'll use the OpenTelemetry Protocol (OTLP) exporter to push metrics to a Datadog Agent.

Install the required packages:

```bash
pip install opentelemetry-api \
            opentelemetry-sdk \
            opentelemetry-exporter-otlp-proto-grpc

```

Configure `telemetry.py`:

```python
from opentelemetry import metrics
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

Here, `OTLPMetricExporter` sends telemetry using OpenTelemetry Protocol (OTLP). The Datadog Agent receives these OTLP metrics and forwards them to Datadog.

Unlike the pull-based Prometheus integration, this approach uses a push-based model where the application periodically pushes metrics out to the collector agent.

## References

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [OpenTelemetry Python Documentation](https://opentelemetry-python.readthedocs.io/)
- [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/en/latest/sdk/metrics.html)
- [OpenTelemetry Python Prometheus Exporter](https://opentelemetry-python.readthedocs.io/en/latest/exporter/prometheus/prometheus.html)
- [OpenTelemetry OTLP Exporter](https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html)
- [Datadog OTLP Ingestion](https://docs.datadoghq.com/opentelemetry/)

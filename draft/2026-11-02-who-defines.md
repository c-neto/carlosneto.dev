---
tags: observability, opentelemetry, cncf, metrics, logs, traces
date: "2026-11-02"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2026/11/02*

---

# Who Defines Observability?

If you work with software development or cloud infrastructure, you have probably heard the buzzword **observability**. Beyond the buzzword, do you know exactly which signals make a system observable, and who decided things should work this way?

In this article, I will demystify the pillars of modern telemetry and show how the industry reached a consensus on monitoring distributed applications. The focus here is not on instrumenting code. It is on understanding where the standards come from and who maintains them.

## The Three Traditional Pillars (and the New Addition)

Observability is the ability to infer a system's internal state from its external outputs. These outputs are called **telemetry signals**. Before discussing who defines the standards, let's get the terminology straight.

### 1. Metrics: The System Thermometer

Numeric values aggregated over time, such as CPU usage, requests per second, or average latency. They are used for alerts and dashboards, and quickly answer the question: *"Is the system healthy or having problems?"*

### 2. Logs: The System's Logbook

Records of discrete events stamped with a date and time (*timestamps*). They help with point-in-time diagnostics and answer the question: *"What exactly happened at this specific second?"*

### 3. Traces: The Journey Map

Distributed tracing follows the path a request takes through multiple microservices and databases. It helps identify performance bottlenecks in complex architectures and answers the question: *"Where is the request spending too much time?"*

> **The 4th Pillar:** **Continuous profiling** is gaining ground as the fourth official signal. It analyzes resource consumption (memory and CPU) at the code or function level in real time, without affecting production.

## But Who Defines These Standards?

This is the part that intrigues me most: no single organization is responsible for defining observability. Unlike formal web standards (such as HTML, defined by the W3C), observability evolved organically through software engineering practice. Books, blog posts, and open source projects together shaped the consensus we use today.

Below are the origins and milestones behind these ideas, so you can check for yourself where the standards come from.

### The Open Source Community (2016-2017)

The conceptual foundation for the three pillars came from the community, not a formal committee. Two milestones helped popularize the shift from "traditional monitoring" to "observability" in microservices:

- [Distributed Systems Observability (O'Reilly report: Cindy Sridharan)](https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/): Published in late 2017 by Cindy Sridharan, then an engineer at Apple/Uber, this e-book popularized the classic definition and distinction between the three pillars (*Logs, Metrics, Traces*) in modern software engineering.
- [Charity Majors's blog post (Honeycomb.io, 2016)](https://charity.wtf/2016/05/31/monitoring-a-tech-debt-story/): one of the notable discussions in the ecosystem about the shift from traditional monitoring to observability in microservices.

### CNCF (Cloud Native Computing Foundation)

With the community pointing the way, neutral standardization became the responsibility of the CNCF, a foundation under the *Linux Foundation* that incubates, manages, and standardizes major open source projects for cloud computing.

- [CNCF Official Website](https://www.cncf.io/): the foundation behind cloud native projects.
- [CNCF Landscape: Observability Section](https://landscape.cncf.io/card-mode?category=observability-and-analysis): the CNCF's official map of neutral market tools maintained by the foundation, such as Prometheus, Jaeger, and OpenTelemetry.

### The OpenTelemetry Project (OTel)

If there is anything close to a formal specification for telemetry signals today, it is OpenTelemetry. Its working groups define and approve the structure of each signal.

- [Official OpenTelemetry Documentation](https://opentelemetry.io/): the CNCF's official portal with technical specifications, SDKs, APIs, and the OTLP protocol.
- [Official OTel Specification on GitHub](https://github.com/open-telemetry/opentelemetry-specification): the *open source* repository where working groups formally define and approve the structure of each telemetry signal (Traces, Metrics, Logs, and Profiles).

## Conclusion (Author Opinion)

After years of hearing "observability" talked about as if it were a product you could buy, what stands out to me is that nobody defined it from the top down. It grew out of practice. Engineers dealing with production problems wrote about it, and only later did it become a specification through the CNCF and OpenTelemetry.

I find that liberating. Understanding observability means learning why the community settled on these signals, not memorizing a committee's standard. If you want to go deeper, start with the references below and read the original sources. That is worth much more than any summary, including this one.

## References

- <https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/>
- <https://charity.wtf/2016/05/31/monitoring-a-tech-debt-story/>
- <https://www.cncf.io/>
- <https://landscape.cncf.io/card-mode?category=observability-and-analysis>
- <https://opentelemetry.io/>
- <https://github.com/open-telemetry/opentelemetry-specification>

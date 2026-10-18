---
tags: prometheus, blackbox, observability
date: ""
category: Log Analytics
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---

# Prometheus Blackbox Exporter: Monitoring From the Outside In

This blog post explains what blackbox monitoring is and where it fits next to the metrics you already collect. It walks through the Prometheus Blackbox Exporter, how to configure it, and the multi-target scrape pattern that makes it work. It also shows how to use the probe metrics to estimate the uptime of your services.

## Whitebox vs Blackbox: Two Ways to Look at a System

Most of the monitoring we set up is whitebox. We instrument the application, expose a `/metrics` endpoint, and collect internal counters: request rates, queue depth, garbage collection, connection pools. It tells you a lot about what is happening inside the process. It is the kind of monitoring Prometheus was built for.

But whitebox monitoring has a blind spot. It assumes the thing exposing the metrics is reachable and healthy enough to report. If the TLS certificate expired, if DNS is broken, if a load balancer in front of your app is dropping traffic, your internal metrics can look perfectly fine while real users stare at an error page.

Blackbox monitoring takes the opposite view. You do not look inside the system, you look at it from the outside, the same way a user would. You send a request and you check the answer. Did the HTTP call return 200? How long did it take? Is the certificate still valid? You do not care why it failed, only that, from the outside, it did.

Both approaches are useful, and they answer different questions. Whitebox tells you why something is slow. Blackbox tells you whether the user can reach it at all.

## The Prometheus Blackbox Exporter

The [Blackbox Exporter](https://github.com/prometheus/blackbox_exporter) is the official Prometheus component for this job. It probes endpoints over HTTP, HTTPS, DNS, TCP, ICMP, and gRPC, and it reports whether the probe succeeded and how long it took.

The idea is simple. You run the exporter somewhere, and Prometheus asks it to probe a target. The exporter does the probe, then returns the result as Prometheus metrics. The exporter itself holds no list of targets. Prometheus decides what to probe and passes the target in the scrape request. This detail matters, and I will come back to it.

What I like about it is how close it sits to the user. It is not a deep monitoring tool, and it is not trying to be. It answers the one question that matters most during an incident: _is the service actually up from the outside?_ For simple, user-facing checks, that is often all you need.

## Configuring the Exporter: Modules

The exporter is configured through a `blackbox.yml` file that defines **modules**. A module is a named probe recipe: which prober to use (http, tcp, dns, icmp, grpc) and the parameters for it.

```{code-block} yaml
:caption: blackbox.yml

modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      preferred_ip_protocol: "ip4"
      valid_status_codes: []  # defaults to 2xx

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp_ping:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"

  dns_lookup:
    prober: dns
    timeout: 5s
    dns:
      query_name: "carlosneto.dev"
      query_type: "A"
```

The `http_2xx` module is the one you will use most. By default it treats any 2xx response as a success. The others let you check that a TCP port accepts connections, that a host answers ICMP ping, or that a DNS query returns the expected record.

You can start the exporter with Docker to try it out:

```{code-block} bash
:caption: run the blackbox exporter

docker run --rm -p 9115:9115 \
  -v "$(pwd)/blackbox.yml:/etc/blackbox_exporter/config.yml" \
  prom/blackbox-exporter:latest
```

## Probing a Target by Hand

Before wiring Prometheus, it helps to understand the exporter's `/probe` endpoint. You call it with two query parameters: the `module` and the `target`.

```{code-block} bash
:caption: probe carlosneto.dev with the http_2xx module

curl 'http://localhost:9115/probe?module=http_2xx&target=https://carlosneto.dev'

# output expected (truncated):
#
# probe_success 1
# probe_duration_seconds 0.183
# probe_http_status_code 200
# probe_ssl_earliest_cert_expiry 1.7612...e+09
```

The most important metric here is `probe_success`. It is `1` when the probe succeeded and `0` when it failed. Everything else is extra context: `probe_duration_seconds` for latency, `probe_http_status_code` for the response code, and `probe_ssl_earliest_cert_expiry` for the certificate expiry date.

> <i class="fa-solid fa-circle-info"></i> Add `&debug=true` to the probe URL to get a plain-text page with the full probe logs and module config. It is the first thing I reach for when a probe fails and I do not understand why.

## Wiring Prometheus: The Multi-Target Pattern

Here is the part that confused me the first time. You do not point Prometheus at the exporter and list targets in a normal job. Instead, Prometheus scrapes the exporter, but the _target_ to probe is passed through relabeling. This is the multi-target exporter pattern.

```{code-block} yaml
:caption: prometheus.yml

scrape_configs:
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://carlosneto.dev
          - https://github.com
          - https://prometheus.io
    relabel_configs:
      # pass the target as the "target" query parameter to the exporter
      - source_labels: [__address__]
        target_label: __param_target
      # keep the probed URL as the "instance" label on the metrics
      - source_labels: [__param_target]
        target_label: instance
      # send the scrape to the exporter itself, not to the target
      - target_label: __address__
        replacement: 127.0.0.1:9115
```

Read the `relabel_configs` from top to bottom:

- __1__: the target from `static_configs` (`__address__`) becomes the `target` query parameter the exporter expects.
- __2__: that same value is stored in the `instance` label, so each metric is tagged with the URL it describes.
- __3__: the actual scrape address is rewritten to the exporter (`127.0.0.1:9115`), so Prometheus talks to the exporter and lets it do the probing.

Once this is running, every target in the list produces a `probe_success` series tagged with its URL. Adding a new endpoint to monitor is just one more line under `targets`.

## Estimating Uptime From probe_success

This is where the Blackbox Exporter earns its place for me. Because `probe_success` is a `1` or `0` sampled on every scrape, you can average it over time to get an availability ratio.

```{code-block} text
:caption: uptime over the last 30 days, as a percentage

avg_over_time(probe_success{instance="https://carlosneto.dev"}[30d]) * 100
```

If the probe succeeded on 99.7% of the scrapes in that window, you get `99.7`. That is a rough but honest estimate of uptime as seen from where the exporter runs. It is not a contractual SLA calculation, and it only reflects the probe interval and the exporter's own vantage point, but as a first approximation it is good enough to answer "how reliable has this endpoint been lately?".

A couple of other queries I keep around:

```{code-block} text
:caption: endpoints currently down

probe_success == 0
```

```{code-block} text
:caption: TLS certificates expiring in the next 15 days

(probe_ssl_earliest_cert_expiry - time()) / 86400 < 15
```

That certificate query has saved me more than once. A whitebox setup would never have caught an expiring cert on a load balancer I did not even own.

## A Simple Alert

Pairing the probe with an alert closes the loop. Here is the one I always start with:

```{code-block} yaml
:caption: alert.rules.yml

groups:
  - name: blackbox
    rules:
      - alert: EndpointDown
        expr: probe_success == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Endpoint {{ $labels.instance }} is down"
          description: "The blackbox probe for {{ $labels.instance }} has been failing for over 2 minutes."
```

The `for: 2m` avoids paging on a single flaky scrape. It fires only when the endpoint stays unreachable, which is usually what you actually care about.

## Conclusion (Author Opinion)

The Blackbox Exporter is one of those tools that does a small thing and does it well. It will not tell you why your service is slow, and it is not a substitute for proper application metrics. But for checking that your user-facing endpoints are reachable, that certificates are not about to expire, and for getting a rough read on uptime, it is hard to beat for the effort it takes to set up.

The multi-target relabeling pattern is the only real hump, and once it clicks, adding a new endpoint is a one-line change. I run it alongside my whitebox metrics, not instead of them. Whitebox tells me why something broke, blackbox tells me the user felt it.

If you only have internal metrics today and no idea whether users can actually reach your service, start here. Give it a try.

## References

- Blackbox Exporter: <https://github.com/prometheus/blackbox_exporter>
- Blackbox Exporter configuration: <https://github.com/prometheus/blackbox_exporter/blob/master/CONFIGURATION.md>
- Prometheus multi-target exporter pattern: <https://prometheus.io/docs/guides/multi-target-exporter/>
- Prometheus relabeling: <https://prometheus.io/docs/prometheus/latest/configuration/configuration/#relabel_config>
- PromQL functions: <https://prometheus.io/docs/prometheus/latest/querying/functions/>

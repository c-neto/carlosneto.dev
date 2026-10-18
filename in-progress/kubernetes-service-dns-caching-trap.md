---
tags: kubernetes, dns, istio, python
date: ""
category: Kubernetes
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---

# The Service Still Works After I Deleted It: Kubernetes DNS Caching and Blue-Green Traps

This blog post explains a subtle failure mode I keep running into: an application that calls a Kubernetes Service by its DNS name keeps working even after the Service is gone, because the resolved IP is cached on the client. It walks through why that happens, how it bites you during blue-green deployments, and how to make the application resilient, both with a plain Python retry and with a service mesh like Istio.

## A Weird Thing I Saw in Production

Picture a simple setup. An application sends HTTP requests to another service at `payments.api.svc.cluster.local`. Standard Kubernetes service discovery. The app does not know any IP addresses. It just uses the DNS name, and the cluster resolves it.

One day, during some cleanup, the `payments` Service got deleted by mistake. I expected the calling app to start failing immediately. It did not. Requests kept going through for a while, as if nothing had happened. My first reaction was the honest one: how is this still working? I just deleted the thing it talks to.

That question is the whole point of this post. The answer is DNS caching, and understanding it changes how you think about deployments.

## How Kubernetes Resolves a Service Name

When you create a Service of type `ClusterIP`, Kubernetes assigns it a stable virtual IP. That IP stays the same for the entire lifetime of the Service. CoreDNS watches the API and creates an A record so that `payments.api.svc.cluster.local` resolves to that ClusterIP.

You can see the whole chain from inside a Pod:

```{code-block} bash
:caption: inside a Pod

cat /etc/resolv.conf

# output expected:
#
# nameserver 10.96.0.10
# search api.svc.cluster.local svc.cluster.local cluster.local
# options ndots:5
```

```{code-block} bash
:caption: resolve the service name

nslookup payments.api.svc.cluster.local

# output expected:
#
# Name:      payments.api.svc.cluster.local
# Address 1: 10.96.120.45 payments.api.svc.cluster.local
```

So the name resolves to a ClusterIP (here `10.96.120.45`). Traffic to that IP is then load balanced by kube-proxy across the Pods behind the Service. The application never sees the Pod IPs. It only ever talks to the ClusterIP.

## Why the App Kept Working After the Delete

Two layers of caching explain it.

First, **DNS caching**. CoreDNS answers with a TTL. By default that TTL is only 5 seconds, so you would think a stale record disappears almost instantly. But the TTL is a suggestion, and not everything respects it. Many HTTP clients and runtimes cache the resolved IP for much longer, or until the process restarts.

Second, and more important here, **the open connection**. Once the client has resolved the name to `10.96.120.45` and opened a TCP connection, it does not re-resolve DNS for every request. HTTP keep-alive and connection pools reuse that socket. As long as the ClusterIP still routes to healthy Pods, requests keep flowing, even though the Service object is gone from the API.

Here is the subtle part. Deleting the Service object does not always tear down the ClusterIP routing instantly, and the client is holding a connection to an IP it resolved earlier. From the application's point of view, nothing changed. It is talking to an IP, not to a Kubernetes abstraction. That is why it kept working.

> <i class="fa-solid fa-circle-info"></i> The JVM is the classic offender: its default DNS cache policy can keep a resolved address for the entire life of the process. Python is friendlier, but a `requests` Session with a connection pool will happily reuse a socket to a stale IP for a long time.

## Where This Bites: Blue-Green Deployments

A cached IP that happens to still work is not the real danger. The danger is when the IP changes underneath you and the client never notices.

Think about a blue-green deployment done at the Service level. You have the "blue" payments stack running. You bring up "green" alongside it. To cut over, one common (and flawed) approach is to delete the old Service and create a new one pointing at green.

Here is the trap: when you delete and recreate a `ClusterIP` Service, the new Service usually gets a **different ClusterIP**. The DNS name `payments.api.svc.cluster.local` now points at a new address. But your calling application cached the old one, and it is still holding a connection to it.

The outcomes range from bad to confusing:

- __Silent stale routing__: the client keeps hitting the old ClusterIP. If blue is still up, it talks to the old version. Your "cutover" did nothing for that client.
- __Connection errors__: if the old ClusterIP is gone, the client gets connection refused or timeouts, and keeps retrying the dead IP because that is what it cached.
- __Partial outage__: some replicas of the app re-resolved and moved to green, others did not. Now you have two versions serving traffic at the same time, which is exactly what blue-green was supposed to avoid.

The deployment looked clean from the cluster side. The Service was swapped, DNS was updated. But the application layer was never told, and it was built to trust a name it resolved once and cached.

:::{note}
A good first mitigation is to avoid deleting and recreating the Service at all. Keep the Service stable and shift traffic by changing its label selector, or by using a proper progressive delivery tool. But even then, you cannot assume every client re-resolves promptly. The application still has to be defensive.
:::

## The Application Must Be Prepared

The real lesson is that DNS is not a strong contract. A name that resolved a minute ago can point somewhere else now, or nowhere at all. The application that depends on it has to expect that and recover.

There are two places to fix this: in the application code, or in the network layer around it.

### Option 1: Handle It in the Client (Python Example)

At minimum, the client should time out, retry, and not cling to a dead connection forever. In Python with `requests` plus `urllib3`, you can attach a retry policy to the Session and set sensible timeouts.

```{code-block} python
:caption: resilient_client.py

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry = Retry(
    total=3,                       # retry failed requests up to 3 times
    backoff_factor=0.5,            # exponential backoff: 0.5s, 1s, 2s
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET", "POST"],
)

session = requests.Session()
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

# a connect timeout and a read timeout, so a dead IP fails fast instead of hanging
response = session.get(
    "http://payments.api.svc.cluster.local/charge",
    timeout=(2, 5),   # (connect timeout, read timeout)
)
```

This does two useful things. The timeouts stop the app from hanging forever on a ClusterIP that no longer answers, and the retries give it a chance to establish a fresh connection, which forces re-resolution of the name. It is not a complete fix for the JVM-style "cache forever" problem, but for most Python HTTP clients, a new connection means a new DNS lookup.

The limitation is obvious: every language and every client library handles DNS caching and retries differently. You end up reimplementing the same resilience logic in every service, in every stack. That gets tiring fast.

### Option 2: Push It Down to a Service Mesh (Istio)

This is where a service mesh earns its complexity. With [Istio](https://istio.io/), a sidecar proxy (Envoy) handles the actual network calls for your application. The app still calls `payments.api.svc.cluster.local`, but the proxy manages DNS, connection pools, retries, and health, consistently, for every service in the mesh, regardless of language.

You configure retries declaratively with a `VirtualService`:

```{code-block} yaml
:caption: payments-virtualservice.yaml

apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: payments
spec:
  hosts:
  - payments.api.svc.cluster.local
  http:
  - route:
    - destination:
        host: payments.api.svc.cluster.local
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: connect-failure,refused-stream,503
```

And you can eject unhealthy endpoints automatically with outlier detection in a `DestinationRule`, so the proxy stops sending traffic to backends that keep failing:

```{code-block} yaml
:caption: payments-destinationrule.yaml

apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: payments
spec:
  host: payments.api.svc.cluster.local
  trafficPolicy:
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s
```

The big win is that this behavior lives outside your application and applies uniformly. Your Python service, your Go service, and your legacy JVM app all get the same retry and health logic without touching their code. A mesh also gives you finer control over the blue-green cutover itself, shifting traffic by weight between subsets instead of swapping a Service out from under your clients.

The honest trade-off: Istio is a lot of machinery to run. For a small cluster with a couple of services, it can be overkill, and the sidecars add latency and resource cost. For a large fleet of services in many languages, that cost usually pays for itself.

## Conclusion (Author Opinion)

The thing that stuck with me from this whole episode is how easy it is to trust DNS as if it were a guarantee. It is not. A Kubernetes Service name is a convenient pointer that can change or vanish, and the moment your application caches the resolved IP, it is one deploy away from talking to the wrong place or nothing at all.

The deletion that "did nothing" was the warning sign, not the bug. The real bug would have shown up later, quietly, during a blue-green cutover, as a fraction of requests going to the old version while everyone assumed the switch was clean.

My take: assume DNS can lie to you, and make the client defensive. If you only run a handful of services, a proper retry and timeout policy in the client, like the Python example, is enough and cheap. Once you are running many services across several languages, pushing resilience and traffic control into a mesh like Istio stops being overengineering and starts being the sane option. Every case is different, but the mindset is the same: never assume the name still points where it did a minute ago.

## References

- Kubernetes Service: <https://kubernetes.io/docs/concepts/services-networking/service/>
- DNS for Services and Pods: <https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/>
- Debugging Services: <https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/>
- CoreDNS custom TTL: <https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/>
- urllib3 Retry: <https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry>
- Istio VirtualService retries: <https://istio.io/latest/docs/reference/config/networking/virtual-service/>
- Istio DestinationRule outlier detection: <https://istio.io/latest/docs/reference/config/networking/destination-rule/>

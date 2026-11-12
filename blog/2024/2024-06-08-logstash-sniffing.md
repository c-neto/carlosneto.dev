---
tags: logstash, opensearch, logs
date: "2024-06-08"
category: Observability
author: Carlos Neto
title: "Logstash Sniffing: Improving Log Ingestion in OpenSearch Scalable Clusters"
description: "Why Logstash behind a load balancer keeps sending logs to a single OpenSearch ingest node, and how the output plugin's sniffing options spread ingestion across every node as the cluster scales."
myst:
  html_meta:
    description: "Why Logstash behind a load balancer keeps sending logs to a single OpenSearch ingest node, and how the output plugin's sniffing options spread ingestion across every node as the cluster scales."
og:title: "Logstash Sniffing: Improving Log Ingestion in OpenSearch Scalable Clusters"
og:description: "Why Logstash behind a load balancer keeps sending logs to a single OpenSearch ingest node, and how the output plugin's sniffing options spread ingestion across every node as the cluster scales."
---

*__Blog Post Publish Date:__ 2024/06/08*

---

# Logstash Sniffing: Improving Log Ingestion in OpenSearch Scalable Clusters

This blog post covers a common problem when Logstash ships logs to an OpenSearch cluster with autoscaling ingest nodes behind a load balancer: one node takes all the traffic while the others sit idle. It shows how the output plugin's sniffing options fix that by discovering the nodes from the OpenSearch API.

## The Problem: One Ingest Node Takes All the Traffic

An **ingest node** is an OpenSearch node that preprocesses documents before they are indexed. The [node types](https://opensearch.org/docs/2.14/tuning-your-cluster/) documentation describes how a cluster can have dedicated ingest nodes, and on Kubernetes they are often scaled with a Horizontal Pod Autoscaler (HPA) and reached through a load balancer.

That setup has a catch when Logstash is the shipper. Shipping logs over HTTP is stateless, but Logstash keeps a persistent connection to the node the load balancer picked first. As long as that connection stays open, every log goes to the same node. That node gets overloaded while the other ingest nodes are underused. If the HPA scales on average resource usage, the imbalance also hides the real load, so the autoscaler reacts too late or not at all.

## The Solution: Let Logstash Discover the Nodes

The [`hosts`](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-hosts) parameter of the output plugin accepts one address or several. With several addresses, Logstash balances the traffic across them. For a fixed set of ingest nodes, listing them all solves the problem. For nodes that scale up and down, a static list goes stale quickly.

**Sniffing** is the output plugin's answer for dynamic clusters: Logstash periodically asks the cluster which nodes exist and updates its host list. The [sniffing parameters](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-sniffing) read the node addresses from the [Nodes Info API](https://opensearch.org/docs/latest/api-reference/nodes-apis/nodes-info/). The [OpenSearch output plugin](https://github.com/opensearch-project/logstash-output-opensearch) is a fork of the Elasticsearch one and keeps these options. For example:

```js
output {
  opensearch {
    hosts           => "https://opensearch-load-balancer:9200"
    sniffing        => true
    sniffing_delay  => 30
    sniffing_path   => "/_nodes/ingest:true"
    ...
  }
}
```

When Logstash starts, it calls `/_nodes/ingest:true` to get the addresses of all ingest nodes, and adds them to its host list. Every `30` seconds, it calls the API again, adding new nodes and removing the ones that are gone. The load balancer address is only used to reach that API.

> <i class="fa-solid fa-circle-info"></i> The [`sniffing_path`](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-sniffing_path) parameter selects which nodes to use. For example, `/_nodes/data:true` sends logs straight to the [data nodes](https://opensearch.org/docs/2.14/tuning-your-cluster/).

Two things are worth checking before you enable it. Logstash connects to the addresses the nodes publish, so they must be reachable from where Logstash runs. If Logstash runs outside the Kubernetes cluster, pod IPs usually aren't. And if the connection uses TLS, the node certificates must be valid for those addresses, not only for the load balancer's hostname.

## Why I Use Sniffing

With sniffing enabled, the traffic spreads evenly across the ingest nodes. It also takes the load balancer out of the data path, removes an extra network hop, and makes better use of resources. The HPA also gets a realistic view of the load, so scaling works the way it should.

It's simple and effective enough that I miss it in other log shippers, such as Fluent Bit. I have been using this approach, and the results are really nice!

For more on how OpenSearch places the data once it arrives, see [OpenSearch Concepts: Index and Shards](/blog/2025/2025-01-05-opensearch-concepts-index-and-shards.md). If your Logstash configuration is growing across many applications, [Logstash Modular Pipelines](/blog/2023/2023-11-02-logstash-modular-pipelines.md) shows how I keep it organized.

## Key Takeaways

- Behind a load balancer, Logstash keeps a persistent connection to one OpenSearch node and sends all logs to it.
- That overloads one ingest node, leaves the others idle, and gives the autoscaler a misleading average.
- A static list in `hosts` works for a fixed set of nodes, but not for nodes that scale up and down.
- `sniffing => true` with `sniffing_path => "/_nodes/ingest:true"` makes Logstash discover the ingest nodes and refresh the list every `sniffing_delay` seconds.
- The load balancer address is only used to reach the Nodes Info API.
- The published node addresses must be reachable from Logstash, and TLS certificates must cover them.

## References

- [Elasticsearch output plugin: sniffing options (Logstash)](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-sniffing)
- [logstash-output-opensearch (GitHub)](https://github.com/opensearch-project/logstash-output-opensearch)
- [Creating a cluster: node types (OpenSearch)](https://opensearch.org/docs/2.14/tuning-your-cluster/)
- [Nodes Info API (OpenSearch)](https://opensearch.org/docs/latest/api-reference/nodes-apis/nodes-info/)

*I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Logstash Sniffing: Improving Log Ingestion in OpenSearch Scalable Clusters",
      "description": "Why Logstash behind a load balancer keeps sending logs to a single OpenSearch ingest node, and how the output plugin's sniffing options spread ingestion across every node as the cluster scales.",
      "datePublished": "2024-06-08",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2024/2024-06-08-logstash-sniffing/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2024/2024-06-08-logstash-sniffing/",
      "keywords": ["Logstash", "OpenSearch", "sniffing", "ingest nodes", "load balancing"],
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
        {"@type": "ListItem", "position": 3, "name": "Logstash Sniffing: Improving Log Ingestion in OpenSearch Scalable Clusters"}
      ]
    }
  ]
}
</script>
```

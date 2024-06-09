---
tags: logstash, opensearch
date: "2024-06-08"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2024/06/08*

---

# Logstash Sniffing: Improving Log Ingestion in OpenSearch Scalable Clusters

This blog post outlines an optimize log ingestion in OpenSearch using Logstash. It will address a common issue related to shipping logs to scalable OpenSearch clusters and provide an effective solution to enhance resource utilization.

## The Problem - Unbalanced Node Utilization in OpenSearch Cluster

When managing an OpenSearch cluster with scalable [Ingest Nodes](https://opensearch.org/docs/2.14/tuning-your-cluster/) accessed through a load balancer and using Logstash to ingest logs, the Elasticsearch/OpenSearch output plugin requires customization to optimally utilize the available OpenSearch resources.

Although log shipping to OpenSearch is stateless over the HTTP protocol, Logstash establishes a fixed connection with a specific OpenSearch ingest node. When a load balancer selects a node, Logstash will keep to send all logs to this node as long as the connection remains active. This can overwhelm the selected node, leaving other Ingest Nodes underutilized. Additionally, if you use average resource metrics for scaling Ingest Nodes with Horizontal Pod Autoscaling (HPA), this imbalance can impact performance.

## The Solution - Utilizing OpenSearch API for Dynamic Hosts Registration

The [hosts](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-hosts) parameter in the OpenSearch output plugin can be configured with a single address or multiple addresses. Using multiple addresses allows Logstash to manage and balance log shipping across declared hosts. For non-scalable Ingest Nodes, specifying multiple hosts is a solution of the issue described above. However, for scalable Ingest Nodes, this static approach is insufficient due to the dynamic nature of node scaling.

To address this, the OpenSearch output plugin offers [sniffing parameters](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-sniffing) to dynamically retrieve the current OpenSearch nodes addresses from the [OpenSearch API](https://opensearch.org/docs/latest/api-reference/nodes-apis/nodes-info/) and update the hosts configuration accordingly.

Consider the following example:

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

When Logstash starts, it sends a request to the OpenSearch API endpoint `/_nodes/ingest:true` to retrieve the addresses of all Ingest Nodes. These addresses are dynamically added and removed from the hosts list. Every `30` seconds, the node pool addresses are updated. The Load Balancer address `https://opensearch-load-balancer:9200` is used only to fetch the IP addresses.

> <i class="fa-solid fa-circle-info"></i> You can specify other OpenSearch node types using the [sniffing_path](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-sniffing_path) parameter. For instance, to use [Data nodes](https://opensearch.org/docs/2.14/tuning-your-cluster/), set the parameter to `/_nodes/data:true`.

## Conclusion (Author Opinion)

This approach ensures better traffic distribution to OpenSearch, significantly reduces load balancer traffic, eliminates an extra network hop, and enhances resource usage, thereby improving Horizontal Pod Autoscaling in OpenSearch.

This solution is so effective and straightforward that I'm beginning to miss its presence in other log shipping tools like Fluentbit.

I have been using this approach and the results are really nice!

## Links

- Logstash Output ElasticSearch/OpenSearch: <https://www.elastic.co/guide/en/logstash/current/plugins-outputs-elasticsearch.html#plugins-outputs-elasticsearch-sniffing>
- OpenSearch Cluster Formation (Node Types): <https://opensearch.org/docs/2.14/tuning-your-cluster/>
- OpenSearch Nodes API: <https://opensearch.org/docs/latest/api-reference/nodes-apis/nodes-info/>

---
tags: kubernetes, fluent-bit, logs
date: "2025-06-22"
category: Observability
author: Carlos Neto
title: "Kubernetes Logs Simplified: Everything You Need to Know About Pod Logging"
description: "Where Kubernetes stores container logs, how kubectl logs and log shippers read them, the CRI log line format, how the kubelet rotates log files, and how to ship pod logs with a Fluent Bit DaemonSet."
myst:
  html_meta:
    description: "Where Kubernetes stores container logs, how kubectl logs and log shippers read them, the CRI log line format, how the kubelet rotates log files, and how to ship pod logs with a Fluent Bit DaemonSet."
og:title: "Kubernetes Logs Simplified: Everything You Need to Know About Pod Logging"
og:description: "Where Kubernetes stores container logs, how kubectl logs and log shippers read them, the CRI log line format, how the kubelet rotates log files, and how to ship pod logs with a Fluent Bit DaemonSet."
---

*__Blog Post Publish Date:__ 2025/06/22*

---

# Kubernetes Logs Simplified: Everything You Need to Know About Pod Logging

This blog post explains where Kubernetes stores container logs and how `$ kubectl logs` and log shippers read them. It also covers the CRI log line format, how log rotation works, and how to ship pod logs to an external system with a DaemonSet. Kubernetes logging can look complex, but knowing these details makes troubleshooting much easier.

## How Kubernetes Stores Container Logs

Kubernetes runs containers through a container runtime, such as containerd or CRI-O. The **Container Runtime Interface (CRI)** is the API that the kubelet uses to talk to that runtime. As the [CRI documentation](https://kubernetes.io/docs/concepts/architecture/cri/) describes, one part of it defines how container logs are handled: file names, directory locations, and line format. The [CRI logging design proposal](https://github.com/kubernetes/design-proposals-archive/blob/main/node/kubelet-cri-logging.md) and the [Kubernetes logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/) page have the details.

Each container in a pod writes its logs to its own file, with everything the application sends to _stdout_ and _stderr_ (the [standard streams](https://en.wikipedia.org/wiki/Standard_streams)). The files live on the node where the pod runs:

```bash
# pod container log file pattern
/var/log/pods/<namespace>_<podname>_<uid>/<container_name>/<restart-count>.log

# example
/var/log/pods/default_nginx-7f5c7d4f9b-abcde_12345/nginx-container/
  ├── 0.log   # first run of the container
  ├── 1.log   # run after the first restart
  └── ...
```

The file name is the container's restart count. The first run writes `0.log`. If the container crashes or restarts, the new run writes `1.log`, then `2.log`, and so on, while the previous file stays on disk. The kubelet keeps the logs of the most recent terminated run, which is what `$ kubectl logs --previous <pod> -c <container>` reads.

To make ingestion easier for third-party tools, the kubelet also creates a symbolic link to each container's current log file in `/var/log/containers/`. The link name includes the pod name, namespace, container name, and container ID, so log shippers can identify each container:

```bash
# >>> symbolic link log file name pattern
/var/log/containers/<pod_name>_<namespace>_<container_name>-<container_id>.log

# >>> symbolic link log file name example
/var/log/containers/nginx-7f5c7d4f9b-abcde_default_nginx-container-12345.log

# >>> real file that the symbolic link points to
/var/log/pods/default_nginx-7f5c7d4f9b-abcde_12345/nginx-container/0.log
```

`$ kubectl logs` doesn't use these links. They exist for log shippers such as [Fluent Bit](https://docs.fluentbit.io/manual), [Vector](https://vector.dev/), and [Filebeat](https://www.elastic.co/beats/filebeat). A link always points to the log file of the current run and doesn't concatenate older runs. The container ID is part of the link name, so a restarted container gets a new link that points to its new log file. The same happens when the kubelet rotates a file: the path stays the same, but it's a new file.

Log shippers must handle that. Fluent Bit, for example, tracks the inode of each file it reads. When a rotated file has the same name but a new inode, Fluent Bit treats it as a new file and reads it from the start. See [the Tail input reference](https://docs.fluentbit.io/manual/pipeline/inputs/tail#keep_state) for the details.

## The Kubernetes Log Line Format

The CRI defines the format of each line in the log file:

```text
# >>> log line pattern
<timestamp> <stream> <flags> <message>

# >>> log line examples
2023-10-06T00:17:09.669794202Z stdout F Your log message here
2023-10-06T00:17:09.669794202Z stdout P Another log pt 1
```

- __timestamp__: when the line was written, in [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) format with nanosecond precision.
- __stream__: `stdout` or `stderr`.
- __flags__: `F` for a full line, `P` for a partial line.
- __message__: the raw log message from the container.

The `P` flag appears when a single line is longer than the runtime's maximum log line size, 16 KiB by default in containerd (`max_container_log_line_size`). The runtime splits the line into chunks: each chunk except the last is written with `P`, and the last one with `F`. For example, an application that prints one 40 KB line produces three entries:

```text
2025-06-21T22:15:10.123456789Z stdout P <first 16 KiB of the line>
2025-06-21T22:15:10.123456790Z stdout P <next 16 KiB of the line>
2025-06-21T22:15:10.123456791Z stdout F <rest of the line>
```

`$ kubectl logs` joins the partial chunks before showing them, so you see one line. Log shippers have to do the same. Fluent Bit, for example, does it with its built-in CRI multiline parser.

## Managing Log Growth with Log Rotation

Logs can grow until they fill the node's disk, which hurts observability in the cluster and the performance of the applications on that node. Even if an application logs very little, enforce size limits and rotation.

**Log rotation** for container logs is done by the kubelet. According to the [log rotation](https://kubernetes.io/docs/concepts/cluster-administration/logging/#log-rotation) documentation, the kubelet rotates each container log file when it reaches `containerLogMaxSize` (10Mi by default) and keeps at most `containerLogMaxFiles` files (5 by default). Configure these limits in the kubelet instead of using a third-party tool such as [logrotate](https://github.com/logrotate/logrotate). Renaming, truncating, or closing files behind the kubelet's back can corrupt its log management, and the log layout may change in future Kubernetes versions.

You set the limits in the [kubelet configuration file](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/):

```{code-block} yaml
:caption: /var/lib/kubelet/config.yaml (excerpt)

apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
containerLogMaxSize: 100Mi
containerLogMaxFiles: 5
```

Or with the equivalent kubelet flags, for example through the kubelet's systemd unit:

```{code-block} ini
:caption: [/etc/systemd/system/kubelet.service](https://github.com/kubernetes/release/blob/cd53840/cmd/krel/templates/latest/kubelet/kubelet.service)

Environment="KUBELET_EXTRA_ARGS=--container-log-max-size=100Mi --container-log-max-files=5"
```

If you change the kubelet unit, put the change in a drop-in file instead of editing the unit itself, as I explain in [Systemd Drop-in Overrides](/blog/2023/2023-11-19-systemd-override-parameters.md).

## Shipping Kubernetes Logs to an External System

For search and long-term analysis, ship workload logs to a log analytics system such as [OpenSearch](https://opensearch.org/), [Elasticsearch](https://www.elastic.co/elasticsearch), [Grafana Loki](https://grafana.com/oss/loki/), [Splunk](https://www.splunk.com/), or [Datadog](https://www.datadoghq.com/). Inside the cluster, tools such as [Fluent Bit](https://docs.fluentbit.io/manual), [Filebeat](https://www.elastic.co/beats/filebeat), and [Vector](https://vector.dev/) read, process, and send the logs.

Whatever shipper you choose, the deployment pattern is the same. A **DaemonSet** is a Kubernetes workload that runs one pod on every node, and the [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) for the shipper mounts the node's `/var/log` directory with a [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume. The shipper reads `/var/log/containers/*.log`, and because those links point into `/var/log/pods/`, the mount must include both directories. Mounting `/var/log` covers them. For example, a Fluent Bit DaemonSet:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: default
  labels:
    app: fluent-bit
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      containers:
        - name: fluent-bit
          image: docker.io/bitnami/fluent-bit:4.0.3-debian-12-r0
          resources:
            limits:
              memory: "200Mi"
              cpu: "100m"
            requests:
              memory: "100Mi"
              cpu: "50m"
          volumeMounts: 
            - name: config
              mountPath: /opt/bitnami/fluent-bit/conf/fluent-bit.conf
              subPath: fluent-bit.conf
            # >>> MOUNTS THE NODE'S LOG DIRECTORY (BOTH /var/log/containers AND /var/log/pods)
            - name: varlog
              mountPath: /var/log
              readOnly: true
      volumes:
        - name: config
          configMap:
            name: fluent-bit-config
        # >>> ALLOWS THE FLUENT BIT POD TO READ THE LOG FILES OF PODS SCHEDULED ON THE NODE
        - name: varlog
          hostPath:
            path: /var/log
            type: Directory
```

Many log shippers can also add metadata such as pod labels and annotations to each log. For that, the shipper needs permission to read from the Kubernetes API, usually through a [ClusterRole](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) bound to its service account. [This Fluent Bit ClusterRole](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/templates/clusterrole.yaml) is an example. I'll cover metadata enrichment with Fluent Bit in a future post.

Once the logs are flowing, two problems usually come next. Fluent Bit can deliver a log more than once, which I address in [Generating Log IDs with SHA-256 Hashes](/blog/2025/2025-06-19-fluentbit-log-dedup.md). And teams start counting log lines to build dashboards, which I argue against in [Stop Extracting Metrics from OpenSearch Logs](/blog/2026/2026-11-03-stop-extracting-metrics-from-opensearch-logs.md).

## Key Takeaways

- The container runtime writes each container's stdout and stderr to `/var/log/pods/<namespace>_<pod>_<uid>/<container>/<restart-count>.log` on the node.
- Each restart writes a new file. `kubectl logs --previous` reads the log of the previous run.
- `/var/log/containers/` holds symbolic links to the current log file of each container, for log shippers.
- Each line follows the CRI format `<timestamp> <stream> <flags> <message>`. `P` marks a chunk of a line longer than the runtime's limit, and `F` marks the end.
- The kubelet rotates container logs with `containerLogMaxSize` and `containerLogMaxFiles`. Don't use logrotate on these files.
- Ship logs with a DaemonSet that mounts the node's `/var/log`, not only `/var/log/containers`, because the links point into `/var/log/pods`.

## References

- [Logging architecture (Kubernetes)](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Container Runtime Interface (Kubernetes)](https://kubernetes.io/docs/concepts/architecture/cri/)
- [CRI logging design proposal (Kubernetes)](https://github.com/kubernetes/design-proposals-archive/blob/main/node/kubelet-cri-logging.md)
- [Kubelet configuration (Kubernetes)](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/)
- [DaemonSet (Kubernetes)](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [kubectl logs (Kubernetes)](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/)
- [Tail input (Fluent Bit)](https://docs.fluentbit.io/manual/pipeline/inputs/tail)
- [containerd configuration (containerd)](https://github.com/containerd/containerd/blob/main/docs/man/containerd-config.toml.5.md)
- [Standard streams (Wikipedia)](https://en.wikipedia.org/wiki/Standard_streams)

---

> *I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Kubernetes Logs Simplified: Everything You Need to Know About Pod Logging",
      "description": "Where Kubernetes stores container logs, how kubectl logs and log shippers read them, the CRI log line format, how the kubelet rotates log files, and how to ship pod logs with a Fluent Bit DaemonSet.",
      "datePublished": "2025-06-22",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2025/2025-06-22-kubernetes-logs-simplified/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2025/2025-06-22-kubernetes-logs-simplified/",
      "keywords": ["Kubernetes", "pod logs", "kubectl logs", "CRI", "log rotation", "Fluent Bit"],
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
        {"@type": "ListItem", "position": 3, "name": "Kubernetes Logs Simplified: Everything You Need to Know About Pod Logging"}
      ]
    }
  ]
}
</script>
```

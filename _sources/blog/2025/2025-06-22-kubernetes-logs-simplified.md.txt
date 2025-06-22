---
tags: fluentbit, logs, observability
date: "2025-06-22"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/06/22*

---

# Kubernetes Logs Simplified: Everything You Need to Know About Pod Logging

Have you ever wondered how `$ kubectl logs` retrieves logs, where they are stored, and how to access both current and past logs? Kubernetes logging can seem complex, but understanding it is key to troubleshooting and monitoring. This blog post outlines how Kubernetes organizes logs, how to send them to external systems, and tips to manage log growth effectively.

## How Kubernetes Manages and Stores Logs

Kubernetes is essentially composed of containers, which are managed by container runtimes. These container runtimes must implement the [Container Runtime Interface (CRI)](https://kubernetes.io/docs/concepts/architecture/cri/), which defines how Kubernetes interacts with the containers. One of the specifications in the [CRI](https://kubernetes.io/docs/concepts/architecture/cri/) is container log handling, which standardizes details such as log names, directory locations, and formats.

:::{note}
- CRI Logs Desing Proposal: <https://github.com/kubernetes/design-proposals-archive/blob/main/node/kubelet-cri-logging.md>
- Kubernetes Logging Reference: <https://kubernetes.io/docs/concepts/cluster-administration/logging/>
:::

Each container in a pod writes its logs to a separate file. These logs capture everything the application outputs to _stdout_ and _stderr_ (see [standard streams](https://en.wikipedia.org/wiki/Standard_streams)). The log files are stored on the node where the pod is running at:

```bash
# pod container log file pattern
/var/log/pods/<namespace>_<podname>_<uid>/<container_name>/<execution-id>.log

# example
/var/log/pods/default_nginx-7f5c7d4f9b-abcde_12345/nginx-container/
  ├── 0.log   # current container live running log
  ├── 1.log   # last container log that exited on failure or was restarted
  ├── 2.log   # second to last container log that exited on failure or was restarted
  └── ...
```

The `0.log` file contains the current container's live running logs. If the container crashes and restarts, Kubernetes renames `0.log` to `1.log` and creates a new `0.log` for the new run. This process continues with `2.log`, `3.log`, and so on. When you execute `kubectl logs --previous <pod> -c <container>`, the kubelet searches for logs in `1.log`, `2.log`, and subsequent files.

To make log ingestion easier for third-party tools, the kubelet creates symbolic links to each container's current log file (`0.log`) in the `/var/log/containers/` directory. Each symbolic link is named using the pod name, namespace, container name, and container ID, making it easy for log shippers to identify and process logs for each container.

```bash
# >>> symbolic link log file name pattern
/var/log/containers/<pod_name>_<namespace>_<container_name>-<container_id>.log

# >>> symbolic link log file name example
/var/log/containers/nginx-7f5c7d4f9b-abcde_default_nginx-container-12345.log

# >>> real file that the symbolic link points to
/var/log/pods/default_nginx-7f5c7d4f9b-abcde_12345/nginx-container/0.log
```

The `$ kubectl logs` command always uses the absolute path of the log file and never the symbolic link path. The symbolic link is a mechanism that the kubelet uses to simplify log ingestion for third-party log shipping tools like [Fluent Bit](https://docs.fluentbit.io/manual), [Vector](https://vector.dev/), [Filebeat](https://www.elastic.co/pt/beats/filebeat), etc. It is important to understand that the files present in `/var/log/containers/` point to the current container execution log (`0.log`) and do not concatenate the files `0.log`, `1.log`, `2.log`, and so on. When a container crashes and a new `0.log` is created, the symbolic link points to the new `0.log` file, so the content is overwritten. The log shipping tool should be prepared to handle this behavior. Fluent Bit, for example, uses inode tracking of the symlinked log file. When the file that the symlink points to is rotated, the inode of the file changes as well, and Fluent Bit understands that it is a new log file and needs to read the log content from the start, even though the file name remains the same. For more details, see [the Fluent Bit Input Plugin reference](https://docs.fluentbit.io/manual/pipeline/inputs/tail#keep_state).

## Understanding Kubernetes Log Format

The log file content is saved in a specific pattern defined by the CRI. This log line format is:

```log
# >>> log line pattern
<timestamp> <stream> <flags> <message>

# >>> log line examples
2023-10-06T00:17:09.669794202Z stdout F Your log message here
2023-10-06T00:17:09.669794202Z stdout P Another log pt 1
```

- __timestamp__: The date and time when the log line was written, formatted according to [RFC3339](https://datatracker.ietf.org/doc/html/rfc3339) with nanosecond precision.
- __stream__: Specifies whether the log line was written to `stdout` or `stderr`.
- __flags__: `F` indicates a completed log line, delimited by `\n`, while `P` indicates a partial log line. More details will be explained below.
- __log message__: The container's log message in its raw format.

About __flags__: The `F` flag indicates a complete log line (ending with `\n`). The `P` flag signifies that the application has not finished writing the line yet, so the runtime is writing it in parts. When logs are retrieved using `kubectl logs`, the tool merges these parts together before displaying them to the user.

To understand this better, check the following Python application code:

```python
#!/bin/python

print("part 1 - ", end="")
print("part 2 - ", end="")
print("part 3 - ", end="")
print("log line completed!", end="\n")
```

The logs are saved in the following format:

```log
2025-06-21T22:15:10.123456789Z stdout P part 1 - 
2025-06-21T22:15:10.123456790Z stdout P part 2 - 
2025-06-21T22:15:10.123456791Z stdout P part 3 - 
2025-06-21T22:15:10.123456792Z stdout F log line completed!
```

When a pod log is retrieved using `$ kubectl logs`, the output will concatenate partial logs:

```bash
$ kubectl logs -f python-app

part 1 - part 2 - part 3 - log line completed!
```

## Managing Log Growth with Log Rotation

Logs can grow uncontrollably, causing disk overflow, which can impact observability in your cluster and degrade application performance. Even if the application generates a low volume of logs, it is a best practice and highly recommended to enforce limits and implement log rotation routines. The best approach to control log size limits is to define the values using container runtime parameters. It is not recommended to use third-party tools like [logrotate](https://github.com/logrotate/logrotate) for this task, as file operations such as renaming, truncating, and closing file descriptors can corrupt Kubernetes' log management state. Additionally, the container runtime's log management architecture may change in future Kubernetes versions, requiring updates to third-party tools to align with the new behavior.

Thus, the configuration defines the Container Runtime's log rotation process. The example below demonstrates how to configure containerd to manage the log rotation routine.

```{code-block} toml
:caption: [/etc/containerd/config.toml](https://github.com/containerd/containerd/blob/main/docs/man/containerd-config.toml.5.md)

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  LogSizeMax = 104857600  # set log file size limit to 100MB
  LogFileMax = 5          # set limit 5 log files
```

Also, you can introduce this parameters via environment variables to kubelet service. Below as example using systemd, to define the log rotate parameters for kubelet process to inject log rotate parameters to containerd.

```{code-block} ini
:caption: [/etc/systemd/system/kubelet.service](https://github.com/kubernetes/release/blob/cd53840/cmd/krel/templates/latest/kubelet/kubelet.service)

Environment="KUBELET_EXTRA_ARGS=--container-log-max-size=100Mi --container-log-max-files=5"
```

## Strategy to Ingest Kubernetes Logs to External Thirdy Party System

For a better observability experience, it is highly recommended to use a third-party, dedicated log analytics system like [OpenSearch](https://opensearch.org/), [ElasticSearch](https://www.elastic.co/pt/elasticsearch), [Grafani Loki](https://grafana.com/oss/loki/), [Splunk](https://www.splunk.com/), or [Datadog](https://www.datadoghq.com/). To achieve this, it is necessary to ingest the log file content from Kubernetes nodes into the third-party log system. For log reading, there are specific tools optimized for reading, processing, and shipping logs to external systems, such as [Fluent Bit](https://docs.fluentbit.io/manual), [Filebeat](https://www.elastic.co/pt/beats/filebeat), and [Vector](https://vector.dev/).

Regardless of the log shipping tool you choose, the configuration format for the tool remains the same. The log ingestion tool is deployed using a [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/), which schedules one pod on each node in the cluster. The [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) is configured with a [hostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) volume mount, allowing the pod to access files stored on the node's disk. This enables the log ingestion tool to read log files for all pod containers scheduled on the node at `/var/log/containers/*.log`.

Below is an example of a [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) configuration for implementing [Fluent Bit](https://docs.fluentbit.io/manual):

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
            # >>> THIS LINE MOUNTS THE NODE'S POD CONTAINERS DIRECTORY INSIDE THE CONTAINER.
            - name: varlog
              mountPath: /var/log/containers
      volumes:
        - name: config
          configMap:
            name: fluent-bit-config
        # >>> THIS LINE ALLOWS THE FLUENT BIT POD TO ACCESS LOG FILES OF PODS SCHEDULED ON THE NODE. 
        - name: varlog
          hostPath:
            path: /var/log/containers
            type: Directory
```

Many log collection tools can add extra information to your logs, like pod labels and annotations. To do this, the log collector needs permission to talk to the Kubernetes API. This is usually done by giving the tool a [ClusterRole](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) with the right permissions and linking it to the service account the tool uses. For example, you can look at [this Fluent Bit ClusterRole](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/templates/clusterrole.yaml) to see how it works. With these permissions, the tool can get metadata from Kubernetes and add it to each log before sending it to your log system. Setting up metadata enrichment with [Fluent Bit](https://docs.fluentbit.io/manual) will be explained in a future post.

## References

- <http://kubernetes.io/docs/user-guide/kubectl/kubectl_logs/>
- <https://github.com/containerd/containerd/blob/main/docs/man/containerd-config.toml.5.md>
- <https://github.com/kubernetes/release/blob/cd53840/cmd/krel/templates/latest/kubelet/kubelet.service>
- <https://docs.docker.com/engine/admin/logging/overview/>
- <https://github.com/kubernetes/design-proposals-archive/blob/main/node/kubelet-cri-logging.md>
- <https://github.com/kubernetes/kubernetes/issues/17183>
- <https://github.com/kubernetes/kubernetes/issues/24677>
- <https://github.com/kubernetes/kubernetes/issues/30709>
- <https://github.com/kubernetes/kubernetes/issues/31459>
- <https://github.com/kubernetes/kubernetes/pull/13010>
- <https://github.com/kubernetes/kubernetes/pull/33111>
- <https://kubernetes.io/docs/concepts/cluster-administration/logging/>
- <https://en.wikipedia.org/wiki/Standard_streams>

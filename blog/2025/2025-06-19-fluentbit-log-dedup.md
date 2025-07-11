---
tags: fluentbit, logs, observability
date: "2025-06-19"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/06/19*

---

# Fluent Bit: Generating Log IDs with SHA-256 Hashes for Log Deduplication

This post explores the root causes of log duplication, the necessity of generating unique log identifiers, and how to leverage Fluent Bit’s native capabilities to create SHA-256 hashes for effective deduplication without relying on external scripts or plugins.

## Why Do Duplicate Logs Occur in Fluent Bit?

I encountered issues with duplicated logs being indexed in OpenSearch by Fluent Bit. After some research, I concluded that currently, Fluent Bit, when using the [Tail](https://docs.fluentbit.io/manual/pipeline/inputs/tail) input, offers features designed for the __At Least Once__ delivery strategy. This means that a message may be delivered one or more times, potentially causing duplication. It does not support __Exactly Once__ or __At Most Once__ strategies, where a message is delivered only once or at most once, respectively.

There are several variables that can contribute to this behavior. For example, when using the [Tail](https://docs.fluentbit.io/manual/pipeline/inputs/tail) input plugin, even if you use an SQL database with `DB On` parameter, you may still experience duplicate logs. This is because the database only persists the file reading offset, not the delivery status for each configured [Output](https://docs.fluentbit.io/manual/pipeline/outputs). 

I plan to write a separate blog post with more details about how Fluent Bit manages log delivery state (_chunk, buffering, SQL Lite, Storage Type_). For now, it's important to understand that in certain scenarios such as output unavailability and Fluent Bit restarts—duplication can occur. This is expected behavior and not necessarily a problem, especially when multiple [Output](https://docs.fluentbit.io/manual/pipeline/outputs) configurations are used.

## The Importance of Unique Log IDs

If the delivery strategy is __At Least Once__, generating a unique ID is a hard requirement to avoid duplication at the [Output](https://docs.fluentbit.io/manual/pipeline/outputs) destination. This unique ID should be created based on the log line content. If you are using Logstash and OpenSearch in your log analytics stack, you can generate IDs using the [Logstash Fingerprint filter plugin](https://www.elastic.co/docs/reference/logstash/plugins/plugins-filters-fingerprint) or the [OpenSearch Fingerprint Ingest Pipeline Processor](https://docs.opensearch.org/docs/latest/ingest-pipelines/processors/fingerprint/), both of which create hashes based on specified log field values. Unfortunately, Fluent Bit does not have a specific native filter plugin to create unique IDs. You can use a Lua script or bash script callback for it, but in both cases, the complexity increases and you become dependent on external crypto libraries. However, don't worry, I will show you a workaround to generate a hash from the log line content using only Fluent Bit's native features.

If you are using Fluent Bit to send logs directly to OpenSearch, you can use the [OpenSearch Output Plugin](https://docs.fluentbit.io/manual/pipeline/outputs/opensearch) with the `Generate_ID On` parameter enabled to generate a unique ID for logs. However, __note that the ID generated by this option will be different even if the one ore more log line content is the same__. The `Generate_ID On` option generates an ID within Fluent Bit only; it does not create a unique ID based on the log content. To avoid duplicate logs, generate a hash-based ID derived from the log content itself.

## Generating SHA-256 Hashes for Log Deduplication

I reviewed the available Fluent Bit filter plugins and did not find any that generate hash values based on a log key. However, I discovered a [Processor Content Modifier Action](https://docs.fluentbit.io/manual/pipeline/processors/content-modifier) called [hash](https://docs.fluentbit.io/manual/pipeline/processors/content-modifier#hash-example). This action takes a log event key as an argument and replaces its value with a SHA-256 hash. While this feature is primarily intended for masking sensitive data such as passwords and PII, it can also be used to generate unique identifiers for log events. 

The __key insight__ is to copy the log line content to a new key and hash this new field, keeping the original log line content intact and using the hashed field as the log ID. Check example:

```{code-block} yaml
:caption: [/fluent-bit/fluent-bit.yaml](https://github.com/c-neto/my-devops-labs/blob/main/blog/2025-06-19/fluent-bit.yaml)

# The `pipeline.inputs.processors` feature is only available when using the `yaml` configuration format.  
# It is not supported in the legacy `.conf` configuration format.

pipeline:
  inputs:
    - name: dummy
      dummy: |
        {
          "message": "2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log"
        }
      tag: dummy.foobar
      processors:
        logs:
          # Copy the 'message' field to a new field called '_id'.
          - name: modify
            copy: message _id

          # Hash the '_id' field to anonymize or deduplicate.
          - name: content_modifier
            action: hash
            key: _id

    - name: dummy
      dummy: |
        {
          "message": "2025-06-19T17:02:35.123456789Z stdout F This is a Greeting application log sample running in kubernetes persisted on /var/log/containers/*.log"
        }
      tag: dummy.greeting 
      processors:
        logs:
          # Copy the 'message' field to a new field called '_id'.
          - name: modify
            copy: message _id

          # Hash the '_id' field to anonymize or deduplicate.
          - name: content_modifier
            action: hash
            key: _id

  outputs:
    - name: stdout
      format: json_lines
      match: "dummy.*"

```

The output is like:

```json
{
  "date": 1750366003.411804,
  "message": "2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log",
  "_id": "19a93f55808eb5478c65813c028045f1b354abe12790eb8aee0dd825697aa93e"
}
{
  "date": 1750366003.415653,
  "message": "2025-06-19T17:02:35.123456789Z stdout F This is a Greeting application log sample running in kubernetes persisted on /var/log/containers/*.log",
  "_id": "148917c2efe0114da7f7cef6327bde63f5c9ec5cac5cf05d4a73acefaa69a55c"
}
{
  "date": 1750366004.412541,
  "message": "2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log",
  "_id": "19a93f55808eb5478c65813c028045f1b354abe12790eb8aee0dd825697aa93e"
}
{
  "date": 1750366004.413101,
  "message": "2025-06-19T17:02:35.123456789Z stdout F This is a Greeting application log sample running in kubernetes persisted on /var/log/containers/*.log",
  "_id": "148917c2efe0114da7f7cef6327bde63f5c9ec5cac5cf05d4a73acefaa69a55c"
}
```

The [hash](https://docs.fluentbit.io/manual/pipeline/processors/content-modifier#hash-example) action takes the binary value of the log line, applies the SHA-256 algorithm, and outputs the result as a hexadecimal string. Below is a Python script that performs the same hashing process as Fluent Bit.

```python
import hashlib

log_line_in_string = "2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log"

log_line_in_bytes = log_line_in_string.encode("utf-8")
log_line_in_sha256_hexa_decimal = hashlib.sha256(log_line_in_bytes).hexdigest()

print(log_line_in_sha256_hexa_decimal)
>>> "19a93f55808eb5478c65813c028045f1b354abe12790eb8aee0dd825697aa93e"
```

Now, you can use the `_id` as log unique ID field!

:::{note}
You can find a complete, working example of this configuration in my Docker Compose lab repository: <i class="fab fa-github"></i> [github.com/c-neto/my-devops-labs/blog/2025-06-19/docker-compose.yml](https://github.com/c-neto/my-devops-labs/blob/main/blog/2025-06-19/)
:::

## References

- Docker-Compose Lab: <https://github.com/c-neto/my-devops-labs/blob/main/blog/2025-06-19/docker-compose.yml>
- Logstash Fingerprint Filter Plugin: <https://www.elastic.co/docs/reference/logstash/plugins/plugins-filters-fingerprint>
- OpenSearch Fingerprint Ingest Pipeline Processor: <https://docs.opensearch.org/docs/latest/ingest-pipelines/processors/fingerprint/>
- Fluent Bit Processors Reference: <https://docs.fluentbit.io/manual/pipeline/processors/content-modifier>
- Fluent Bit Hash Example: <https://docs.fluentbit.io/manual/pipeline/processors/content-modifier#hash-example>

---
tags: fluentbit, logs, observability
date: "2025-06-19"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/06/19*

---

# Fluent Bit: Generating Log IDs with SHA-256 Hashes for Log Deduplication

This post explains how to prevent duplicate logs in Fluent Bit, especially when sending logs to OpenSearch. It covers why duplicates occur, the importance of unique log IDs, and how to use Fluent Bit’s built-in features to create SHA-256 hashes for deduplication.

## Why Do Duplicate Logs Occur in Fluent Bit?

I encountered issues with duplicated logs being indexed in OpenSearch by Fluent Bit. After some research, I concluded that currently, Fluent Bit, when using the Tail input, offers features designed for the __At Least Once__ delivery strategy. This means that a message may be delivered one or more times, potentially causing duplication. It does not support __Exactly Once__ or __At Most Once__ strategies, where a message is delivered only once or at most once, respectively.

There are several variables that can contribute to this behavior. For example, when using the Tail input plugin, even if you use an SQL database, you may still experience duplicate logs. This is because the database only persists the file reading offset, not the delivery status for each configured output. 

I plan to write a separate blog post with more details about how Fluent Bit manages log delivery state. For now, it's important to understand that in certain scenarios, like outputs unavailability and Fluent Bit restarts, duplication can occur and is expected not a problem (especially with multiple Output configuration).

## The Importance of Unique Log IDs

If the delivery strategy is __At Least Once__, generating a unique ID is a hard requirement to avoid duplication at the output destination. This unique ID should be created based on the log line content. If you are using Logstash and OpenSearch in your log analytics stack, you can generate IDs using the [Logstash Fingerprint filter plugin](https://www.elastic.co/docs/reference/logstash/plugins/plugins-filters-fingerprint) or the [OpenSearch Fingerprint Ingest Pipeline Processor](https://docs.opensearch.org/docs/latest/ingest-pipelines/processors/fingerprint/), both of which create hashes based on specified log field values. Unfortunately, Fluent Bit does not have a specific native filter plugin to create unique IDs. You can use a Lua script or bash script callback for it, but in both cases, the complexity increases and you become dependent on external crypto libraries. However, don't worry, I will show you a workaround to generate a hash from the log line content using only Fluent Bit's native features.

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
      dummy: '{"message": "2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log"}'
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

  outputs:
    - name: stdout
      format: json_lines
      match: "dummy.foobar"
```

The output is like:

```json
fluentbit  | {"date":1750362419.414721,"message":"2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log","_id":"19a93f55808eb5478c65813c028045f1b354abe12790eb8aee0dd825697aa93e"}
fluentbit  | {"date":1750362420.41307,"message":"2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log","_id":"19a93f55808eb5478c65813c028045f1b354abe12790eb8aee0dd825697aa93e"}
fluentbit  | {"date":1750362421.411586,"message":"2025-06-19T17:02:35.123456789Z stdout F This is a Foobar application log sample running in kubernetes persisted on /var/log/containers/*.log","_id":"19a93f55808eb5478c65813c028045f1b354abe12790eb8aee0dd825697aa93e"}
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
You can find a complete, working example of this configuration in my Docker Compose lab repository: <i class="fab fa-github fa-fade"></i> [github.com/c-neto/my-devops-labs/blog/2025-06-19/docker-compose.yml](https://github.com/c-neto/my-devops-labs/blob/main/blog/2025-06-19/docker-compose.yml)
:::

## References

- Docker-Compose Lab: <https://github.com/c-neto/my-devops-labs/blob/main/blog/2025-06-19/docker-compose.yml>
- Logstash Fingerprint Filter Plugin: https://www.elastic.co/docs/reference/logstash/plugins/plugins-filters-fingerprint
- OpenSearch Fingerprint Ingest Pipeline Processor: https://docs.opensearch.org/docs/latest/ingest-pipelines/processors/fingerprint/
- Fluent Bit Processors Reference: <https://docs.fluentbit.io/manual/pipeline/processors/content-modifier>
- Fluent Bit Hash Example: <https://docs.fluentbit.io/manual/pipeline/processors/content-modifier#hash-example>

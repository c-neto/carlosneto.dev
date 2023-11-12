---
tags: logstash
date: "2023-11-12"
category: Observability
---

*__Blog Post Publish Date:__ 2023/11/12*

---

# Logstash Modular Pipelines: A Solution to Avoid Code Duplicated

This blog post explores the structuring of Logstash pipelines to mitigate code duplicated and presents an elegant method for reusing code statements across multiple pipelines.

The post provides a clear explanation of the Logstash configuration structure, outlining the problem addressed by modular pipelines. It includes an example configuration and directs readers to a Docker-compose lab for hands-on testing and exploration of the possibilities. Finally, the post concludes with my personal opinion on the effectiveness of this structure.

## A Little About Logstash and Pipelines Structure

The Logstash is an amazing tool for crafting robust log pipelines. Several plugins empower the ingestion, process, enrich, and output integration with external stacks. The pipelines are created using Logstash Configuration DSL (_Domain-Specific Language_), a high-level configuration language designed to be efficient and flexible, and focused on Log Pipeline needs.

The Logstash pipeline configuration is composed of three main statements:

- `input`: Define the log ingestion source;
- `filter`: Define the process, parser, and enrich routines;
- `output`: Define the external stacks forward integrations post process step.

> _<i class="fa-solid fa-link"></i> More Details: [Logstash - Configuration File Structure](https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure)_

## The Problem: Scaling Up Pipelines == Growing Code Duplication

When the number of the log pipeline increase, the complexity and code duplicated tends to grow along with it. In simple Application observability needs, pipelines with `input`, `filter`, and `output` configured together in the same file can fit the needs. Otherwise, in complex and big Applications scenarios, like distributed Applications deployed over Kubernetes, some complexity challenges are occurring. One of the main challenges is __code deduplicated avoiding__.

When you have many applications to process the logs, each one with distinct logical needs, you can create only one pipeline composed with logical condition to use specific process statement based on the source identification field in the events, for example, Tags that identifies the module that generated the event. This approach is good because avoids duplicated of the `input` and `output` configuration, but is bad because creates an overhead in the `filter` statement, and makes it hard to do troubleshooting in the Logstash API metrics to detect the Application process offenders.

Another possibility is to create a distinct pipeline, in distinct configuration files, dedicated for each Application. This approach solves the `filter` overhead, but duplicates the `input` and `output`.

## The Solution: Modularize the Pipeline

A good way to solve the problems mentioned before is: __modularize the Logstash statements to load them in dedicated Application log pipelines based on needs__.

For this, it is necessary to create `input`, `filter`, and `output` in separate files, and to create dedicated pipelines by Application, and configure them using blob [
Glob Pattern Support](https://www.elastic.co/guide/en/logstash/current/glob-support.html) and [Environment Variable](https://www.elastic.co/guide/en/logstash/current/environment-variables.html) notation.

The following topic will explain with more details about how to do it.

## Configuration Example

First step is to create the modules, that is, files with `input`, `filter`, and `output` in separate files each one focused on their specifics and atomic needs.

```{code-block} bash
:caption: $ tree /usr/share/logstash/pipeline/

├── filter-app-a.cfg      # filter of the application-a logic parser
├── filter-app-b.cfg      # filter of the application-b logic parser
├── input-http.cfg        # input to receive logs from http protocol
├── input-rabbitmq.cfg    # input to receive logs from rabbitmq rabbit
├── output-opensearch.cfg # output to forward logs processed to opensearch server 
└── output-http.cfg       # output to forward logs processed to http server
```

Next, for each application, configure one with [Environment Variable](https://www.elastic.co/guide/en/logstash/current/environment-variables.html) Logstash notation:

```{code-block} yaml
:caption: $ cat /usr/share/logstash/config/pipeline.yml

- pipeline.id: application-a-pipeline
  path.config: "/usr/share/logstash/pipeline/${LOGSTASH_PIPELINE_APPLICATION_A}.cfg"

- pipeline.id: application-a-pipeline
  path.config: "/usr/share/logstash/pipeline/${LOGSTASH_PIPELINE_APPLICATION_B}.cfg"
```

Finally, the key point of this approach. You will define the pipeline composition based on modules through environment variables. Check the following example:

```{code-block} bash
:caption: $ env

LOGSTASH_PIPELINE_APPLICATION_A="{input-http,input-rabbitmq,filter-app-a,output-opensearch,output-http}"
LOGSTASH_PIPELINE_APPLICATION_B="{input-http,filter-app-b,output-opensearch}"
```

- The `LOGSTASH_PIPELINE_APPLICATION_A` environment variable value configures the Logstash pipeline `application-a-pipeline` to receive logs from HTTP and RabbitMQ, and the logs will be processed by logic defined in the `filter-app-a.cfg` and forwarded to OpenSearch and HTTP server.

- The `LOGSTASH_PIPELINE_APPLICATION_B` environment variable value configures the Logstash pipeline `application-b-pipeline` to receive logs from HTTP and RabbitMQ, and the logs will be processed by logic defined in the `filter-app-a.cfg` and forwarded to OpenSearch and HTTP server.

### Main Advantages:

This approach brings the following advantages:

- __Reusable Code__: Avoid code duplicated of the `input` and `output` statements, because the pipelines will define which inputs will be used.
- __Decrease Complexity__: Decrease the complexity of the `filter` avoiding long pipeline files with conditional logic based on application.
- __Troubleshooting__: Preserve the troubleshooting and metrics because pipelines are traceable in the logstash metic API.
- __Tests__: Make it easier to test `filter` code because the `input` and `output` changes are simple, and can be changed with a mock log source and output to stdout to check if the logic is working as expected.

### Docker Compose Lab

I created a docker-compose lab to test and explore the possibilities of the content presented in this post. Check in my GitHub: <i class="fa-brands fa-github"></i> [c-neto/my-devops-lab/blog/2023-11-12/](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/).

## Conclusion (Author Opinion)

Logstash is a versatile tool for log processing, providing well-configured solutions for both small and large workloads to meet Observability needs. While the Logstash Module structure offers a straightforward approach to mitigate recurring issues in pipeline creation, it is not the exclusive remedy for this challenge.

Understanding Observability requirements is essential for effectively harnessing the tool's features. Occasionally, the Logstash Module Structure may introduce unnecessary complexity, especially in scenarios involving a limited number of applications.

I have implemented this structure and witnessed significant improvements in maintainability tasks, particularly in the advantages it brings to testing, where I can easily assess my filter logics with minimal cognitive effort.

I genuinely appreciate this structure, but it's important to recognize that __every case is unique, and each context presents its own complexity and challenges__. In some instances, I opt against this approach because my primary goal is to simplify maintainability. Therefore, it is advisable to adopt this structure only when addressing a specific existing problem.

## References

- <https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure>
- <https://www.elastic.co/guide/en/logstash/current/glob-support.html>
- <https://www.elastic.co/guide/en/logstash/current/environment-variables.html>
- <https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/>

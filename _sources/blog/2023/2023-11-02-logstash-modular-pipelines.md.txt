---
tags: logstash
date: "2023-11-12"
category: Observability
---

*__Blog Post Publish Date:__ 2023/11/12*

---

# Logstash Modular Pipelines: An Elegant Structure for Code Reusability and Duplication Avoiding

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

As the number of log pipelines increases, so does the complexity and tendency for code duplication. For straightforward application observability needs, having pipelines with `input`, `filter`, and `output` configured together in the same file might suffice. However, in complex scenarios involving large applications, such as distributed applications deployed on Kubernetes, various challenges emerge. Among these challenges, one of the most significant is avoiding code duplication.

When dealing with multiple applications requiring distinct logic for log processing, one approach is to create a single pipeline with logical conditions determining the specific processing statements based on fields such as Tags, which identify the module generating the event. While this method is advantageous in avoiding duplication of `input` and `output` configurations, it has drawbacks. It introduces overhead in the `filter` statement and complicates troubleshooting in the Logstash API metrics for identifying application process issues.

Alternatively, another approach is to establish separate pipelines, each with its own dedicated configuration files for individual applications. While this resolves the `filter` overhead issue, it comes at the cost of duplicating both `input` and `output` configurations.

## The Solution: Modularize the Pipeline

A good way to solve the problems mentioned before is: __modularize the Logstash statements to load them in dedicated Application log pipelines based on needs__.

For this, it is necessary to create `input`, `filter`, and `output` in separate files, and to create dedicated pipelines by Application, and configure them using blob [
Glob Pattern Support](https://www.elastic.co/guide/en/logstash/current/glob-support.html) and [Environment Variable](https://www.elastic.co/guide/en/logstash/current/environment-variables.html) notation.

The following topic will explain with more details about how to do it.

## Configuration Example

First step is to create the modules, that is, files with `input`, `filter`, and `output` in separate files each one focused on their specifics and atomic needs.

```{code-block} bash
:caption: $ tree /usr/share/logstash/pipeline/

├── filter-app-a.cfg        # filter of the application-a logic parser
├── filter-app-b.cfg        # filter of the application-b logic parser
├── input-http.cfg          # input to receive logs from http protocol
├── input-rabbitmq.cfg      # input to receive logs from rabbitmq rabbit
├── output-opensearch.cfg   # output to forward logs processed to opensearch server 
└── output-http.cfg         # output to forward logs processed to http server
```

Next, for each application, configure them with [Environment Variable](https://www.elastic.co/guide/en/logstash/current/environment-variables.html) Logstash notation:

```{code-block} yaml
:caption: $ cat /usr/share/logstash/config/pipeline.yml

- pipeline.id: application-a-pipeline
  path.config: "/usr/share/logstash/pipeline/${LOGSTASH_PIPELINE_APPLICATION_A}.cfg"

- pipeline.id: application-b-pipeline
  path.config: "/usr/share/logstash/pipeline/${LOGSTASH_PIPELINE_APPLICATION_B}.cfg"
```

Finally, the core aspect of this approach lies in defining the pipeline composition based on modules through the use of environment variables. Consider the following example:

```{code-block} bash
:caption: $ env

LOGSTASH_PIPELINE_APPLICATION_A="{input-http,input-rabbitmq,filter-app-a,output-opensearch,output-http}"
LOGSTASH_PIPELINE_APPLICATION_B="{input-http,filter-app-b,output-opensearch}"
```

- __LOGSTASH_PIPELINE_APPLICATION_A__: Composes the Logstash pipeline `application-a-pipeline` to receive logs from HTTP and RabbitMQ, and the logs will be processed by logic defined in the `filter-app-a.cfg` and forwarded to OpenSearch and HTTP server.

- __LOGSTASH_PIPELINE_APPLICATION_B__: Composes the Logstash pipeline `application-b-pipeline` to receive logs from HTTP, logs will be processed by logic defined in the `filter-app-b.cfg` and forwarded to OpenSearch.

### Main Advantages:

This approach brings the following advantages:

- __Avoid Code Duplication__: Avoid code duplicated of the `input` and `output` statements, because the pipelines will define which inputs will be used.
- __Reusable Code__: Allows the _import_ modules in multiple pipelines.
- __Decrease Complexity__: The `filter` code is composed of only the application log parser logic.
- __Troubleshooting__: Preserve the traceable of the pipelines in the logstash metric API.
- __Tests__: Make it easier to test `filter` code because the `input` and `output` modules is simple to change, allowing a configuration of the _mock_ log source as `input` and _stdout_ as a `output` to check if the logic is working as expected.

### Docker Compose Lab

I created a docker-compose lab to test and explore the possibilities of the content presented in this post. Check in my GitHub: <i class="fa-brands fa-github"></i> [c-neto/my-devops-lab/blog/2023-11-12/docker-compose.yaml](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/).

## Conclusion (Author Opinion)

Logstash is a versatile tool for log processing, providing well-configured solutions for both small and large workloads to meet Observability needs. While the Logstash Module structure offers a straightforward approach to mitigate recurring issues in pipeline creation, it is not the exclusive remedy for this challenge.

Understanding Observability requirements is essential for effectively harnessing the tool's features. Occasionally, the Logstash Module Structure may introduce unnecessary complexity, especially in scenarios involving a limited number of applications.

I have implemented this structure and witnessed significant improvements in maintainability tasks, particularly in the advantages it brings to testing, where I can easily assess my filter logics with minimal cognitive effort (changing a environment variable).

I genuinely appreciate this structure, but it's important to recognize that __every case is unique, and each context presents its own complexity and challenges__. In some instances, I opt against this approach because my primary goal is to simplify maintainability. Therefore, it is advisable to adopt this structure only when addressing a specific existing problem.

## References

- <https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure>
- <https://www.elastic.co/guide/en/logstash/current/glob-support.html>
- <https://www.elastic.co/guide/en/logstash/current/environment-variables.html>
- <https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/>

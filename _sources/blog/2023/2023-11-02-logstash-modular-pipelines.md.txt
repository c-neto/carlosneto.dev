---
tags: logstash
date: "2023-11-12"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2023/11/12*

---

# Logstash Modular Pipelines: An Elegant Structure for Code Reusability and Duplication Avoiding

This blog post explores a Logstash pipelines structure to mitigate code duplicated and presents an elegant method for reusing code section across multiple pipelines.

The post provides a clear explanation of the Logstash configuration structure, outlining the problem addressed by modular pipelines. It includes an example configuration and a Docker-compose lab for hands-on testing and exploration of the possibilities. Finally, the post concludes with my opinion on the effectiveness of this structure.

## A Little About Logstash and Pipelines Structure

The Logstash is an amazing tool for crafting robust log pipelines. Several plugins empower the ingestion, process, enrich, and output integration with external stacks. The pipelines are created using Logstash Configuration DSL (_Domain-Specific Language_), a high-level configuration language designed to be efficient and flexible, and focused on Log Pipeline needs.

The Logstash pipeline configuration is composed of three main sections:

- `input`: Define the log ingestion source.
- `filter`: Define the process, parser, and enrich routines.
- `output`: Define the forward routines with external stacks.

> _<i class="fa-solid fa-link"></i> More Details: [Logstash - Configuration File Structure](https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure)_

## The Problem: Scaling Up Pipelines == Growing Code Duplication

As the number of log pipelines increases, so does the complexity and tendency for code duplication. For straightforward application observability needs, having pipelines with `input`, `filter`, and `output` configured together in the same file might suffice. However, in complex scenarios involving large applications, such as distributed applications deployed on Kubernetes, various challenges emerge. Among these challenges, one of the most significant is avoiding code duplication.

When dealing with multiple applications requiring distinct logic for log processing, one approach is to create a single pipeline with logical conditions determining the specific processing statements based on fields such as Tags, which identify the module generating the event. While this method is advantageous in avoiding duplication of `input` and `output` configurations, it has drawbacks. It introduces overhead in the `filter` section and complicates troubleshooting in the Logstash API metrics for identifying application process issues.

Alternatively, another approach is to establish separate pipelines, each with its own dedicated configuration files for individual applications. While this resolves the `filter` overhead issue, it comes at the cost of duplicating both `input` and `output` configurations.

## The Solution: Modularize the Pipeline

A good way to solve the problem mentioned before is __modularize the Logstash Pipelines sections _(input, filter, output)_ in isolated files, and load them in dedicated Pipelines based on their needs__.

For this, it is necessary to create separate files with only one Pipeline section definition (_input, filter, output_), create dedicated pipelines for each Application, and configure them using [
Glob Pattern Support](https://www.elastic.co/guide/en/logstash/current/glob-support.html) and [Environment Variable](https://www.elastic.co/guide/en/logstash/current/environment-variables.html) notation.

The following sub topic will explain with more details about how to do it.

## Configuration Example

First step, is to create the modules, that is, the code of the `input`, `filter`, and `output` in separate files, each one focused on their specifics and atomic needs.

```{code-block} bash
:caption: $ tree /usr/share/logstash/pipeline/

├── filter-app-a.cfg        # filter of the application-a logic parser
├── filter-app-b.cfg        # filter of the application-b logic parser
├── input-http.cfg          # input to receive logs from http protocol
├── input-rabbitmq.cfg      # input to receive logs from rabbitmq queue
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

Finally, configure the composition of the pipeline with [Glob Pattern Support](https://www.elastic.co/guide/en/logstash/current/glob-support.html) notation. Consider the following example:

```{code-block} bash
:caption: $ env

LOGSTASH_PIPELINE_APPLICATION_A="{input-http,input-rabbitmq,filter-app-a,output-opensearch,output-http}"
LOGSTASH_PIPELINE_APPLICATION_B="{input-http,filter-app-b,output-opensearch}"
```

- __LOGSTASH_PIPELINE_APPLICATION_A__: Composes the Logstash pipeline `application-a-pipeline` to receive logs from HTTP and RabbitMQ, processed them with parse logic defined in the `filter-app-a.cfg` and forwarded to OpenSearch and HTTP server.

- __LOGSTASH_PIPELINE_APPLICATION_B__: Composes the Logstash pipeline `application-b-pipeline` to receive logs from HTTP, process them with the logic defined in the `filter-app-b.cfg` and forwarded to OpenSearch only.

### Main Advantages:

This approach brings the following advantages:

- __Avoid Code Duplication__: Allows to use modules across multiple pipelines (for example, configure the same `input` and `output` module for all pipelines).
- __Reusable Code__: Allows a simple configurable way to use more than one module of the same type in specific pipelines (for example, two `output`, and three `input` in one specific pipeline).
- __Decrease Complexity__: The `filter` code is composed of only the application parser logic, avoiding conditional logical based on source event tags to identify how the logic need to be used.
- __Troubleshooting__: Preserve the traceable of the pipelines in the logstash metric API.
- __Tests__: Make it easier to test `filter` code because the `input` and `output` modules is simple to change (environment variables), allowing a configuration of the _mock_ log source as `input` and _stdout_ as a `output` to check if the logic is working as expected.

### Docker Compose Lab

I created a docker-compose lab to test and explore the possibilities of the content presented in this post. 

Check in my GitHub: <i class="fa-brands fa-github"></i> [c-neto/my-devops-lab/blog/2023-11-12/docker-compose.yaml](https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/).

## Conclusion (Author Opinion)

Logstash is a versatile tool for log processing, providing well-configured solutions for both small and large workloads to meet Observability needs. While the Logstash Module structure offers a straightforward approach to mitigate recurring issues in pipeline creation, it is not the exclusive remedy for this challenge.

Understanding Observability requirements is essential for effectively harnessing the tool's features. Occasionally, the Logstash Module Structure may introduce unnecessary complexity, especially in scenarios involving a limited number of applications.

I have implemented this structure and witnessed significant improvements in maintainability, particularly in the __Tests__ advantages mentioned, where I can easily test my `filter` logics with a simple a environment variable value changing.

I genuinely appreciate this structure because my primary goal is to simplify and make it easier the maintainability, but it’s important to recognize that __every case is unique, and each context presents its own complexity and challenges__. Therefore, I recommend adopting this structure when the maintenance of pipelines becomes complex, code duplication is on the rise, and the configuration of Logstash becomes prone to errors, ultimately rendering it difficult to maintain.

## References

- <https://www.elastic.co/guide/en/logstash/8.11/configuration-file-structure.html#configuration-file-structure>
- <https://www.elastic.co/guide/en/logstash/current/glob-support.html>
- <https://www.elastic.co/guide/en/logstash/current/environment-variables.html>
- <https://github.com/c-neto/my-devops-labs/tree/main/blog/2023-11-12/>

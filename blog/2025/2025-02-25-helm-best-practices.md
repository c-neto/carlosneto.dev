---
tags: helm
date: "2025-02-25"
category: Kubernetes
---

*__Blog Post Publish Date:__ 2025/02/25*

---

# Helm Charts: Development Practices from a Programmer’s Perspective

In the last quarter of 2024, I delved deep into the world of Helm Charts and encountered several challenges. Initially, creating a new Helm Chart seemed to introduce complexity, and I didn't see significant advantages over using Kustomize. However, after spending days reflecting, reading more about Helm, and examining existing projects, I gained insights that helped me view Helm as an ally rather than an unnecessarily complex tool. So, I compiled the main insights in this blog post to present Helm chart development tips from a programmer's perspective.

## Why Helm Charts Are a Powerful Tool for IaC

Before discussing best practices for Helm chart development, it is important to understand why Helm Charts are a powerful tool for Infrastructure as Code (IaC). Helm Charts enable the adoption of IaC by providing a robust templating engine for rendering Kubernetes manifests (powered by Go Templates). They allow the creation of reusable components, abstracting Kubernetes workloads, and offering a high-level parameterization interface.

One of Helm’s key advantages is its ability to distribute charts as artifacts, similar to programming language packages or system distributions like RPM and DEB. This allows the creation of new charts that use existing ones as dependencies, which increases agility in developing new solutions based on proven components.

Helm simplifies Kubernetes workload management, streamlining configuration, deployment, and updates. It also supports storing charts as OCI artifacts in registries like AWS Elastic Container Registry (ECR) or as tarball files, ensuring reproducible and seamless deployments. CI/CD tools like Spinnaker and ArgoCD natively support Helm for deployment automation.

Helm Charts are particularly effective for creating reusable, deployable infrastructure components, especially when managing multiple clusters with environment-specific configurations. This approach reduces manifest duplication in Git repositories, improving maintainability and operational efficiency.

## Simple Made Easy - Is Helm Chart Overengineering?

> "_Complexity has to pay for itself. It has to buy you something._"  
> — Simple Made Easy (Rich Hickey, 2011)

When I first started working with Helm Charts, my initial thought was: "_Oh my God, this is so complex, am I just introducing unnecessary complexity?_" However, like any new tool, Helm has a learning curve that takes time to overcome. The key to embracing Helm lies in understanding the problem it solves. If you think Helm is complex, try maintaining multiple nearly identical Kubernetes manifests, where the only differences are a few parameters per cluster it's a recipe for chaos.

In reality, Helm Charts are overengineering only if you’re solving a problem you don’t have. The complexity introduced by Helm justifies itself when it eliminates a bigger problem such as duplicated code across multiple environments. If you’re managing workloads across several clusters, the complexity of Helm is not an overhead but a necessary trade-off to improve maintainability.

I’ll explore this concept further in the next section.

## DRY - Eliminating Redundancy in Kubernetes Manifests with Helm

> "_DRY (Don't Repeat Yourself) is about the duplication of knowledge, of intent. It’s about expressing the same thing in two different places, possibly in two totally different ways._"  
> — The Pragmatic Programmer (Andrew Hunt & David Thomas, 1999)

To illustrate the DRY (Don’t Repeat Yourself) principle, let’s consider a common scenario in IT corporations: maintaining isolated environments for different stages of development. Typically, companies have a development environment used internally for testing, a staging environment for validation, and a production environment serving real users.

If you work in this type of setup, you likely manage workloads across multiple Kubernetes clusters, running the same applications with slight variations, such as Ingress settings, resource allocations, and environment-specific variables. A straightforward approach to handling these differences is to create separate Kubernetes manifest files for each environment, maintaining the same structure but modifying specific values. While this method works, it introduces a significant drawback: __code duplication__.

When managing duplicated manifests, you increase the risk of errors and inconsistencies. This approach may seem manageable with one or two environments, but as the number of environments grows (e.g., 3 or more), it quickly becomes unscalable and difficult to maintain. For instance, applying a patch to one environment requires updating several separate files, increasing operational overhead.

This is where Helm Charts excel. Instead of maintaining multiple duplicate manifests, Helm enables template-driven configuration. The base structure of your Kubernetes manifests resides within the Helm Chart, while environment-specific values are dynamically injected through Go Templates.

Helm achieves this through the `Values.yaml` file, where each environment has its own configuration file defining runtime parameters. Instead of maintaining duplicated YAML files, you have a single chart that dynamically renders manifests based on input values. This approach ensures consistency, maintainability, and scalability.

As you can see, templatizing Kubernetes manifests is another way Helm follows the DRY principle. By reducing redundancy, Helm minimizes errors and simplifies the management of multiple environments, making Kubernetes deployments more efficient and maintainable.

## YAGNI - Avoid Overengineering in Helm Templates

> _"Always implement things when you actually need them, never when you just foresee that you will need them._"  
> — Ron Jeffries about XP principle: _"You ain’t gonna need it (YAGNI)."_

Templates should only be created when they represent a well-defined and reproducible structure. A common mistake when designing Helm Charts is over-templatization, introducing excessive parameterization that makes templates overly flexible but harder to maintain.

If you find yourself defining numerous template functions to handle many variations in your `Values.yaml`, it’s likely a sign that your template lacks a clear structure. Instead of simplifying deployment, you’re introducing unnecessary complexity that can lead to confusion, harder debugging, and increased maintenance effort.

Even worse than not having a template is maintaining template functions that will never be used. Every extra function, conditional statement, or parameter adds cognitive overhead. When a team inherits a Helm Chart filled with unused or rarely used logic, they are forced to understand and maintain complexity that provides no real value.

This follows the YAGNI (You Ain’t Gonna Need It) principle, a fundamental concept in software development that warns against building features or abstractions that are not immediately necessary. Instead of preparing for hypothetical future scenarios, focus on solving real, present problems efficiently.

## Library Charts - Ensuring Reusable Patterns

> _"The design of reusable libraries should provide clear and simple interfaces, allowing users to interact with them without needing to understand their internal details."_
> — Design Patterns: Elements of Reusable Object-Oriented Software (_paraphrased from the sections on encapsulation and reusability_)

There are two types of Helm Charts: __Application__ and __Library__. Application charts are complete solutions, specifically designed for deployment. They define all the necessary Kubernetes resources required to deploy an application. On the other hand, __Library__ charts contain reusable resources such as templates and functions, which are shared across other charts but are not directly deployed. These library charts act as an abstraction layer, providing common components that can be reused in multiple contexts.

A prime example of a well-designed library chart is the Bitnami Common Chart, which consists of reusable functions and patterns that ensure consistency across all Bitnami charts. These patterns are adopted across the entire Bitnami Charts repository, making it easier to maintain and extend their Kubernetes applications. You can find more about the Bitnami Common Library Chart here, and an example of how the common chart is used in practice within Bitnami Fluentbit can be seen here:

- [Bitnami Common Library Chart](https://github.com/bitnami/charts/tree/main/bitnami/common)  
- [Bitnami Fluentbit Example of Common Chart Usage](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/templates/configmap.yaml#L11).

## Conclusion

Incorporating best practices from programming concepts such as DRY, YAGNI, and modular design can significantly improve Helm chart development. By focusing on maintainability, scalability, and reducing unnecessary complexity, you can leverage Helm to create more efficient, reusable Kubernetes components. Helm is not just a tool for templating Kubernetes manifests; it’s a framework for thinking about infrastructure in a modular, reusable way—something that every developer can appreciate. 

These practices allow teams to scale their Kubernetes deployments more efficiently while minimizing overhead and ensuring that the system is easier to maintain in the long run.

## References

- [Anti-patterns - Wikipedia](https://en.wikipedia.org/wiki/Anti-pattern)  
- [Helm Chart Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Martin Fowler on YAGNI](https://martinfowler.com/bliki/Yagni.html)  
- [The 12-Factor App](https://12factor.net/)  
- [Don't Repeat Yourself (DRY) - Wikipedia](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [Bitnami Common Library Chart](https://github.com/bitnami/charts/tree/main/bitnami/common)  
- [Bitnami Fluentbit Example of Common Chart Usage](https://github.com/bitnami/charts/blob/main/bitnami/fluent-bit/templates/configmap.yaml#L11).

---
tags: aws, gcp, azure, oracle
date: "2023-10-21"
category: Cloud
---

*__Blog Post Publish Date:__ 2023/10/21*

---

# Cloud Computing: Overview and Concepts

This blog post explores the impact of Cloud Computing, essential concepts, primary Cloud models, and my personal opinion about its adoption.

## The Impact of Cloud Computing

Historically, Development teams emphasized agility in contributions, while Operations/Infrastructure teams focused more on stability due to hardware interactions. However, with the advent of technologies like virtualization, manual infrastructure tasks became obsolete, and infrastructure components started being provided as a service by Cloud providers like AWS, Google, Microsoft, and others.

Now, agility has become a crucial aspect for Operations teams as well. The maintenance of infrastructure as a service by Cloud providers alleviates concerns about electricity, hardware health, and other infrastructure requirements. This shift allows businesses to concentrate on their core purposes rather than infrastructure necessities. Outsourcing maintenance tasks to specialized teams enhances reliability and security, with various services tailored for infrastructure contexts and business cases. Additionally, hardware security is vital to address concerns like natural disasters and physical threats.

A significant keyword in the Cloud landscape is possibilities. The Cloud offers possibilities to access high computing performance components as needed, scale components on demand, and pay only for the time used. These possibilities can lead to reduced costs if your application or infrastructure is scalable, allowing you to pay only for the resources needed for application functionality.

However, it's important to note that Cloud Computing isn't a one-size-fits-all solution for every IT infrastructure case. It is one of the options to deploy your infrastructure or application. Before adopting the Cloud for your infrastructure, it's crucial to ask yourself, "What problem am I trying to solve?" If your application aligns with the Cloud characteristics mentioned above, it might be the best choice for your needs.

## Concepts and Characteristics

Cloud Computing is a __model for delivering computing services over the internet, providing a platform to manage, process, and store data on remote servers.__

The Cloud Computing main characteristics are:

::::{grid}

:::{grid-item-card}
__Maintenance__
- Less concern about energy and hardware maintenance processes;
- Business focuses more on IT technologies.
---
__Reliability__
- Specialization in determining tools;
- High availability possibilities.
---
__Security__
- Utilization of specific security tools;
- Software and hardware security solutions.
:::

:::{grid-item-card}
__Performance__
- Hardware components available as a service;
- Performance enhancements possible when needed.
---
__Scalability__
- Scalability on demand;
- Minimal IT resource requirements to run applications.
---
__Cost and Elasticity__
- Cost management options;
- Both soft and hard cost considerations with available possibilities.
:::

::::

> <i class="fa-solid fa-link"></i> See also: [AWS - What is Cloud Computing](https://aws.amazon.com/what-is-Cloud-computing/?nc1=h_ls)


## Cloud Main Models

The cloud is not limited to AWS, Google Cloud Platform, or Oracle Cloud. These mentioned cloud providers belong to the category of __Public Cloud__. However, it's essential to understand that there are other ways to implement cloud solutions.

::::{grid}

:::{grid-item-card}
__Public Cloud__
Resources are shared and can be used by anyone (examples: AWS, GCP, Oracle Cloud).
---
__Private Cloud__
Often referred to as _Bare Metal Cloud_ owned by a single entity, and resources are not shared with other corporations (examples: OpenStack, VMWare, and XenServer).
:::

:::{grid-item-card}
__Hybrid Cloud__
A combination of both Private Cloud and Public Cloud components.
---
__MultiCloud__
Cloud architecture is not dependent on a specific Cloud model and can run in both Private and Public Cloud environments.
---
__Community Cloud__
Custom Cloud architecture created by corporations to provide clients with the flexibility of multiple Public and Private Cloud features.
:::

::::

> <i class="fa-solid fa-link"></i> More Details: [NIST - Cloud Computing Definition](https://csrc.nist.gov/publications/detail/sp/800-145/final)

## Conclusion (Author Opinion)

Cloud computing is a __powerful__ tool that can greatly benefit businesses. Cloud providers offer __fantastic solutions__ and services to address the challenges and product requirements, mainly to __large enterprises__. Undoubtedly, Cloud computing has contributed to improvements in the IT product experience and the creation of new products, primarily due to the _Business focusing more on IT technologies_ characteristic, which allows engineers to concentrate their efforts on the product rather than infrastructure challenges.

However, it is important to understand that __it is not a one-size-fits-all solution__. Its effectiveness __depends on your specific needs__ and use cases. While it offers scalability and flexibility, it __can also be more expensive__, especially if not optimized for your requirements. Migrating to the Cloud __requires specialized expertise__ to ensure a smooth transition and efficient management. Additionally, it's important to note that the Cloud is not a guarantee of security; it requires a diligent implementation of security measures to safeguard your data and applications, further emphasizing the need for specialized expertise. Ultimately, the decision to embrace Cloud computing should be carefully evaluated, taking into account the unique demands and goals of your organization.

---

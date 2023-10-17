---
tags: cloud-architect, aws, concepts
date: "2022-05-09"
category: cloud
---

*__Blog Post Publish Date:__ 2022/05/09*

---

# Cloud Basic Concepts

This section covers the fundamental concepts of Cloud Computing, including its definition, advantages and disadvantages, cloud models, and deployment models.

## Cloud Computing: Advantages and Disadvantages

A concise definition of Cloud Computing, often attributed to AWS, is: _"Cloud computing is the on-demand delivery of IT resources over the Internet with pay-as-you-go pricing."_

For beginners, this definition can be a bit overwhelming. To grasp it fully, we need to associate the following key characteristics:

- __Maintenance__
  - Less concern about energy and hardware maintenance processes
  - Business focuses more on IT technologies

- __Reliability__
  - Specialization in determining tools
  - High availability possibilities

- __Security__
  - Utilization of specific security tools
  - Software and hardware security solutions

- __Performance__
  - Hardware components available as a service
  - Performance enhancements possible when needed

- __Scalability__
  - Scalability on demand
  - Minimal IT resource requirements to run applications

- __Cost and Elasticity__
  - Cost management options
  - Both soft and hard cost considerations with available possibilities

Historically, Development teams emphasized agility in contributions, while Operations/Infrastructure teams focused more on stability due to hardware interactions. However, with the advent of technologies like virtualization, manual infrastructure tasks became obsolete, and infrastructure components started being provided as a service by cloud providers like AWS, Google, Microsoft, and others.

Now, agility has become a crucial aspect for Operations teams as well. The maintenance of infrastructure as a service by cloud providers alleviates concerns about electricity, hardware health, and other infrastructure requirements. This shift allows businesses to concentrate on their core purposes rather than infrastructure necessities. Outsourcing maintenance tasks to specialized teams enhances reliability and security, with various services tailored for infrastructure contexts and business cases. Additionally, hardware security is vital to address concerns like natural disasters and physical threats.

A significant keyword in the cloud landscape is `possibilities`. The cloud offers possibilities to access high computing performance components as needed, scale components on demand, and pay only for the time used. These possibilities can lead to reduced costs if your application or infrastructure is scalable, allowing you to pay only for the resources needed for application functionality.

However, it's important to note that Cloud Computing isn't a one-size-fits-all solution for every IT infrastructure case. It is one of the options to deploy your infrastructure or application. Before adopting the cloud for your infrastructure, it's crucial to ask yourself, "What problem am I trying to solve?" If your application aligns with the cloud characteristics mentioned above, it might be the best choice for your needs.

## Main Cloud Models

The primary Cloud Models are:

- __IaaS__ (Infrastructure as a Service): Infrastructure components delivered as a service, such as Virtual Machines, Networks, Firewalls, etc.
  - Examples: AWS VPC, AWS EC2, AWS S3.

- __PaaS__ (Platform as a Service): Services to run applications over infrastructure abstraction. For example, running a web app and delivering static files.
  - Examples: Heroku, AWS Elastic Beanstalk, OpenShift, etc.

- __FaaS__ (Function as a Service): Granular services to simplify recurring tasks, such as sending emails, webhooks, or syncing databases.
  - Examples: AWS Data Sync, AWS Lambda.

## Main Deployment Models

The main Deployment Models include:

- __Private Cloud__: Often referred to as "Bare Metal Cloud," owned by a single entity, and resources are not shared with other corporations.
  - Examples: Created with OpenStack, VMWare, XenServer.

- __Public Cloud__: Resources are shared and can be used by anyone. Major providers include AWS, GCP, Oracle Cloud.
  - Examples: AWS, Google Cloud Platform, Microsoft Azure, Alibaba Cloud.

- __Hybrid Cloud__: A combination of both Private Cloud and Public Cloud components.

- __Multicloud__: Cloud architecture is not dependent on a specific cloud model and can run in both Private and Public Cloud environments.

- __Community Cloud__: Custom cloud architecture created by corporations to provide clients with the flexibility of multiple Public and Private Cloud features.

## References

- AWS - Cloud Computing Definition: <https://aws.amazon.com/what-is-cloud-computing/?nc1=h_ls>
- NIST - Cloud Computing Definition: <https://csrc.nist.gov/publications/detail/sp/800-145/final>

---

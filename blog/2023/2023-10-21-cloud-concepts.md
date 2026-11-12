---
tags: aws, gcp, azure
date: "2023-10-21"
category: Cloud
author: Carlos Neto
title: "What is the Cloud and why does everyone keep talking about it?"
description: "A plain-language explanation of cloud computing: what it is, the problem it solved, when on-premises infrastructure still makes sense, and the costs that vendor pitches tend to skip."
myst:
  html_meta:
    description: "A plain-language explanation of cloud computing: what it is, the problem it solved, when on-premises infrastructure still makes sense, and the costs that vendor pitches tend to skip."
og:title: "What is the Cloud and why does everyone keep talking about it?"
og:description: "A plain-language explanation of cloud computing: what it is, the problem it solved, when on-premises infrastructure still makes sense, and the costs that vendor pitches tend to skip."
---

*__Blog Post Publish Date:__ 2023/10/21*

---

# What is the Cloud and why does everyone keep talking about it?

This blog post explains what the Cloud is without technical jargon: the problem it solved, why it changed how software is built, when running your own servers still makes sense, and the costs that sales pitches tend to leave out. If you've ever heard someone say "it's on the cloud" and weren't quite sure what that meant, this post is for you.

I decided to write it after watching the same scene one too many times. A cloud vendor would walk into a meeting, give a slick pitch, and my bosses would walk out convinced that the Cloud would fix every problem we had. It won't. The Cloud is a powerful tool, but it's **not a silver bullet**, and in some cases it's the worse choice, especially financially.

## The problem the Cloud solved

Imagine you want to launch an online store. Not long ago, you would need to buy a powerful computer to act as a server and find a place with stable power to keep it running 24/7. You would also hire someone to fix it when it broke, and hope it could handle the load when too many people visited at once.

All of that was expensive, slow, and risky. If the server went down, so did your store.

Now imagine that instead of buying that computer, you **rent** it and pay only for the time you use it. If you need more capacity during a big sale, you scale up with a click, then scale back down when it's over. That's the Cloud.

## Cloud = renting computers over the internet

**Cloud computing** is the on-demand rental of computing resources (servers, storage, databases, networks) over the internet. The [NIST definition](https://csrc.nist.gov/pubs/sp/800/145/final), the one most people in the industry refer to, describes it as on-demand, self-service access to a shared pool of resources that can be provisioned and released quickly.

Behind the word "cloud" there are massive data centers spread around the world, packed with servers and owned by companies such as Amazon ([AWS](https://aws.amazon.com/what-is-cloud-computing/)), Google ([GCP](https://cloud.google.com/learn/what-is-cloud-computing)), and Microsoft ([Azure](https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-cloud-computing)). You access them over the internet, use what you need, and pay for what you consume, much like your electricity bill.

**Pay-as-you-go** is the pricing model behind that comparison: you are billed for the capacity you actually used, by the hour, second, or request, instead of paying for hardware upfront. That means a small startup can use the same infrastructure as a giant corporation without investing millions in hardware first.

## Why it matters

Before the Cloud, only large companies could afford robust infrastructure. Today, anyone with a credit card can have a server running anywhere in the world in a few minutes.

That changed how products are built. New products reach the market much faster, because you don't need to buy hardware just to test an idea. If the product takes off, the infrastructure grows with it, and the provider has entire teams keeping the data centers running.

You already use the Cloud every day. For example, watching a movie on Netflix, listening to music on Spotify, or backing up your photos on Google Photos all run on it. None of those companies keeps a server in your house. Your data lives in their data centers, and you reach it over the internet.

| Before the Cloud | With the Cloud |
|---|---|
| Buy expensive servers | Rent what you need |
| Months to get something running | Minutes |
| Pay even when idle | Pay for what you use |
| Large team to maintain hardware | Focus on the product |
| Downtime if your only server fails | Capacity spread across data centers |

## Companies that don't use the Cloud

**On-premises infrastructure** (or "on-prem") is the alternative: a company keeps its own physical servers, either in a rented data center or in its own building.

That's not necessarily wrong. Sometimes it makes more sense, such as when strict regulations control where data can be stored, or when usage is so predictable and constant that buying is cheaper than renting. The Cloud fits best when you need flexibility and the ability to scale quickly.

## The part the vendors won't tell you

The sales pitches tend to skip one fact: the Cloud can get expensive, sometimes much more expensive than running your own hardware.

Renting is great when usage goes up and down, or when you're still figuring things out. But if your workload is steady and runs 24/7 at the same capacity, you pay a premium every month for flexibility you aren't using. At that point, buying your own servers and paying them off over a few years can be far cheaper.

"Pay only for what you use" cuts both ways. If nobody actively manages what's running, the bills creep up: forgotten resources, oversized machines, and data transfer costs that nobody noticed until the invoice arrived. Even inside one provider, an infrastructure choice can change the bill a lot. I wrote about one of those trade-offs in [running OpenSearch on EC2 Instance Store](/blog/2026/2026-11-08-opensearch-hot-instance-store.md) instead of EBS.

The Cloud also isn't automatically more secure, and migrating to it isn't free. Moving an existing system takes real expertise, and doing it badly can cost more than staying put.

None of this makes the Cloud bad. It's a tool, not a cure-all. Don't ask whether the Cloud will fix everything. Ask what problem you are trying to solve, and whether the Cloud is the best and most affordable way to solve it.

## Key Takeaways

- The Cloud is computing infrastructure offered as a service: you rent servers, storage, and networks over the internet instead of buying them.
- AWS, Google Cloud, and Azure run the data centers. You pay for what you consume, much like electricity.
- It lowered the cost of starting something new, which is why small teams can now build products that reach millions of people.
- On-premises infrastructure still makes sense for strict data regulations or steady, predictable workloads.
- Steady 24/7 workloads can cost more in the Cloud than on hardware you own, and unmanaged resources make bills grow quickly.
- Before you move, know what problem you're solving and check that the Cloud is the best and most affordable way to solve it.

## References

- [The NIST Definition of Cloud Computing (NIST SP 800-145)](https://csrc.nist.gov/pubs/sp/800/145/final)
- [What is cloud computing? (AWS)](https://aws.amazon.com/what-is-cloud-computing/)
- [What is cloud computing? (Google Cloud)](https://cloud.google.com/learn/what-is-cloud-computing)
- [What is cloud computing? (Microsoft Azure)](https://azure.microsoft.com/en-us/resources/cloud-computing-dictionary/what-is-cloud-computing)

*I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "What is the Cloud and why does everyone keep talking about it?",
      "description": "A plain-language explanation of cloud computing: what it is, the problem it solved, when on-premises infrastructure still makes sense, and the costs that vendor pitches tend to skip.",
      "datePublished": "2023-10-21",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2023/2023-10-21-cloud-concepts/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2023/2023-10-21-cloud-concepts/",
      "keywords": ["cloud computing", "AWS", "Google Cloud", "Azure", "on-premises"],
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
        {"@type": "ListItem", "position": 3, "name": "What is the Cloud and why does everyone keep talking about it?"}
      ]
    }
  ]
}
</script>
```

---
tags: network, tcp, aws
date: "2025-10-29"
category: Cloud
---

*__Blog Post Publish Date:__ 2025/10/29*

---

# TCP Ephemeral Ports: How a Single Client Keeps Many Connections Alive

This blog post explains what TCP ephemeral ports are, how TCP uses them to route responses back to the right place, and why they matter when you configure firewalls. I will also cover the difference between stateful and stateless devices and how AWS Security Groups fit into this picture.

## Why I Wrote This

I got curious about ephemeral ports while debugging a connectivity issue on AWS. An instance could reach an external service, but I kept second-guessing my Security Group rules. Did I need an inbound rule for the response traffic? Did I need to open the high port range? The answer turned out to be simpler than I feared, and understanding ephemeral ports was the piece I was missing. This post is the explanation I wish I had read first.

## What is an Ephemeral Port?

Ephemeral ports are temporary ports, usually with high numbers (for example, `49152` to `65535`), that clients use to initiate TCP connections. They let the same host keep multiple simultaneous connections to the same server without conflicts. When you open an SFTP session, the server listens on port `22`, while your client talks back using a local ephemeral port.

At the TCP level, each packet carries a source IP and port (from the client) and a destination IP and port (to the server). That is why the server "sees" the client's ephemeral port and can respond directly to it. The port information in the headers makes sure responses reach the correct socket on the client.

So the server does not need to guess or remember anything special. The client's ephemeral port travels in every packet, and the server simply swaps source and destination to reply.

## Stateful vs Stateless

The difference between stateful and stateless devices is where firewall rules get tricky.

A __stateful__ device tracks the state of open connections and automatically allows the return traffic that belongs to a session. A __stateless__ device analyzes each packet in isolation. It needs explicit rules for inbound and outbound traffic, and it will not infer that a response belongs to a connection you started internally.

The practical consequence shows up in how many rules you write. With a stateless device, if you allow an outbound request, you also have to write an inbound rule for the response, usually targeting the whole ephemeral port range. With a stateful device, you do not.

## AWS Security Groups

In AWS, Security Groups are stateful virtual firewalls applied at the instance level. They have inbound rules (who can initiate connections to the instance) and outbound rules (where the instance can initiate connections to).

Because they are stateful, Security Groups do not need duplicate rules to allow responses. If the instance initiates an outbound connection, the related response traffic is allowed automatically. You still need inbound rules to control which sources can initiate connections with the instance.

This answers the question I had when I started: no, you do not open the ephemeral port range for return traffic. The Security Group already tracks the connection and lets the response back in.

:::{note}
A common gotcha: Network ACLs in AWS are __stateless__. If you use NACLs alongside Security Groups, you do have to allow the ephemeral port range on the return path, because the NACL does not track connection state like the Security Group does.
:::

## Conclusion (Author Opinion)

Ephemeral ports used to feel like a black box to me, and they are the reason stateful firewalls are so convenient. Once I understood that the client's port travels in every TCP header, the behavior of Security Groups finally made sense: the response is allowed because the firewall remembers the connection, not because I opened a port for it.

If you work with AWS, I recommend keeping the stateful behavior of Security Groups and the stateless behavior of NACLs clear in your head. That single distinction has saved me from writing rules I did not need, and from forgetting rules I actually did.

## References

- IANA ephemeral port range: <https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml>
- AWS Security Groups: <https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html>
- AWS Network ACLs: <https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html>

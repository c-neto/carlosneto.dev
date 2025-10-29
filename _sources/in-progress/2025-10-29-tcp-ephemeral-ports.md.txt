---
tags: fluentbit, logs, observability
date: "2025-06-22"
category: Log Analytics
---

*__Blog Post Publish Date:__ 2025/06/22*

---

# TCP Ephemeral Ports

## What is?

Ephemeral ports are temporary ports, typically with high numbers (e.g., 49152–65535), that clients use to initiate TCP connections. They allow the same host to maintain multiple simultaneous connections with the same server without identification conflicts — for example, when opening an SFTP session, the server listens on port 22, while the client communicates using a local ephemeral port.

At the TCP level, each packet carries source IP and port (from client) and destination IP and port (to server). This is why the server "sees" the client's ephemeral port and can respond directly to it: the port information in the headers ensures responses reach the correct socket on the client.

## Firewall Statefulset vs Stateless

The distinction between stateful and stateless devices is important when discussing firewalls and network rules. A stateful device tracks the state of open connections and automatically allows return traffic associated with that session. A stateless device analyzes each packet in isolation and requires explicit rules for inbound and outbound traffic, without automatically inferring that a response belongs to an internally initiated connection.

## AWS Security Group

In AWS, Security Groups function as stateful virtual firewalls applied at the instance level. They have inbound rules (who can initiate connections to the instance) and outbound rules (where the instance can initiate connections to). Being stateful, Security Groups don't need duplicate rules to allow responses: if the instance initiates an outbound connection, related response traffic is automatically allowed, while inbound rules remain necessary to control which sources can initiate connections with the instance.

In summary, ephemeral ports are the mechanism that enables multiple client connections, TCP carries ports in its packets for correct response routing, and stateful firewalls like Security Groups simplify configuration by allowing return traffic without explicit rules in both directions — while maintaining control over who initiates connections and where instances can connect to.

## Summary

Summary of Ephemeral Ports, TCP Connections, and Security Groups:

1. Ephemeral Ports
- Are temporary, high-numbered ports (e.g., 49152–65535) used by clients to initiate TCP connections
- Allow distinction between multiple simultaneous connections from the same IP
- Example: when opening an SFTP connection (SSH on server port 22), the client uses a local ephemeral port to communicate

2. How Does the Server "Know" the Client's Port?
- In TCP protocol, each packet carries:
- Source IP and port (client)
- Destination IP and port (server)
- The server sees the client's ephemeral port and responds directly to it, ensuring proper communication

3. Stateful vs Stateless
- Stateful: device (firewall, Security Group) tracks connection states and automatically allows response traffic
- Stateless: device analyzes each packet in isolation and needs explicit rules for inbound and outbound traffic

4. Security Groups in AWS
- Is a stateful virtual firewall, applied at instance level
- Has Inbound and Outbound rules:
- Inbound defines who can initiate connection to the instance
- Outbound defines where the instance can initiate connection to
- Being stateful, SG automatically allows response traffic, even without explicit reverse rules

5. Why do SGs have inbound and outbound rules if they're stateful?
- To control who can initiate connections to the instance (inbound)
- To control where the instance can initiate connections to (outbound)
- SG facilitates granular control and security while automatically allowing packet returns


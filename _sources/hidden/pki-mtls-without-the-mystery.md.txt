---
tags: security, cryptography, mtls, tls, zero-trust
date: ""
category: Security
---

*__Blog Post Publish Date:__ *

---

# mTLS Without the Mystery: When Both Sides Prove Who They Are

This blog post explains what mutual TLS (mTLS) is, how it differs from regular TLS, and why it matters. It covers the "only the server proves itself" gap in normal TLS, how mTLS closes it by making the client present a certificate too, where mTLS is actually used (service-to-service communication, zero-trust networks, APIs, service meshes), the trade-offs that come with it, and a hands-on with `openssl` and `curl` so you can set up both sides yourself. If you understand regular TLS, you already understand most of mTLS.

I wrote this as a follow-up to my posts on digital certificates and TLS. If the chain of trust and the handshake already make sense to you, this is a short and satisfying next step.

## The Gap in Regular TLS

Think about what happens when you open a normal HTTPS site. Your browser checks the server's certificate and confirms the server is who it claims to be. But the server has no idea who __you__ are. Anyone on the internet can open that connection. The server authenticates to the client, and the client stays anonymous.

For a public website, that is exactly what you want. You should not need a certificate to read a blog. The server handles "who are you?" with a login form, a password, a token, something at the application layer.

But flip the scenario. Imagine two backend services talking to each other inside your infrastructure, or a client hitting a sensitive internal API. Now "anyone can connect, we will figure out who they are later" is a weak starting point. You would rather the connection itself refuse to open unless the caller can cryptographically prove its identity. That is the gap regular TLS leaves open, and it is the gap mTLS fills.

## What mTLS Actually Changes

mTLS stands for __mutual TLS__. The word that matters is _mutual_. In regular TLS, one side proves its identity. In mTLS, __both__ sides do.

The mechanics are the same ones you already know. During the handshake, after the server sends its certificate, the server also asks the client for a certificate. The client presents its own certificate, signed by a CA the server trusts, and the server verifies it the same way a browser verifies a server: name, dates, revocation, and chain up to a trusted root. If the client cannot present a valid, trusted certificate, the connection never completes.

So mTLS is regular TLS with one extra requirement switched on: client authentication. You get the same confidentiality and integrity as always, plus authenticity in __both__ directions instead of one.

:::{note}
The trust can use two separate roots. The client verifies the server against one set of trusted CAs, and the server verifies the client against another (often a private, internal CA that issues certificates only to your own services). They do not have to share the same trust anchor.
:::

## Why mTLS Is Important

Here is where I will take a side, because this is the part that made mTLS click for me.

The big shift in modern security is __zero trust__. The old model assumed that anything inside the corporate network was safe, and the firewall at the edge was the wall that kept attackers out. That model is broken. Networks get breached, services run across clouds, and "inside the network" no longer means "trustworthy". Zero trust flips the assumption: trust nothing by default, and make every single connection prove itself, even between two services sitting in the same cluster.

mTLS is the concrete mechanism that makes zero trust real at the network layer. A few reasons it matters so much:

- __Strong identity, not just a shared secret__: an API key or a bearer token can leak, get logged, or get copied. A private key that never leaves the service is much harder to steal and misuse. The identity is cryptographic, tied to a certificate, not a string someone can paste.
- __The connection fails closed__: with mTLS, an unauthenticated caller cannot even complete the handshake. You are rejecting bad actors before any application logic runs, not after.
- __Both directions are protected__: the client knows it reached the real server, and the server knows the client is a legitimate, enrolled service. Neither side is talking to an impostor.
- __It fits service-to-service traffic perfectly__: machines do not fill in login forms. Certificates are a natural way for services to authenticate each other automatically.

This is why mTLS shows up everywhere in modern infrastructure: __service meshes__ like Istio and Linkerd turn it on automatically between pods, __Kubernetes__ components use it internally, and __zero-trust__ platforms lean on it as the default. When you hear "the mesh gives you mTLS for free", this is what it means: every service got a certificate, and every connection between them is now mutually authenticated.

## The Trade-Offs (Because There Always Are Some)

mTLS is great, but it is not free, and I would be dishonest to pretend otherwise.

The real cost is __certificate management__. Now every client needs a certificate, not just every server. That means you have to issue those certificates, distribute them, rotate them before they expire, and revoke them when a service is retired or compromised. Multiply that across hundreds of services and short certificate lifetimes, and manual management becomes impossible fast. This is exactly why people reach for automation (a service mesh, SPIFFE/SPIRE, or an internal CA with short-lived certificates) instead of hand-rolling it.

There is also operational pain when things go wrong. A plain TLS failure usually means "fix the server certificate". An mTLS failure can mean the server certificate, the client certificate, or a trust mismatch on either side, so debugging has more places to look. And for a public-facing website, mTLS is simply the wrong tool. Do not ask random visitors to install a client certificate to read your content.

My rule of thumb: mTLS is excellent for machine-to-machine and internal traffic where you control both ends. It is a poor fit for open, public, human-facing services.

## Hands-On: mTLS With openssl and curl

Let me make this concrete. The following builds a tiny private CA, issues a client certificate from it, and then forces a server to require that client certificate. You can run it on any machine with `openssl` and `curl`.

First, create a private CA and a client certificate signed by it:

```{code-block} bash
:caption: $ build a private CA and issue a client certificate

# 1. create the CA private key and a self-signed CA certificate
openssl genrsa -out ca.key 4096
openssl req -x509 -new -key ca.key -days 3650 -subj "/CN=My Internal CA" -out ca.crt

# 2. create the client private key and a certificate signing request (CSR)
openssl genrsa -out client.key 2048
openssl req -new -key client.key -subj "/CN=my-service-client" -out client.csr

# 3. sign the client CSR with the CA to produce the client certificate
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 365 -out client.crt
```

Now stand up a test server that __requires__ a client certificate. The `-Verify` flag is what turns plain TLS into mTLS, because it tells the server to demand and validate a client certificate against the CA:

```{code-block} bash
:caption: $ run an openssl test server that requires client auth

# generate a quick server certificate (self-signed, for the lab only)
openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key \
  -subj "/CN=localhost" -days 365 -out server.crt

# start a TLS server that demands a client certificate signed by our CA
openssl s_server -accept 8443 -cert server.crt -key server.key \
  -CAfile ca.crt -Verify 1
```

With the server running, compare the two calls from another terminal:

```{code-block} bash
:caption: $ a client without a certificate is rejected, one with it succeeds

# no client certificate: the handshake is refused
curl -k https://localhost:8443
# output expected: the server rejects the connection, no client certificate was presented

# with the client certificate and key: the handshake completes
curl -k --cert client.crt --key client.key https://localhost:8443
```

That contrast is the entire idea of mTLS in two commands. The first caller is anonymous and gets rejected at the connection layer, while the second caller proves its identity with a certificate the server trusts and is let in.

:::{note}
I keep a fuller version of this as a Docker Compose lab, with a real server and automatic certificate generation, in my labs repository: <i class="fab fa-github"></i> [c-neto/my-devops-labs](https://github.com/c-neto/my-devops-labs/). It is handy for experimenting without polluting your workstation with throwaway certificates.
:::

## Conclusion (Author Opinion)

mTLS used to sound like an advanced, enterprise-only thing to me, and it is not. Once you understand regular TLS, mTLS is the same handshake with client authentication turned on, so one side proving its identity becomes both sides proving their identity.

What I really appreciate about mTLS is that it moves identity down to the connection itself. A bad actor does not get to send a request and get rejected by my code, because the bad actor cannot even open the door. For service-to-service traffic, internal APIs, and anything built on zero-trust principles, that is a strong default, and I recommend it.

But I will keep the honesty I try to keep in every post: the certificate management overhead is real, and you should not adopt mTLS by hand across a big fleet. Lean on automation, a service mesh, or a proper internal CA. And do not force it onto a public, human-facing site. Used in the right place, mTLS is one of the cleanest security wins I know, and used in the wrong place it is just pain. Pick the right place, and give it a try.

## References

- <https://datatracker.ietf.org/doc/html/rfc8446>
- <https://www.cloudflare.com/learning/access-management/what-is-mutual-tls/>
- <https://spiffe.io/>
- <https://istio.io/latest/docs/concepts/security/>
- <https://www.openssl.org/docs/man3.0/man1/openssl-s_server.html>

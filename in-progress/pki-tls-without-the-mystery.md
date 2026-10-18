---
tags: security, cryptography, tls, https, openssl
date: ""
category: Security
---

*__Blog Post Publish Date:__ *

---

# TLS Without the Mystery: What It Is and Why It Exists

This blog post explains what TLS is, in plain language, and what it actually does for you beyond the padlock in your browser. It covers the three guarantees TLS gives (confidentiality, integrity, and authenticity), why "TLS equals encryption" is a common and wrong oversimplification, how the trust in a certificate is anchored in a root store, the difference between browser-level and system-level root stores (Firefox versus macOS, Windows, and Linux), and a small hands-on with `openssl` and `curl` so you can see it yourself. You do not need any cryptography background to read it.

If you already read my post on digital certificates, this is the natural next step. Certificates are the documents. TLS is the protocol that puts them to work every time you open an HTTPS site.

## TLS Is Not Just Encryption

Let me start with the misconception I see the most, because getting this wrong leads to bad security decisions.

It is wrong to think TLS is only about encrypting data. Yes, encryption matters, and TLS does it. But that is just one part of the job. TLS gives you three guarantees at once:

- __Confidentiality__: the data is encrypted, so someone sniffing the network sees gibberish instead of your password.
- __Integrity__: the data was not altered in transit. If a single byte is flipped on the way, the other side detects it and the connection breaks.
- __Authenticity__: you are really talking to the server you intended, not an impostor sitting in the middle.

That last one is the part people forget, and it is the one that does the heavy lifting. Encryption without authenticity is almost useless, because you could have a perfectly encrypted conversation with an attacker and never know it. You would just be encrypting your data with the attacker's key. TLS avoids this by making the server prove its identity with a certificate before any real data flows, so encryption keeps the conversation private and authenticity makes sure you are having it with the right party.

So whenever someone says "we use TLS, the data is encrypted", the fuller answer is "yes, and it is also checked for tampering and the server identity is verified".

## What TLS Actually Stands For

TLS means __Transport Layer Security__. It is the protocol that sits between your application (a browser, a mobile app, a backend service) and the raw network connection, and secures everything that passes through.

You have probably seen __SSL__ mentioned too. SSL (Secure Sockets Layer) is the old name. SSL is dead and insecure, and every version of it is deprecated. What runs today is TLS, but the name "SSL" stuck around in tool names and casual conversation. When someone says "SSL certificate", they almost always mean a TLS certificate. When your URL starts with `https://`, the `s` is TLS doing its work underneath HTTP.

## How a TLS Connection Starts: The Handshake

Before any page content moves, the client and server run a short negotiation called the __handshake__. I will keep it conceptual, because the details change between TLS versions, but the shape is always the same:

- __1__: The client says hello and lists which cryptographic options it supports.

- __2__: The server replies and sends its __certificate__, which contains its public key and its identity (for example `example.com`), signed by a Certificate Authority.

- __3__: The client verifies that certificate. It checks the name matches, the dates are valid, the certificate was not revoked, and, most importantly, that it chains up to a __root it already trusts__. This is the authenticity check.

- __4__: If the certificate checks out, both sides use asymmetric cryptography to agree on a temporary shared key, then switch to fast symmetric encryption for the actual data.

The expensive, careful part happens once, at the start. After the handshake, the connection is just fast symmetric encryption with integrity protection on every message. You get the safety of asymmetric crypto and the speed of symmetric crypto in the same connection.

:::{note}
If you want the deeper story of how certificates, public and private keys, and the chain of trust work, I cover all of it in my post on digital certificates. This post assumes that foundation and focuses on what TLS does with it.
:::

## Where Does the Trust Come From? Root Stores

Step 3 above hides the whole magic of TLS: "a root it already trusts". Your browser has never met `example.com`, so why does it accept the certificate that site presents?

Because trust is delegated down a chain that ends at a __Root Certificate Authority (CA)__. The site's certificate is signed by an intermediate CA, which is signed by a root CA. If your machine trusts that root, the trust flows all the way down to the site.

So the real question becomes: which roots does your machine trust? That list of trusted root certificates is called a __trust store__ (or root store). And here is the part that confuses a lot of people, because there is not one single store.

### System-Level Trust Stores

Most of the time, the trust store belongs to the operating system, and every application on the machine shares it:

- __macOS__: the trusted roots live in the system __Keychain__. You can open the Keychain Access app and look at the "System Roots" to see Apple's curated list. Safari, `curl`, and most native apps rely on it.
- __Windows__: roots live in the __Windows Certificate Store__, managed by Microsoft and viewable through the `certmgr.msc` tool. Edge, Chrome on Windows, and most Windows software trust it.
- __Linux__: there is no single vendor, so distributions ship a package (commonly `ca-certificates`) that drops the root bundle into a path like `/etc/ssl/certs`. Tools like `curl`, `wget`, and `openssl` read from there.

When you install a corporate laptop and your company's proxy "just works" with HTTPS, it is usually because IT pushed a custom root into this system store.

### The Firefox Exception: Its Own Root Store

Now the interesting case, and the reason I wanted to write this section. __Firefox does not use the operating system trust store by default.__ It ships and maintains its __own__ internal list of trusted root CAs, at the browser level, independent of the machine it runs on.

Mozilla runs its own CA program and bundles that root list inside Firefox itself. This has a real, practical consequence that bites people:

- A certificate that works perfectly in Safari or Edge, because its root is in the macOS or Windows store, can fail in Firefox if that root is not in Mozilla's list.
- The opposite happens too. A root you manually added to your operating system is not automatically trusted by Firefox, because Firefox is not looking at the system store.

:::{note}
Firefox has a setting, `security.enterprise_roots.enabled`, that can tell it to also import roots from the operating system store. It is often turned on in corporate environments precisely so that company-issued roots work in Firefox like they do everywhere else. But the default behavior is Firefox trusting only its own list.
:::

So "is this certificate trusted?" does not have one global answer on your machine. It depends on which store the application consults. Chrome and Safari lean on the system store. Firefox brings its own. This is exactly why the same site can show a padlock in one browser and a warning in another.

### Who Decides Which Roots Are Trustworthy

None of these lists are random. The big players (Apple, Microsoft, Google, Mozilla) each run a root program with strict rules a CA must follow to be included, and they coordinate through an industry group called the __CA/Browser Forum__. When you install an operating system or a browser, you are implicitly trusting whoever curates that list. Everything else in TLS is derived from that one decision.

## Hands-On: See TLS For Yourself

Enough theory. You can inspect all of this with tools you probably already have. Here are a few commands I actually use.

Inspect the certificate a server presents, straight from the handshake:

```{code-block} bash
:caption: $ inspect a live server certificate with openssl

# connect to the server and print the certificate chain it sends
openssl s_client -connect example.com:443 -servername example.com </dev/null

# show just the human-readable certificate details
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates
```

The `-subject` is who the certificate is for, `-issuer` is the CA that signed it, and `-dates` are the validity window. These are the exact fields the client checks during the handshake.

Now watch the authenticity check happen with `curl`:

```{code-block} bash
:caption: $ curl validates the chain against the trust store

# a normal request: curl verifies the chain against the system trust store
curl -v https://example.com

# force a failure to see the authenticity check reject a bad certificate
curl -v https://self-signed.badssl.com
# output expected: curl: (60) SSL certificate problem: self-signed certificate
```

That second command is the whole point of this post in one line. The data channel could be encrypted just fine, but `curl` refuses because the server cannot prove who it is, and TLS treats an unverified identity as a hard failure.

You can inspect which root bundle your tools are using too:

```{code-block} bash
:caption: $ find the system trust store on Linux

# the default CA bundle path on many Linux distributions
openssl version -d
ls /etc/ssl/certs | head
```

:::{note}
A full hands-on lab with a local CA, a server certificate, and `mTLS` is something I keep in my labs repository: <i class="fab fa-github"></i> [c-neto/my-devops-labs](https://github.com/c-neto/my-devops-labs/). If you want to reproduce the handshake end to end, that is the place.
:::

## Conclusion (Author Opinion)

For a long time I treated TLS as a synonym for encryption. Turn it on, see the padlock, move on. Understanding that TLS is really three guarantees, confidentiality, integrity, and authenticity, changed how I reason about security. The authenticity part is the one that does the heavy lifting, and it is the one most people ignore until a certificate error blocks them.

The root store detail is my other favorite takeaway, because it explains so many real-world headaches. The next time a site loads fine in Chrome but throws a warning only in Firefox, you will not be confused. Firefox is simply consulting its own list of trusted roots instead of the operating system's, and the root behind that certificate is missing from Mozilla's bundle. Once you know where trust is stored, those errors stop being mysterious and start being obvious.

My advice is to internalize one sentence: TLS does not just hide your data, it also proves who you are talking to. If you want to go one step further, the natural next topic is mutual TLS, where the client also presents a certificate and both sides authenticate each other. I cover that in a dedicated post.

## References

- <https://datatracker.ietf.org/doc/html/rfc8446>
- <https://wiki.mozilla.org/CA>
- <https://cabforum.org/>
- <https://ssl-config.mozilla.org/>
- <https://badssl.com/>

---
tags: security, cryptography, tls, diffie-hellman, rsa
date: ""
category: Security
---

*__Blog Post Publish Date:__ *

---

# TLS Key Exchange Without the Mystery: Diffie-Hellman vs RSA

This blog post explains how two computers that have never met agree on a secret key over a network everyone can watch. It covers the problem key exchange solves, how the old RSA key exchange worked and why it was retired, how Diffie-Hellman lets both sides build the same secret without ever sending it, what forward secrecy means and why it is the whole point, and a small hands-on with `openssl` so you can see which key exchange your connections actually use. I will lean on a paint-mixing analogy, so you do not need any math background to follow it.

This is a follow-up to my posts on digital certificates and TLS. In the TLS post I said step 4 of the handshake is "both sides agree on a temporary shared key" and left it there. This post opens that box. If the handshake already makes sense to you, this fills in the one piece I skipped.

## The Problem: Agreeing on a Secret in Public

Symmetric encryption is fast, and TLS uses it for the actual data. But symmetric encryption has one requirement that sounds impossible: both sides need the same secret key. The server has it, the client needs it, and the only path between them is a network where anyone can be listening.

So how do you send the key to the other side without the eavesdropper copying it on the way? If you just transmit it, you have handed your secret to everyone sniffing the wire. This is the key exchange problem, and for a long time it felt like a chicken-and-egg trap. You need a secure channel to share the key, but you need the key to have a secure channel.

There are two classic ways TLS solved this. One is clever but flawed. The other feels like magic the first time you get it.

## The Old Way: RSA Key Exchange

The first approach TLS used leaned on the server's certificate. Remember that the certificate carries the server's __public key__, and asymmetric cryptography means anything encrypted with the public key can only be decrypted with the matching private key.

So the RSA key exchange went like this:

- __1__: The client generates a random secret (the material for the symmetric key).

- __2__: The client encrypts that secret with the server's public key, taken from the certificate.

- __3__: The client sends the encrypted blob across the network. Anyone watching sees it, but only the server's private key can open it.

- __4__: The server decrypts it with its private key. Now both sides share the secret, and nobody in the middle could read it.

This works, and for years it was everywhere. But it has a flaw that eventually got it removed from modern TLS, and the flaw is worth understanding because it leads straight to the reason Diffie-Hellman won.

### Why RSA Key Exchange Was Retired

The secret only ever traveled in one form: encrypted with the server's public key. That sounds safe, until you ask one question. What happens the day the server's private key leaks?

Imagine an attacker who has been patient. They cannot read your traffic today, so they just record all of it and store it. Encrypted blobs, year after year. Then, someday, the server's private key is stolen, through a breach, a bug like Heartbleed, a subpoena, whatever. With that one private key, the attacker goes back and decrypts __every__ recorded session, because every one of them shipped its secret encrypted with the matching public key.

One stolen key unlocks the entire history, and that is the problem. The security of every past conversation depends on a long-lived private key staying secret forever, and "forever" is not a guarantee anyone can make.

This attack even has a name people use now: __harvest now, decrypt later__. RSA key exchange is exactly the scenario it preys on.

## The New Way: Diffie-Hellman

Diffie-Hellman solves the same problem from a completely different angle. Instead of one side creating the secret and shipping it to the other, __both sides build the same secret together__, and the secret itself is never sent across the network. Not encrypted, not in any form. It simply never travels.

The first time I understood this, it genuinely felt like a trick. The clearest way I know to explain it is with paint.

### The Paint Mixing Analogy

Picture two people, Alice and Bob, who want to end up with the same secret color of paint. They can shout across a room full of eavesdroppers, but anything they say out loud is public.

- __1__: They publicly agree on a __shared base color__, say yellow. Everyone in the room hears this. It is not a secret.

- __2__: Alice picks a __private color__ and keeps it to herself, say red. Bob picks his own private color, say blue. Neither one tells anyone.

- __3__: Each mixes their private color into the public yellow. Alice makes orange (yellow + red), Bob makes green (yellow + blue). They shout these mixtures across the room. The eavesdroppers now hear "orange" and "green".

- __4__: Alice takes Bob's green and mixes in her own private red. Bob takes Alice's orange and mixes in his own private blue. Both end up with the exact same muddy color: yellow + red + blue.

The eavesdroppers heard yellow, orange, and green, but they cannot reproduce the final color. To get there they would need to un-mix orange back into its ingredients to recover Alice's red, and separating mixed paint into its original colors is the hard part. Mixing is easy, un-mixing is practically impossible. That gap is the whole security.

In real Diffie-Hellman the "colors" are numbers and the "mixing" is modular exponentiation, a math operation that is easy to do forward and brutally hard to reverse. But the shape is exactly the paint. Both sides derive the same secret, and the secret never once crosses the wire.

:::{note}
Diffie-Hellman handles the key exchange, but on its own it does not tell you __who__ you are mixing paint with. An attacker in the middle could run the exchange with each side separately. That is why TLS still uses the server's certificate to authenticate the server during the handshake. Diffie-Hellman agrees on the key, the certificate proves identity. I cover the identity side in my TLS and digital certificates posts.
:::

### Why Diffie-Hellman Gives Forward Secrecy

Now bring back the patient attacker who records everything. In modern TLS, the private colors Alice and Bob pick are __fresh and temporary__, generated for that one connection and thrown away the moment it ends. This variant is called __ephemeral__ Diffie-Hellman, which is why you see it written as __DHE__ or __ECDHE__ (the E is for ephemeral).

Because the secret for each session was built from throwaway private values that no longer exist, stealing the server's long-lived private key later gets the attacker nothing. That private key was used to __sign__ the handshake and prove identity, but it was never used to derive the session secret. There is no master key sitting around that unlocks the recorded history.

This property is called __forward secrecy__ (or perfect forward secrecy). Each session is its own island. Crack one, and you have exactly one session, not the archive. This single property is why the entire industry moved off RSA key exchange, and why TLS 1.3 removed it completely and only allows ephemeral Diffie-Hellman.

## RSA vs Diffie-Hellman Side by Side

To make the difference concrete:

- __RSA key exchange__: one side creates the secret and sends it encrypted with the server's public key. Simple, but if the server's private key ever leaks, every recorded past session can be decrypted. No forward secrecy.

- __Diffie-Hellman (ephemeral)__: both sides build the same secret together, and the secret never travels. The per-session private values are discarded immediately, so a leaked long-term key does not expose past sessions. Forward secrecy by design.

One more thing worth clearing up, because the naming confuses people. RSA shows up in two different jobs, and TLS 1.3 only retired one of them. The __RSA key exchange__ is gone. But an __RSA certificate__, where the server's RSA key is used to sign the handshake and prove identity, is still perfectly fine. So a modern connection can and often does use an RSA certificate for authentication while using ECDHE for the key exchange. RSA the key exchange is dead. RSA the signature is alive and well.

## Hands-On: See Your Key Exchange

Enough theory. You can see exactly which key exchange a connection negotiated, with tools you already have.

Connect to a server and look at the negotiated cipher and key exchange:

```{code-block} bash
:caption: $ inspect the negotiated key exchange with openssl

# connect and let the handshake complete, then read the details
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | grep -iE "protocol|cipher"
```

On a modern server you will see a TLS 1.3 protocol and a cipher like `TLS_AES_256_GCM_SHA384`. TLS 1.3 does not even print the key exchange in the cipher name anymore, because it is __always__ ephemeral Diffie-Hellman. There is no other option left.

On TLS 1.2 the key exchange is visible right in the cipher name, so you can tell the two approaches apart at a glance:

```{code-block} bash
:caption: $ the key exchange is written into the TLS 1.2 cipher name

# ECDHE at the front means ephemeral Diffie-Hellman, so forward secrecy
# example: ECDHE-RSA-AES256-GCM-SHA384
#          ^^^^^ key exchange   ^^^ certificate signature

# a cipher that starts with TLS_RSA_... is the old RSA key exchange, no forward secrecy
```

Read that cipher name like a sentence. `ECDHE-RSA-AES256-GCM-SHA384` means: use ephemeral elliptic-curve Diffie-Hellman for the key exchange, an RSA certificate to prove identity, and AES-256-GCM for the data. The `ECDHE` at the front is your forward secrecy. A name that starts with plain `RSA` for the exchange is the old, retired approach.

You can also list which key exchanges your local OpenSSL supports:

```{code-block} bash
:caption: $ list ciphers that provide forward secrecy

# ECDHE and DHE ciphers are the ones with forward secrecy
openssl ciphers -v 'ECDHE:DHE' | head
```

:::{note}
A full hands-on lab with a local CA, a server certificate, and the handshake end to end lives in my labs repository: <i class="fab fa-github"></i> [c-neto/my-devops-labs](https://github.com/c-neto/my-devops-labs/). If you want to reproduce a connection and watch the key exchange yourself, that is the place.
:::

## Conclusion (Author Opinion)

For a long time, "how do two strangers agree on a secret key in public" was the one part of TLS I accepted on faith and never really understood. The paint analogy was what finally made it click for me, and I keep coming back to it because it is honest: mixing is easy, un-mixing is not, and that asymmetry is the entire trick.

The takeaway I care about most is forward secrecy. RSA key exchange was clever, but tying the safety of every past conversation to one long-lived private key was a time bomb, and "harvest now, decrypt later" is not a hypothetical. Diffie-Hellman defused it by never sending the secret at all and throwing away the per-session values the moment the connection closes. That is why TLS 1.3 made it the only option, and I think that was the right call.

If I had to compress this whole post into one sentence: RSA key exchange ships the secret and hopes the key never leaks, Diffie-Hellman builds the secret on both sides so there is nothing to leak. Once you see that difference, the move the whole industry made stops looking like a detail and starts looking obvious.

## References

- <https://datatracker.ietf.org/doc/html/rfc8446>
- <https://en.wikipedia.org/wiki/Diffie%E2%80%93Hellman_key_exchange>
- <https://en.wikipedia.org/wiki/Forward_secrecy>
- <https://ssl-config.mozilla.org/>

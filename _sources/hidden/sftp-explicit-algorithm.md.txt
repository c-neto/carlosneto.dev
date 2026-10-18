---
tags: sftp, ssh, linux
date: "2026-10-17"
category: Linux
---

*__Blog Post Publish Date:__ 2026/10/17*

---

# SFTP: How to Explicitly Set the Algorithm in a Connection

I hit a confusing SFTP error where the log pointed me in the wrong direction. The real cause was the key algorithm, not the key itself. This blog post explains how to diagnose that case and how to explicitly set the algorithm on the client side so the connection goes through.

## The Problem: a Misleading Error

Depending on how the SFTP server is configured, you sometimes have to explicitly tell the client which algorithm to use for the connection. When this is the issue, the log message is confusing and does not clearly point at the algorithm as the cause.

Here is a real example. The connection fails with a permission error:

```bash
$ sftp -i pk.pem -oPort=10122 mftTRSYs@mft-test.53.com

mftTRSYs@mft-test.53.com: Permission denied (publickey).
Connection closed
```

At first glance, `Permission denied (publickey)` looks like a problem with the key, so you go check the key, the permissions, the user, and everything except the real cause. Recent OpenSSH clients disable older algorithms by default, and the server on the other side still expects one of them.

## Listing the Supported Algorithms

Before guessing, ask the server which key algorithms it supports. The `ssh -Q key` command lists them:

```bash
$ ssh -Q key mftTRSYs@mft-test.53.com

ssh-ed25519
ssh-ed25519-cert-v01@openssh.com
sk-ssh-ed25519@openssh.com
sk-ssh-ed25519-cert-v01@openssh.com
ecdsa-sha2-nistp256
ecdsa-sha2-nistp256-cert-v01@openssh.com
ecdsa-sha2-nistp384
ecdsa-sha2-nistp384-cert-v01@openssh.com
ecdsa-sha2-nistp521
ecdsa-sha2-nistp521-cert-v01@openssh.com
sk-ecdsa-sha2-nistp256@openssh.com
sk-ecdsa-sha2-nistp256-cert-v01@openssh.com
ssh-dss
ssh-dss-cert-v01@openssh.com
ssh-rsa
ssh-rsa-cert-v01@openssh.com
```

Notice `ssh-rsa` at the bottom. That is one of the older algorithms recent OpenSSH versions no longer enable by default, and it is the one this server needs.

## The Fix: Explicitly Set the Algorithm

Now pick the algorithm and set it explicitly on the client side. You do this with the `HostKeyAlgorithms` and `PubkeyAcceptedKeyTypes` options, using the `+` prefix to add the algorithm back to the accepted list:

```bash
$ sftp -i pk.pem \
    -o HostKeyAlgorithms=+ssh-rsa \
    -o PubkeyAcceptedKeyTypes=+ssh-rsa \
    -o Port=10122 \
    mftTRSYs@mft-test.53.com

Connected to mft-test.53.com.
sftp>
```

The connection goes through. The `+` is the important detail: it appends `ssh-rsa` to the default set instead of replacing it, so you re-enable the old algorithm without losing the modern ones.

## Conclusion (Author Opinion)

This is one of those small traps that costs you more time than it should, because the error message sends you looking in the wrong place. The lesson I took from it: when an SFTP connection fails with a vague `publickey` error and the key is fine, check the algorithms with `ssh -Q key` before assuming anything. Setting `HostKeyAlgorithms` and `PubkeyAcceptedKeyTypes` explicitly is a quick fix once you know that is the problem. I keep this one in my notes, and now it is here too.

## References

- https://man.openbsd.org/sftp
- https://man.openbsd.org/ssh_config

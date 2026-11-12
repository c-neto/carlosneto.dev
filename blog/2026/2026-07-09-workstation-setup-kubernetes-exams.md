---
tags: kubernetes, certification, terminal
date: "2026-07-09"
category: Kubernetes
author: Carlos Neto
title: "Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)"
description: "The workstation tweaks I use to save time in the CKA, CKAD, and CKS exams: macOS keyboard and shortcut settings, Bash history search by prefix, a minimal vimrc, kubectl aliases, and how to copy them to each question node."
myst:
  html_meta:
    description: "The workstation tweaks I use to save time in the CKA, CKAD, and CKS exams: macOS keyboard and shortcut settings, Bash history search by prefix, a minimal vimrc, kubectl aliases, and how to copy them to each question node."
og:title: "Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)"
og:description: "The workstation tweaks I use to save time in the CKA, CKAD, and CKS exams: macOS keyboard and shortcut settings, Bash history search by prefix, a minimal vimrc, kubectl aliases, and how to copy them to each question node."
---

*__Blog Post Publish Date:__ 2026/07/09*

---

# Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)

This blog post covers the workstation tweaks I use to work faster during the Linux Foundation Kubernetes exams: macOS settings that avoid keyboard and proctoring problems, Bash history search by prefix, a minimal Vim configuration, kubectl aliases, and how to copy all of it to each question node.

Time management is one of the most important factors for passing these exams. The CKA, CKAD, and CKS are hands-on exams that run on remote Ubuntu instances with the XFCE desktop, where network latency and the remote desktop slow you down. Every keystroke you save adds up.

## Configure the U.S. Keyboard Layout (MacBooks)

If you take the exam on a MacBook, set your keyboard layout to `U.S.`. Otherwise, the remote Linux environment may not recognize some characters correctly, especially `~` and `` ` ``. This is a common problem with layouts such as `U.S. International - PC` and `Brazilian ABNT2`.

Before the exam:

1. Open *__System Settings » Keyboard » Input Sources__*.
2. Add the `U.S.` input source.
3. Remove all other input sources, so only `U.S.` remains.

## Disable Mission Control Shortcuts (MacBooks)

By default, __CTRL + ←→__ switches between macOS Spaces. During the exam, the proctor can see that as leaving the exam environment, which may trigger a warning or even interrupt your session.

Before the exam:

1. Open *__System Settings » Keyboard » Keyboard Shortcuts__*.
2. Select *__Mission Control__*.
3. Disable every shortcut under *__Mission Control__*.

That prevents accidental desktop switches and the risk of a proctor alert or a suspension on suspicion of consulting unauthorized material.

## Disable Window Tiling Apps (MacBooks)

If you use a window tiling app such as [Rectangle](https://rectangleapp.com/) or [Magnet](https://magnet.crowdcafe.com/), close it before the exam. Its keyboard shortcuts can conflict with the exam workstation and cause unexpected behavior with shortcuts such as __⌘ + ↑↓←→__.

## History Search by Prefix

__This is my most valuable tip.__

The exam environment uses __Bash__, and Bash relies on the [GNU Readline](https://tiswww.case.edu/php/chet/readline/readline.html) library for command-line editing, key bindings, and history navigation. For example, the reverse search on __CTRL + R__ comes from Readline. I explain how Readline works in more depth in [GNU Readline: The Magic Behind Terminal Autocomplete](/blog/2026/2026-10-18-gnu-readline-foundation.md).

**History search by prefix** is a Readline feature, disabled by default, that searches your history using the text already typed before the cursor. The [history-search-backward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029) and [history-search-forward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dforward-_0028_0029) functions implement it, instead of simply moving to the previous or next command.

For example, imagine your command history contains:

```bash
kubectl get pods
kubectl get nodes
kubectl describe pod nginx
helm list
```

If you type:

```bash
kubectl g
```

and press __↑__, `history-search-backward` cycles only through commands that start with `kubectl g`:

```bash
kubectl get nodes
kubectl get pods
```

`kubectl describe pod nginx` and `helm list` are skipped because they don't match the prefix. That's much faster than the default __↑__, which walks through every command, and often more convenient than pressing __CTRL + R__ repeatedly.

To enable it, create `~/.inputrc` with this configuration:

```{code-block} bash
:caption: ~/.inputrc
# ↑ (previous matching command)
"\e[A": history-search-backward
# ↓ (next matching command)
"\e[B": history-search-forward
```

Bash reads this file when a new session starts. To load changes in the current session, run:

```bash
bind -f ~/.inputrc
```

## Setting Up Vim

The exam workstation includes [VSCodium](https://vscodium.com/), but every task requires you to connect to a remote node over SSH, and VSCodium isn't available there. The workstation also often has high latency, which makes the mouse unreliable. This is where Vim shines.

These settings make editing Kubernetes YAML manifests much easier. Create `~/.vimrc` with:

```{code-block} vim
:caption: ~/.vimrc
set nu        " Show line numbers
set ai        " Preserve indentation while editing
set et        " Convert tabs into spaces
set ts=2      " Display tabs as two spaces
set sw=2      " Indent and unindent using two spaces
set sts=2     " Make Tab and Backspace use two-space indentation
set hls       " Highlight search matches
set cuc       " Highlight the current cursor column
syntax on     " Enable syntax highlighting
```

Avoid `set mouse=a`, because of the latency. Also, clipboard settings such as `clipboard+=unnamedplus,autoselect` don't work on the exam workstations.

> *I wrote a separate post, [Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)](/blog/2026/2026-07-15-vim-kubernetes-exams.md), with the editing techniques I use most during the exams.*

## kubectl Aliases and Shortcuts

Each remote question node already has a `~/.bashrc` with useful settings. A handy trick is to copy it to the main workstation, append your own aliases, and copy it back to the question nodes.

First, copy `~/.bashrc` from a question node:

```bash
scp cks1234:~/.bashrc ~/.bashrc
```

Then append these aliases to the end of the file:

```{code-block} bash
:caption: ~/.bashrc
### omitted the .bashrc copied from question node

alias kgp="kubectl get pods"

alias kaf="kubectl apply -f"
alias kdel="kubectl delete --now"
alias kdelp="kubectl delete pod --now"

alias kns="kubectl config set-context --current --namespace"
alias kctx="kubectl config use-context"

export x="--dry-run=client -oyaml"
```

> *__INFO:__ `export x` is a shorthand to generate YAML from imperative kubectl commands, such as `k run nginx --image nginx:latest $x > nginx.yaml`.*

I use the same style of aliases every day through the oh-my-zsh kubectl plugin, as I describe in [ZSH + Starship](/blog/2024/2024-02-08-starship-zsh.md).

## Copy the Settings to Each Question Node

Every task must be done on a remote question node over SSH. Create your configuration files once on the main workstation, then copy them to the question node before you start each task:

```bash
scp ~/.inputrc ~/.vimrc ~/.bashrc cks1234:~/
ssh cks1234
```

## Key Takeaways

- On a MacBook, use only the `U.S.` keyboard layout, disable Mission Control shortcuts, and close window tiling apps before the exam.
- Bind __↑__ and __↓__ to `history-search-backward` and `history-search-forward` in `~/.inputrc` to search history by prefix.
- Use Vim on the question nodes, with a small `~/.vimrc` for YAML: line numbers, auto-indent, and two-space tabs.
- Don't enable `set mouse=a` or clipboard settings. They don't help on the exam workstation.
- Copy the question node's `~/.bashrc`, append your kubectl aliases and `export x="--dry-run=client -oyaml"`, and copy everything back with `scp` before each task.

## References

- [GNU Readline: history-search-backward (Readline manual)](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029)
- [kubectl quick reference (Kubernetes)](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
- [kubectl commands (Kubernetes)](https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#-em-deployment-em-)
- [Options: cursorcolumn (Vim documentation)](https://vimdoc.sourceforge.net/htmldoc/options.html#'cursorcolumn')
- [Vim cheat sheet (vim.rtorr.com)](https://vim.rtorr.com/)

---

> *I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)",
      "description": "The workstation tweaks I use to save time in the CKA, CKAD, and CKS exams: macOS keyboard and shortcut settings, Bash history search by prefix, a minimal vimrc, kubectl aliases, and how to copy them to each question node.",
      "datePublished": "2026-07-09",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-07-09-workstation-setup-kubernetes-exams/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-07-09-workstation-setup-kubernetes-exams/",
      "keywords": ["CKA", "CKAD", "CKS", "Kubernetes certification", "Bash", "Vim", "kubectl aliases"],
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
        {"@type": "ListItem", "position": 3, "name": "Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)"}
      ]
    }
  ]
}
</script>
```

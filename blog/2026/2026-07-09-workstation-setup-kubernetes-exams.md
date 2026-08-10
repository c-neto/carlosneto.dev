---
tags: cks, cka, ckad, linux-foundation, kubernetes
date: "2026-07-09"
category: kubernetes
---

*__Blog Post Publish Date:__ 2026/07/09*

---

# Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)

This blog post walks through the workstation optimizations I use to work more efficiently during the exam, including Vim configuration, Bash keybindings, shell aliases, and other tweaks that help reduce friction and save valuable time.

Time management is one of the most critical factors for passing the Linux Foundation Kubernetes certification exams. The CKA, CKAD, and CKS are hands-on exams conducted on remote Ubuntu instances running the XFCE desktop environment, where network latency and the remote desktop experience can slow you down. Check out the following tips to optimize your setup.

## Configure the U.S. Keyboard Layout (MacBooks)

If you're taking the exam on a MacBook, make sure your keyboard layout is set to `U.S.`. Otherwise, the remote Linux environment may not recognize certain characters correctly, especially `~` and `` ` ``. This is a common issue with layouts such as `U.S. International - PC` and `Brazilian – ABNT2`.

Before the exam, perform the following steps:

1. Open *__System Settings » Keyboard » Input Sources__*.
2. Add `U.S.` input source.
3. Remove any other input sources so only `U.S.` remains.

This helps prevent unexpected keyboard mapping issues during the exam.

## Disable Mission Control Shortcuts (MacBooks)

By default, pressing __CTRL + ←→__ switches between macOS Spaces. During the exam, this can be interpreted by the proctor as leaving the exam environment, potentially triggering a warning or even interrupting your session.

Before the exam, perform the following steps:

1. Open *__System Settings » Keyboard » Keyboard Shortcuts__*.
2. Select *__Mission Control__*.
3. Disable all shortcuts under *__Mission Control__*.

This helps prevent accidental desktop switching and reduces the risk of unnecessary proctor alerts or exam suspension on suspicion of consulting unauthorized material.

## Disable Window Tiling Apps (MacBook)

If you use window tiling apps such as [Rectangle](https://rectangleapp.com/) or [Magnet](https://magnet.crowdcafe.com/), it's strongly recommended to disable/close them before the exam. Their keyboard shortcuts can conflict with the exam workstation, causing unexpected behavior when using shortcuts such as __⌘ + ↑↓←→__.

## History Search by Prefix

__This is probably my most valuable tip!__

The exam environment uses __Bash__ as the default shell. Behind the scenes, Bash relies on the [GNU Readline](https://tiswww.case.edu/php/chet/readline/readline.html) library, which provides command-line editing, key bindings, and history navigation. For example, the interactive reverse search that appears when you press __CTRL + R__ is implemented by [GNU Readline](https://tiswww.case.edu/php/chet/readline/readline.html).

One of Readline's most useful features is history search by prefix, that is disabled by default. The [history-search-backward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029) and [history-search-forward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dforward-_0028_0029) functions search your command history using the text that already exists before the cursor, instead of simply moving to the previous or next command.

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

and press __↑__, [history-search-backward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029) cycles only through commands that begin with `kubectl g`:

```bash
kubectl get nodes
kubectl get pods
```

Commands such as `kubectl describe pod nginx` or `helm list` are skipped because they do not match the typed prefix.

This is much faster than the default __↑__ behavior, which walks through every command in your history, and often more convenient than repeatedly using __CTRL + R__ during the exam.

To enable this behavior, create the `~/.inputrc` file and add the following configuration:

```{code-block} bash
:caption: ~/.inputrc
"\e[A": history-search-backward   # ↑ (previous matching command)
"\e[B": history-search-forward    # ↓ (next matching command)
```

The file is automatically loaded whenever a new Bash session starts. If you modify it during an existing session, reload it with:

```bash
bind -f ~/.inputrc
```

## Setting Up Vim

The exam workstation includes [VSCodium](https://vscodium.com/). However, every exam task requires you to connect to a remote node via SSH, and VSCodium is not available on those remote machines. In addition, the exam workstation often has high latency, making mouse operation unreliable, this is where Vim shines.

The following settings provide a much better editing experience for Kubernetes YAML manifests.

Create the `~/.vimrc` file and add the following configuration:

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

Avoid using `set mouse=a` due to the exam workstation's high connection latency. Also, the clipboard settings with `clipboard+=unnamedplus,autoselect` does not work on the exam workstations.

> *I have created a blog post [Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)](2026-07-15-vim-kubernetes-exams.md) with editing techniques I use most frequently during exams.*

## Kubectl Aliases and Shortcuts

Each remote exam node already contains a preconfigured `~/.bashrc` file with several useful settings. A handy trick is to copy it to main workstation, append your own aliases, and then copy it back to the question nodes.

First, copy the `~/.bashrc` from question node:

```bash
scp cks1234:~/.bashrc ~/.bashrc
```

Append the following aliases to the end of the file:

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

> *__INFO:__ The `export x` is useful shorthand for generating YAML in imperative kubectl commands such as `k run nginx --image nginx:latest $x > nginx.yaml`*

## Copy Settings to Exam Question Node

All exam tasks are required to be performed on the remote question node via SSH. A convenient workflow is to create your configuration files once on the main instance and then copy them to the question node before starting the task.

```bash
scp ~/.inputrc ~/.vimrc ~/.bashrc cks1234:~/
ssh cks1234
```

## References

- <https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029>
- <https://vimdoc.sourceforge.net/htmldoc/options.html#'cursorcolumn'>
- <https://vim.rtorr.com/>
- <https://kubernetes.io/docs/reference/kubectl/quick-reference/>
- <https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#-em-deployment-em->

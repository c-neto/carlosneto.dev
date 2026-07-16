---
tags: cks, cka, ckad, linux-foundation, kubernetes
date: "2026-07-09"
category: kubernetes
---

*__Blog Post Publish Date:__ 2026/07/09*

---

# Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)

Time management is one of the most critical factors for passing the Linux Foundation Kubernetes certification exams. The CKA, CKAD, and CKS are hands-on exams conducted on remote Ubuntu instances running the XFCE desktop environment, where network latency and the remote desktop experience can slow you down.

This guide walks through the workstation optimizations I use to work more efficiently during the exam, including Vim configuration, Bash keybindings, shell aliases, and other tweaks that help reduce friction and save valuable time.

> _**NOTE**: The exam Linux instances have limited internet access. Therefore, you should memorize your setup because you won't be able to search for it during the exam._

## Configure the U.S. Keyboard Layout (MacBooks)

If you're taking the exam on a MacBook, make sure your keyboard layout is set to `U.S.`. Otherwise, the remote Linux environment may not correctly recognize certain characters, especially `~` and `` ` ``, when using layouts such as `Brazilian – ABNT2`.

1. Open ***System Settings » Keyboard » Input Sources***.
2. Add `U.S.` input source.
3. Remove any other input sources so only `U.S.` remains.

This helps prevent unexpected keyboard mapping issues during the exam.

## Disable Mission Control Shortcuts (MacBooks)

By default, pressing **CTRL + ←/→** switches between macOS Spaces. During the exam, this can be interpreted by the proctor as leaving the exam environment, potentially triggering a warning or even interrupting your session.

Before the exam:

1. Open ***System Settings » Keyboard » Keyboard Shortcuts***
2. Select ***Mission Control***
3. Disable all shortcuts under ***Mission Control***.

This helps prevent accidental desktop switching and reduces the risk of unnecessary proctor alerts or exam suspension on suspicion of consulting unauthorized material.

## History Search by Prefix

__This is probably my most valuable tip!__

The exam environment uses __Bash__ as the default shell. Behind the scenes, Bash relies on the [GNU Readline](https://tiswww.case.edu/php/chet/readline/readline.html) library, which provides command-line editing, key bindings, and history navigation. For example, the interactive reverse search that appears when you press __CTRL + R__ is implemented by [GNU Readline](https://tiswww.case.edu/php/chet/readline/readline.html).

One of Readline's most useful features is history search by prefix. The [history-search-backward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029) and [history-search-forward](https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dforward-_0028_0029) functions search your command history using the text that already exists before the cursor, instead of simply moving to the previous or next command.

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
"\C-w": backward-kill-word        # CTRL + w (delete word by word in terminal)
```

The file is automatically loaded whenever a new Bash session starts. If you modify it during an existing session, reload it with:

```bash
bind -f ~/.inputrc
```

Since each exam task is performed on a different remote node, copy the file to the target node (for example, `node01`):

```bash
scp ~/.inputrc node01:~/.inputrc
```

## Setting Up Vim

The exam workstation includes [VSCodium](https://vscodium.com/). However, every exam task requires you to connect to a remote node via SSH, and [VSCodium](https://vscodium.com/) is __not__ available on those remote machines. Therefore, the best approach is to use Vim (unfortunately).

The following settings provide a much better editing experience for Kubernetes YAML manifests.

Create the `~/.vimrc` file and add the following configuration:

```{code-block} vim
:caption: ~/.vimrc
set nu        " (number) Displays line numbers.
set ai        " (autoindent) Automatically preserves indentation while editing.
set et        " (expandtab) Converts tabs to spaces, preventing invalid YAML indentation.
set ts=2      " (tabstop) Displays tab characters as two spaces.
set sw=2      " (shiftwidth) Uses a two-space indentation level when indenting or unindenting.
set sts=2     " (softtabstop) Makes the Tab and Backspace keys use two-space indentation levels.
set hls       " (highlightsearch) Highlights all search matches.
set mouse=a   " (mouse) Enables mouse support for cursor movement, scrolling, and visual mode.
set cuc       " (cursorcolumn) Highlights the current cursor column, useful for YAML files.
syntax on     " Enables syntax highlighting based on file extension.
```

Copy the file to the remote node for the exam question (for example, `node01`):

```bash
scp ~/.vimrc node01:~/.vimrc
```

__Bonus__: I have created a blog post [Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)](2026-07-15-vim-kubernetes-exams.md) that focuses on the minimal Vim configuration and the editing techniques I use most frequently when working with Kubernetes YAML manifests.

## Kubectl Aliases and Shortcuts

During the exam you will type `kubectl` hundreds of times and will also need to back up configuration files. To save time and reduce the risk of mistakes (especially when nervous), avoid typing repeated commands: use aliases, functions, and shortcuts to prevent typos.

Each remote exam node already contains a preconfigured `~/.bashrc` file with several useful settings. A handy trick is to copy that file back to the main workstation, append your own aliases, and then copy it back to the remote nodes.

First, create a backup of the main instance `~/.bashrc` file:

```bash
cp ~/.bashrc ~/.bashrc.bkp
scp node01:~/.bashrc ~/.bashrc
```

Append the following aliases to the end of the file:

```{code-block} bash
:caption: ~/.bashrc
### omitted the .bashrc copied from question node

# disable default CTRL+W word erase behavior in terminal to be able to use backward-kill-word instead.
stty werase undef

# create a quick backup command `$ bkp <file>` to copy a file by appending .bkp
bkp() { cp "$1" "$1.bkp"; }

# kubectl aliases
alias k="kubectl"
alias kgp="kubectl get pods"
alias kgs="kubectl get svc"
alias kgn="kubectl get nodes"
alias kd="kubectl describe"
alias ke="kubectl get endpoints"
alias kaf="kubectl apply -f"
alias kdel="kubectl delete"
alias kdelp="kubectl delete pod"
alias kns="kubectl config set-context --current --namespace"
alias kctx="kubectl config use-context"

# shorthand for generating YAML in the imperative kubectl commands
export x="--dry-run=client -oyaml"
```

Finally, copy the updated configuration files back to the remote node:

```bash
scp ~/.bashrc node01:~/.bashrc
```

## References

- <https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029>
- <https://vimdoc.sourceforge.net/htmldoc/options.html#'cursorcolumn'>
- <https://vim.rtorr.com/>
- <https://kubernetes.io/docs/reference/kubectl/quick-reference/>
- <https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#-em-deployment-em->

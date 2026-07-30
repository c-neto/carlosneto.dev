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

Before the exam, perform the follow steps:

1. Open __System Settings » Keyboard » Input Sources__.
2. Add `U.S.` input source.
3. Remove any other input sources so only `U.S.` remains.

This helps prevent unexpected keyboard mapping issues during the exam.

## Disable Mission Control Shortcuts (MacBooks)

By default, pressing __CTRL + ←/→__ switches between macOS Spaces. During the exam, this can be interpreted by the proctor as leaving the exam environment, potentially triggering a warning or even interrupting your session.

Before the exam, perform the follow steps:

1. Open __System Settings » Keyboard » Keyboard Shortcuts__
2. Select __Mission Control__
3. Disable all shortcuts under __Mission Control__.

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
set nu        " Show line numbers.
set ai        " Preserve indentation while editing.
set et        " Convert tabs into spaces.
set ts=2      " Display tabs as two spaces.
set sw=2      " Indent and unindent using two spaces.
set sts=2     " Make Tab and Backspace use two-space indentation.
set mouse=c   " Enable mouse support for cursor position.
set hls       " Highlight search matches.
set cuc       " Highlight the current cursor column.
syntax on     " Enable syntax highlighting.
```

> *__NOTE__: Avoid using `set mouse=a` due to the exam workstation's high connection latency. Also, the `clipboard+=unnamedplus,autoselect` setting does not work on the exam workstations.*

Copy the file to the remote node for the exam question (for example, `node01`):

```bash
scp ~/.vimrc node01:~/.vimrc
```

__Bonus__: I have created a blog post [Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)](2026-07-15-vim-kubernetes-exams.md) with editing techniques I use most frequently during exams.

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

# kubectl aliases
alias k="kubectl"

alias kgp="kubectl get pods"
alias kd="kubectl describe"

alias kgs="kubectl get svc"
alias ke="kubectl get endpoints"

alias kaf="kubectl apply -f"
alias kdel="kubectl delete --now"
alias kdelp="kubectl delete pod --now"

alias kns="kubectl config set-context --current --namespace"
alias kctx="kubectl config use-context"

# make visible the cursor column in vim default theme
export TERM=xterm-265color

# define vim as default editor (systemctl edit)
export EDITOR="vim"

# shorthand for generating YAML in the imperative kubectl commands
# $ k run nginx --image nginx:latest $x > nginx.yaml
export x="--dry-run=client -oyaml"

# shorthand for show labels
# $ kgp $l
export l="--show-labels"
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

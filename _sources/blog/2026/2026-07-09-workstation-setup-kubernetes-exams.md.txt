---
tags: kubernetes
date: "2026-07-09"
category: kubernetes
---

*__Blog Post Publish Date:__ 2026/07/09*

---

# Workstation Setup for Kubernetes Exams (CKA/CKAD/CKS)

Time management is one of the most critical factors for passing the Linux Foundation Kubernetes certification exams. The CKA, CKAD, and CKS are hands-on exams conducted on remote Ubuntu instances running the XFCE desktop environment, where network latency and the remote desktop experience can slow you down. 

This guide walks through the workstation optimizations I use to work more efficiently during the exam, including Vim configuration, Bash keybindings, shell aliases, and other tweaks that help reduce friction and save valuable time.

> <i class="fa-solid fa-circle-info"></i> _The exam Linux instances have limited internet access. Therefore, you should memorize your setup because you won't be able to search for it during the exam._

## Configure the U.S. Keyboard Layout (MacBooks)

If you're taking the exam on a MacBook, make sure your keyboard layout is set to `U.S.`. Otherwise, the remote Linux environment may not correctly recognize certain characters, especially `~` and `` ` ``, when using layouts such as `Brazilian – ABNT2`.

To configure it, open __*Settings » Keyboard » Text Input » Edit*__ and define `U.S.` as your only input source. This helps avoid unexpected keyboard mapping issues during the exam.

## Bash History Search

__This is probably my most valuable tip!__

The exam environment uses __Bash__ as the default shell. Behind the scenes, Bash relies on the __GNU Readline__ library, which provides powerful command-line editing and history features. For example, the interactive search menu that appears when you press __Ctrl + R__ is implemented by GNU Readline.

Two useful Readline functions are __not bound to keys by default__: `history-search-backward` and `history-search-forward`. These functions search your command history using the text you've already typed at the prompt.

For example to undestand the `history-search-backward` and `history-search-forward`, suppose you previously executed the following commands:

```bash
ls -lR        # first execution
ps aux
touch foobar
ls -lahrt     # last execution
```

If you type:

```bash
ls
```

and press __Arrow Up__, Bash autocompletes the first matching command, ignoring `touch foobar` and `ps aux` occourences:

```bash
ls -lahrt
```

Press __Arrow Up__ again to move to the previous matching command:

```bash
ls -lR
```

Press __Arrow Down__ to move forward through the filtered history.

These functions are extremely useful during the exam because they save valuable time by avoiding the need to retype long commands or repeatedly use __Ctrl + R__.

To configure the `history-search-backward` and `history-search-forward`, create the `.inputrc` file:

```bash
vim ~/.inputrc
```

Add the following content:

```{code-block} bash
:caption: ~/.inputrc
"\e[A": history-search-backward
"\e[B": history-search-forward
"\C-w": backward-kill-word
```

> <i class="fa-solid fa-circle-info"></i> _`"\e[A"` and `"\e[B"` are the escape sequences for the __Arrow Up__ and __Arrow Down__ keys, respectively._

The file is loaded automatically whenever a new shell session starts. You can also reload it manually:

```bash
bind -f ~/.inputrc
```

Copy the file to remote node of the exam question (for example, `node01`):

```bash
scp ~/.inputrc node01:~/.inputrc
```

## Setting Up Vim

The exam workstation includes __VSCodium__. However, every exam task requires you to connect to a remote node via SSH, and VSCodium is __not__ available on those remote machines. Therefore, the best approach is to use Vim (unfortunately).

The following settings provide a much better editing experience for Kubernetes YAML manifests.

Create the `.vimrc` file and add the following configuration:

```{code-block} bash
:caption: ~/.vimrc
set nu
set ai
set et
set ts=2
set sw=2
set sts=2
set hls
set mouse=a
set cursorcolumn
syntax on
```

Copy the file to remote node of the exam question (for example, `node01`):

```bash
scp ~/.vimrc node01:~/.vimrc
```

Parameters Explanation:

- `set nu`: (_number_) Displays line numbers, making it easier to locate YAML parser errors.
- `set ai`: (_auto ident_) Automatically preserves indentation while editing.
- `set et`: (_expand tab_) Converts tabs to spaces, preventing invalid YAML indentation.
- `set ts=2`: (_tab stop_) Displays tab characters as two spaces.
- `set sw=2`: (_shift width_) Uses a two-space indentation level when indenting or unindenting.
- `set sts=2`: (_soft tab stop_) Makes the Tab and Backspace keys use two-space indentation levels.
- `set hls`: (_high light search_) Highlights all search matches.
- `set mouse=a`: (_mouse all_) Enables mouse support for cursor movement and scrolling.
- `set cuc`: (_cursor column_) Highlights the current cursor column, making indentation easier to follow.
- `syntax on`: Enables syntax highlighting for improved readability.

## Kubectl Aliases

You'll type `kubectl` hundreds of times during the exam, so creating aliases is well worth it.

Each remote exam node already contains a preconfigured `.bashrc` file with several useful settings. A handy trick is to copy that file back to the main workstation, append your own aliases, and then copy it back to the remote nodes.

First, create a backup and copy the remote `.bashrc`:

```bash
cp ~/.bashrc ~/.bashrc.bkp
scp node01:~/.bashrc ~/.bashrc
```

Append the following aliases to the end of the file:

```{code-block} bash
:caption: ~/.bashrc
...

stty werase undef

alias kgp="kubectl get pods"
alias kgs="kubectl get svc"
alias kgn="kubectl get nodes"
alias kd="kubectl describe"
alias ke="kubectl get endpoints"
alias kaf="kubectl apply -f"
alias kdel="kubectl delete"
alias kns="kubectl config set-context --current --namespace"
alias kgns="kubectl config get-context"
alias kctx="kubectl config use-context"

export x="--dry-run=client -o yaml"
```

Finally, copy the updated configuration files back to the remote node:

```bash
scp ~/.bashrc root@node01:~/.bashrc
```

## References

- <https://tiswww.case.edu/php/chet/readline/readline.html#index-history_002dsearch_002dbackward-_0028_0029>
- <https://vimdoc.sourceforge.net/htmldoc/options.html#'cursorcolumn'>
- <https://vim.rtorr.com/>

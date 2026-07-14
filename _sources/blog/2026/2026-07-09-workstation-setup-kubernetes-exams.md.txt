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

## Disable Mission Critical Shortcuts (MacBooks)

If you press CTRL + Arrow (Left/Right) it can change the macOS desktop (Space), which may trigger the exam proctor and can lead to the exam interruption. Disable these shortcuts before the exam:

1. Open _System Settings → Keyboard → Keyboard Shortcuts_.
2. Select `Mission Control`
3. Uncheck or change the shortcuts for _Move left a space_ and _Move right a space_ (or any shortcuts using CTRL + Left/Right).

## Bash History Search

__This is probably my most valuable tip!__

The exam environment uses __Bash__ as the default shell. Behind the scenes, Bash relies on the __GNU Readline__ library, which provides powerful command-line editing and history features. For example, the interactive search menu that appears when you press __CTRL + R__ is implemented by GNU Readline.

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

These functions are extremely useful during the exam because they save valuable time by avoiding the need to retype long commands or repeatedly use __CTRL + R__.

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
set nu              # (number) Displays line numbers, making it easier to cursor movement and line range operation.
set ai              # (auto ident) Automatically preserves indentation while editing.
set et              # (expand tab) Converts tabs to spaces, preventing invalid YAML indentation.
set ts=2            # (tab stop) Displays tab characters as two spaces.
set sw=2            # (shift width) Uses a two-space indentation level when indenting or unindenting.
set sts=2           # (soft tab stop) Makes the Tab and Backspace keys use two-space indentation levels.
set hls             # (high light search) Highlights all search matches.
set mouse=a         # (mouse all) Enables mouse support for cursor movement, scrolling, and visual mode.
set cursorcolumn    # (cursor column) Highlights the current cursor column, useful for YAML files.
syntax on           # Enables syntax highlighting based on file extension.
```

Copy the file to remote node of the exam question (for example, `node01`):

```bash
scp ~/.vimrc node01:~/.vimrc
```

__Bonus__: The following `vim` commands and operations cover all needs for editing files during the exam:

```python
~                # toggle letter case (upper/lower)
dd               # cut line
p                # paste line
u                # undo
cW               # replace an entire word and active the insertion mode
$                # go to the final line
^                # go to the start line
:%s/foo/bar/g    # substitutes (replaces) all occurrences of "foo" with "bar".
:10,15>          # indents lines 10 through 15 by one shiftwidth.
:10,15<          # back indents lines 10 through 15 by one shiftwidth.
:30,50d          # cuts lines 30 through 50.
:30,50t70        # copies lines 30 through 50 and pastes them right below line 70
:30,50m70        # move lines 30 through 50 and pastes them right below line 70
SHIFT+i » CTRL+y # repeat the line above character by character
CTRL+c » select column » SHIFT+i » write text + ESC + ESC  # multi-line column insertion (comments)
```

## Kubectl Aliases and Shortcuts

During the exam you will type `kubectl` hundreds of times and will also need to back up configuration files. To save time and reduce the risk of mistakes (especially when nervous), avoid typing repeated commands: use aliases, functions, and shortcuts to prevent typos.

Each remote exam node already contains a preconfigured `.bashrc` file with several useful settings. A handy trick is to copy that file back to the main workstation, append your own aliases, and then copy it back to the remote nodes.

First, create a backup and copy the remote `.bashrc`:

```bash
cp ~/.bashrc ~/.bashrc.bkp
scp node01:~/.bashrc ~/.bashrc
```

Append the following aliases to the end of the file:

```{code-block} bash
:caption: ~/.bashrc
### >>> omitted the .bashrc copied from question node

# disable default CTRL+W word erase behavior in terminal to be able to use backward-kill-word instead.
stty werase undef

# create a quick backup copy of a file by appending .bkp
bkp() { cp "$1" "$1.bkp"; }

# kubectl aliases
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

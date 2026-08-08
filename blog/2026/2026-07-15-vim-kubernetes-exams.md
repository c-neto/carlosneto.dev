---
tags: cks, cka, ckad, linux-foundation, kubernetes
date: "2026-07-15"
category: kubernetes
---

*__Blog Post Publish Date:__ 2026/07/15*

---

# Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)

This post focuses on the minimal Vim configuration and the editing techniques I use during Kubernetes certifications exams by Linux Foundation. The goal is not to master Vim, but to learn a small set of commands to improve your editing speed during the exam.

## Vim: Less Mouse, More Efficiency

The exam workstation includes *[VSCodium](https://vscodium.com/)* (*the free and open-source binaries of VS Code*), but it's not a practical choice during the exam. While the workstation itself includes *VSCodium*, all exam tasks are completed on remote nodes via terminal over SSH, where it is unavailable. In addition, the connection to the exam workstation often has noticeable latency, making mouse operations slow and unreliable. The less you rely on the mouse, the faster you'll be able to edit files. This is where Vim shines.

You don't need to become a Vim expert to pass the exam. This guide covers everything you need to edit Kubernetes YAML manifests efficiently under exam conditions. Focus on building muscle memory by practicing these commands in the simulation labs.

## Vim Configuration

This configuration is intentionally minimal and optimized for editing Kubernetes YAML manifests. Two-space indentation prevents invalid YAML formatting, line numbers make it easier to jump to specific locations, syntax highlighting improves readability, and cursor highlighting helps you keep track of indentation levels.

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

> *__NOTE__: Avoid using `set mouse=a` due to the exam workstation's high connection latency. Also, the clipboard settings with `clipboard+=unnamedplus,autoselect` do not work on the exam workstations.*

Each exam task is performed on a different remote node. Before starting a task, copy your local `~/.vimrc` to the target question machine:

```bash
scp ~/.vimrc node01:~/.vimrc
```

## Essential Editing Commands

These are the commands you'll use most often. They let you navigate, copy, delete, replace, and repeat edits without leaving Normal mode, making common editing tasks much faster.

```bash
.           # repeat the last command
~           # toggle character case
dd          # cut/delete the current line
dG          # cut/delete from the cursor to the end of the file
dgg         # cut/delete from the cursor to the start of the file
y           # yank (copy)
p           # paste below
P           # paste above
u           # undo
CTRL+r      # redo
O           # open a new line above and enter Insert mode
o           # open a new line below and enter Insert mode
cW          # replace the current word and enter Insert mode
C           # delete from the cursor to the end of the line and enter Insert mode
i » CTRL+y  # copy the character above the cursor
A           # move to the end of the line and enter Insert mode
:wq         # save and quit (or ZZ)
```

## Navigation Commands

I strongly recommend __not__ using `set mouse=a` during the exam. The remote exam workstations have higher latency than the Killer Shell simulation environment, making mouse interactions in Vim slow and unreliable. Use the mouse only for scrolling. For navigation, use the following commands:

```bash
/greeting   # search for "greeting"
?foo/bar    # search for "foo/bar" (include "/")
n           # jump forward in the search match list
SHIFT+n     # jump backward in the search match list
12gg        # jump to line 12
0           # jump to the beginning of the line
gg          # jump to the start of the file
G           # jump to the end of the file
W           # jump to the next word
B           # jump to the previous word
v           # enter in Visual inline mode (lowercase)
V           # enter in Visual lines mode (uppercase)
CTRL+v      # enter in Visual block mode (lowercase)
```

## Fixing YAML Indentation

Indentation mistakes are one of the most common causes of invalid Kubernetes manifests. Vim makes it easy to SHIFT entire YAML blocks to the right or left while preserving their structure.

To increase the indentation:

```bash
V       # 1. enter Visual Line mode (uppercase)
↑↓      # 2. select the lines
>       # 3. SHIFT indentation right
ESC     # 4. apply the change
.       # 5. repeat the indentation
```

If you need to reverse the indentation or perform another operation on the same lines, use `gv` to restore the previous Visual selection:

```bash
gv      # 1. reselect the previous Visual selection
<       # 2. SHIFT indentation left
ESC     # 3. apply the change
.       # 4. repeat the operation
```

## Commenting Multiple Lines

Visual Block mode allows you to insert the same text across multiple lines simultaneously. This is particularly useful for commenting or uncommenting YAML blocks.

```bash
CTRL+v    # 1. enter Visual Block mode
↑↓        # 2. select the first column of the lines
SHIFT+i   # 3. enter Insert mode
#         # 4. type the comment character
ESC       # 5. apply the change to all selected lines
```

The same technique can also be used to insert identical text across multiple lines, such as prefixes, labels, or environment variables.

## Search and Replace

When renaming resources, labels, namespaces, image names, or environment variables, replacing every occurrence manually is both slow and error-prone.

To replace every occurrence of a string:

```bash
:%s/foo/bar/g                   # replace "foo" with "bar"
:%s#/kubernets/#/kubernetes/#g  # replace "/kubernets/" with "/kubernetes/"
```

Sometimes, however, you only want to replace one occurrence at a time. In that case, use the following workflow:

```bash
*                   # 1. search for the word under the cursor (or use "/foobar")
cW                  # 2. replace the current occurrence
type replacement    # 3. type the replacement
n                   # 4. jump to the next occurrence
.                   # 5. repeat the replacement
n                   # 6. jump forward in the match list
SHIFT+n             # 8. jump backward in the match list
.                   # 9. repeat the replacement
```

This approach lets you review each occurrence before replacing it, making it safer than a global search-and-replace.

## Working with YAML Blocks

Many editing operations can be performed directly on a range of line numbers without entering Visual mode. This is especially useful when moving, copying, deleting, or reindenting large YAML blocks.

```bash
:%<         # unindent all lines
:10,15>     # indent lines 10-15
:10,15<     # unindent lines 10-15
:30,50x     # delete lines 30-50
:30,50t70   # copy lines 30-50 and paste below line 70
:30,50m70   # cut lines 30-50 and paste below line 70
:30,50d     # cut lines 30-50
:10,15y     # copy lines 10-15
:50put      # paste lines below line 50
```

## Working with Numbers

Kubernetes manifests frequently contain numeric values such as replica counts, ports, resource requests, limits, and probe timings. Instead of deleting and retyping numbers, Vim can increment or decrement the value directly under the cursor.

```bash
50 » CTRL+a     # increment a number by 50
40 » CTRL+x     # decrement a number by 40
```

## Running Shell Commands in Vim

You can leverage operating system CLI tools to process and edit file content directly inside Vim. For example, you can execute [yq](https://github.com/mikefarah/yq) on the current buffer to check for syntax errors and format the file:

```bash
:%!yq
```

You can also apply the same approach to a selection of lines. For example, to sort and remove duplicate lines, select the lines and pipe them through [sort](https://man7.org/linux/man-pages/man1/sort.1.html) and [uniq](https://ss64.com/bash/uniq.html):

```bash
SHIFT+V         # 1. Select the lines (Visual Line mode)
:!sort | uniq   # 2. Sort and remove duplicates from the selection
```

Vim can also execute commands without modifying the current buffer. This is useful when you need to quickly inspect information from the cluster while editing a manifest. For example, when editing a NetworkPolicy, you can check pod and namespace labels with:

```bash
:!kubectl get pods,ns --show-labels -n foobar
```

Another useful trick is saving protected files without opening them with `sudo vim`. This is particularly handy when you forget to open a file with elevated privileges and have already made several changes. Instead of reopening the file with `sudo vim` and repeating your edits, you can write the current buffer using:

```bash
:w !sudo tee %
```

`:w` normally saves the buffer to a file. When followed by `!`, it sends the buffer's content to an external command's standard input (STDIN) instead of writing to the file directly.

## Learn More

Take a look at the complete Vim cheatsheet <https://vim.rtorr.com/> for insights into more ways to improve vim tricks.

For more tips on how I configure my Kubernetes exam workstation, including Bash aliases and search history shortcuts, take a look at my previous blog post [Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)](2026-07-09-workstation-setup-kubernetes-exams.md).

---
tags: cks, cka, ckad, linux-foundation, kubernetes
date: "2026-07-15"
category: kubernetes
---

***Blog Post Publish Date:** 2026/07/15*

---

# Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)

This post focuses on the minimal Vim configuration and the editing techniques I use most frequently when working with Kubernetes YAML manifests. The goal is not to master Vim, but to learn a small set of commands to improve your editing speed during the exam.

## Vim: A Necessary Evil

While the exam workstation includes [VSCodium](https://vscodium.com/), every task takes place on remote nodes over SSH. Copying and pasting manifests into a local GUI editor is a trap that will drain your time. 

Love it or hate it, getting comfortable with Vim is essential for working fast enough to pass the CKA, CKAD, and CKS.

## Vim Configuration

This configuration is intentionally minimal and optimized for editing Kubernetes YAML manifests. Two-space indentation prevents invalid YAML formatting, line numbers make it easier to jump to specific locations, syntax highlighting improves readability, and cursor highlighting helps you keep track of indentation levels.

```{code-block} vim
:caption: ~/.vimrc
set nu        " Show line numbers.
set ai        " Preserve indentation while editing.
set et        " Convert tabs into spaces.
set ts=2      " Display tabs as two spaces.
set sw=2      " Indent and unindent using two spaces.
set sts=2     " Make Tab and Backspace use two-space indentation.
set hls       " Highlight search matches.
set mouse=c   " Enable mouse support for cursor position.
set cuc       " Highlight the current cursor column.
syntax on     " Enable syntax highlighting.
nnoremap kd :w !kubectl diff -f -<CR>   " Maps 'kd' to run 'kubectl diff' with current editing file content
```

> __WARNING__: Don't use `set mouse=a` during the exam!
>
> The remote exam workstations have higher latency than the Killer Shell simulation environment, making mouse interactions in Vim slow and unreliable. Use the mouse only for scrolling. For editing and text selection, rely on Vim's Visual mode and line-jump commands instead.

Each exam task is performed on a different remote node. Before starting a task, copy your local `~/.vimrc` to the target question machine:

```bash
scp ~/.vimrc node01:~/.vimrc
```

## Essential Editing Commands

These are the commands you'll use most often. They allow you to navigate, copy, delete, replace, and repeat edits without leaving Normal mode, making common editing tasks much faster.

```bash
.               # repeat the last command
~               # toggle character case
dd              # delete (cut) the current line
y               # yank (copy)
p               # paste
u               # undo
CTRL+r          # redo
O               # open a new line above and enter Insert mode
o               # open a new line below and enter Insert mode
cW              # replace the current word and enter Insert mode
i » CTRL+y      # copy characters from the line above
/foobar         # search forward for "foobar"
0               # move to the beginning of the line
$               # move to the end of the line
W               # jump to the next word
B               # go back to the previous word
```

## Fixing YAML Indentation

Indentation mistakes are one of the most common causes of invalid Kubernetes manifests. Vim makes it easy to SHIFT entire YAML blocks to the right or left while preserving their structure.

To increase the indentation:

```bash
V               # 1. enter Visual Line mode
select lines    # 2. select the lines
>               # 3. SHIFT indentation right
ESC             # 4. apply the change
.               # 5. repeat the indentation
```

If you need to reverse the indentation or perform another operation on the same lines, use `gv` to restore the previous Visual selection:

```bash
gv              # 1. reselect the previous Visual selection
<               # 2. SHIFT indentation left
ESC             # 3. apply the change
.               # 4. repeat the operation
```

## Commenting Multiple Lines

Visual Block mode allows you to insert the same text across multiple lines simultaneously. This is particularly useful for commenting or uncommenting YAML blocks.

```bash
CTRL+v          # 1. enter Visual Block mode
select column   # 2. select the first column
SHIFT+i         # 3. enter Insert mode
#               # 4. type the comment character
ESC             # 5. apply the change to all selected lines
```

The same technique can also be used to insert identical text across multiple lines, such as prefixes, labels, or environment variables.

## Search and Replace

When renaming resources, labels, namespaces, image names, or environment variables, replacing every occurrence manually is both slow and error-prone.

To replace every occurrence of a string:

```bash
:%s/foo/bar/g       # replace all occurrences of "foo" with "bar"
```

Sometimes, however, you only want to replace one occurrence at a time. In that case, use the following workflow:

```bash
*                   # 1. search for the word under the cursor
cW                  # 2. replace the current occurrence
type replacement    # 3. type the replacement
n                   # 4. jump to the next occurrence
.                   # 5. repeat the replacement
n                   # 6. skip this occurrence if desired
n                   # 7. jump to the next occurrence
SHIFT+n             # 8. go back to previous selection
.                   # 9. repeat the replacement
```

This approach lets you review each occurrence before replacing it, making it safer than a global search-and-replace.

## Working with YAML Blocks

Many editing operations can be performed directly on a range of line numbers without entering Visual mode. This is especially useful when moving, copying, deleting, or reindenting large YAML blocks.

```bash
:10,15>         # indent lines 10-15
:10,15<         # unindent lines 10-15
:30,50d         # delete (cut) lines 30-50
:10,15y         # copy lines 10-15
:30,50t70       # copy lines 30-50 below line 70
:30,50m70       # move lines 30-50 below line 70
:50put          # put yanked lines below line 50
```

## Working with Numbers

Kubernetes manifests frequently contain numeric values such as replica counts, ports, resource requests, limits, and probe timings. Instead of deleting and retyping numbers, Vim can increment or decrement the value directly under the cursor.

```bash
50 » CTRL+a     # increment a number by 50
40 » CTRL+x     # decrement a number by 40
```

## Running Shell Commands in Vim

You can leverage your operating system's CLI tools to edit file content directly inside Vim. For example, if you need to sort and remove duplicate lines in a manifest, you can pipe your selection directly to the [sort](https://man7.org/linux/man-pages/man1/sort.1.html) and [uniq](https://ss64.com/bash/uniq.html) utilities:

```bash
SHIFT + V       # 1. Select the lines (Visual Line mode)
:!sort | uniq  # 2. Sort and remove duplicates from the selection
```

You can also apply this logic to an entire file. For instance, to quickly format raw JSON, you can use Python's built-in [`json.tool`](https://docs.python.org/3/library/json.html):

```bash
:%!python -m json.tool
```

Beyond filtering and editing text, you can pass your unsaved buffer into external commands without modifying the file or leaving Vim. For example, this command allows you to compare the file you are editing in Vim with the one running in the Kubernetes cluster without needing to save the file first.

```bash
:w !kubectl diff -f -
```

> _In Vim, `:w` normally saves to a file. But when followed by `!`, it redirects your buffer’s content to an external command's standard input (STDIN) instead of writing to disk._

## Further Reading

If you'd like to learn more about Vim, check the complete Vim cheat sheet at <https://vim.rtorr.com/>. However, I recommend focusing on mastering a small set of commands rather than trying to memorize everything Vim has to offer.

## Conclusion

You don't need to become a Vim expert to pass the Kubernetes certification exams.

A minimal configuration and a handful of well-practiced commands are enough to edit Kubernetes YAML manifests quickly and confidently under exam conditions.

Focus on building muscle memory with the commands presented in this guide. The less time you spend fighting the editor, the more time you'll have to solve the Kubernetes problems that actually determine your exam score.

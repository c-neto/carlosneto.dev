---
tags: kubernetes, certification, vim
date: "2026-07-15"
category: Kubernetes
author: Carlos Neto
title: "Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)"
description: "The minimal vimrc and the small set of Vim commands I use to edit Kubernetes YAML fast in the CKA, CKAD, and CKS exams: indentation, block comments, search and replace, line ranges, and shell filters."
myst:
  html_meta:
    description: "The minimal vimrc and the small set of Vim commands I use to edit Kubernetes YAML fast in the CKA, CKAD, and CKS exams: indentation, block comments, search and replace, line ranges, and shell filters."
og:title: "Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)"
og:description: "The minimal vimrc and the small set of Vim commands I use to edit Kubernetes YAML fast in the CKA, CKAD, and CKS exams: indentation, block comments, search and replace, line ranges, and shell filters."
---

*__Blog Post Publish Date:__ 2026/07/15*

---

# Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)

This blog post covers the minimal Vim configuration and the editing techniques I use in the Linux Foundation Kubernetes certification exams. You don't need to master Vim. A small set of commands is enough to edit YAML manifests much faster under exam conditions.

## Vim: Less Mouse, More Efficiency

The exam workstation includes *[VSCodium](https://vscodium.com/)* (*the free and open-source binaries of VS Code*), but it isn't practical during the exam. Every task is done on a remote node over SSH, where VSCodium isn't available. The connection to the workstation also often has noticeable latency, which makes the mouse slow and unreliable. The less you rely on the mouse, the faster you edit. This is where Vim shines.

**Vim** is a modal text editor: you switch between modes, such as Normal mode for moving and editing with short commands and Insert mode for typing text. That is what makes it fast without a mouse. Practice the commands below in the simulation labs, such as Killer Shell, until they become muscle memory.

## Vim Configuration

This configuration is intentionally minimal and tuned for Kubernetes YAML. Two-space indentation prevents invalid YAML, line numbers make it easy to jump to a line, syntax highlighting helps reading, and the cursor column highlight shows the indentation level.

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

> _Avoid using `set mouse=a` due to the exam workstation's high connection latency. Also, the clipboard settings `clipboard+=unnamedplus,autoselect` do not work on the exam workstations._

Each exam task is performed on a different remote node. Before starting a task, copy your local `~/.vimrc` to the target question machine:

```bash
scp ~/.vimrc node01:~/.vimrc
```

## Essential Editing Commands

These are the commands you'll use most. They copy, delete, replace, and repeat edits without the mouse. `Ctrl+y` works in Insert mode; the others run from Normal mode:

```bash
o           # Open a new line below
Shift+o     # Open a new line above
i           # Enter Insert mode
Shift+a     # Enter Insert mode at the end of the line
cW          # Cut the word under the cursor and enter Insert mode (for word replacement)
Shift+c     # Cut to the end of the line and enter Insert mode (for line replacement)
Ctrl+y      # Copy the character from the line above

y           # Yank (copy)
p           # Paste below
Shift+p     # Paste above
dd          # Cut the current line
dG          # Cut to the end of the file
dgg         # Cut to the beginning of the file

u           # Undo
Ctrl+r      # Redo

Shift+v     # Enter Visual Line mode (for indentation and copying)
Ctrl+v      # Enter Visual Block mode (for commenting lines)
>           # Indent to the right
<           # Indent to the left
.           # Repeat the last command
~           # Toggle character case

:retab      # Convert tabs to spaces
:wq         # Save and quit (or ZZ)
```

## Cursor Movement

I strongly recommend **not** using `set mouse=a` in the exam. The remote exam workstations have higher latency than the Killer Shell simulator, so mouse interactions in Vim are slow and unreliable. Use the mouse only to scroll, and navigate with these commands:

```bash
/greeting   # Search for "greeting"
/foo/bar    # Search for "foo/bar"
n           # Jump to the next match
N           # Jump to the previous match
12gg        # Jump to line 12
0           # Jump to the beginning of the line
gg          # Jump to the beginning of the file
G           # Jump to the end of the file
W           # Jump to the next word
B           # Jump to the previous word
```

## YAML Indentation

Indentation mistakes are one of the most common causes of invalid Kubernetes manifests. Vim indents whole YAML blocks to the right or left while keeping their structure.

To increase the indentation:

```bash
Shift+v   # 1. Select lines in Visual Line mode (↑↓)
>         # 2. Shift indentation to the right
ESC       # 3. Apply the change
.         # 4. Repeat the indentation
```

If you need to reverse the indentation or perform another operation on the same lines, use `gv` to restore the previous Visual selection:

```bash
gv      # 1. Reselect the previous Visual selection
<       # 2. Shift indentation to the left
ESC     # 3. Apply the change
.       # 4. Repeat the operation
```

## Commenting Multiple Lines

**Visual Block mode** selects a rectangle of text across several lines, so you can insert the same text on all of them at once. It's the quickest way to comment or uncomment a YAML block.

```bash
Ctrl+v    # 1. Select columns across lines in Visual Block mode (↑↓)
Shift+i   # 2. Enter Insert mode
#         # 3. Type the comment character
ESC       # 4. Apply the change to all selected lines
```

The same technique can also be used to insert identical text across multiple lines, such as prefixes, labels, or environment variables.

## Search and Replace

When you rename resources, labels, namespaces, image names, or environment variables, replacing every occurrence by hand is slow and error-prone.

To replace every occurrence of a string:

```bash
:%s/foo/bar/g                   # Replace "foo" with "bar"
:%s#/kubernets/#/kubernetes/#g  # Replace "/kubernets/" with "/kubernetes/"
```

Sometimes you want to replace one occurrence at a time instead. Use this workflow:

```bash
*         # Search for the word under the cursor (or use "/greeting")
cW        # Replace the current occurrence
foobar    # Type the replacement text
n         # Jump to the next match
.         # Repeat the replacement
n         # Jump to the next match
n         # Skip this match and jump to the next one
Shift+n   # Go back to the previous match
.         # Repeat the replacement here
```

This approach lets you review each occurrence before replacing it, making it safer than a global search-and-replace.

## Working with YAML Blocks

Many operations work directly on a range of line numbers, without Visual mode. That's especially useful to move, copy, delete, or reindent large YAML blocks.

```bash
:%<         # Unindent all lines
:10,15>     # Indent lines 10-15
:10,15<     # Unindent lines 10-15
:30,50t70   # Copy lines 30-50 and paste below line 70
:30,50m70   # Cut lines 30-50 and paste below line 70
:30,50d     # Cut lines 30-50
:10,15y     # Copy lines 10-15
:50put      # Paste lines below line 50
```

## Working with Numbers

Kubernetes manifests are full of numbers such as replica counts, ports, resource requests and limits, and probe timings. Instead of deleting and retyping them, Vim can increment or decrement them in place.

Place the cursor before or on a number, then use `Ctrl+a` to increment it or `Ctrl+x` to decrement it. You can also provide a count to change the value by a larger amount:

```bash
50 » Ctrl+a     # Increment the next number by 50
40 » Ctrl+x     # Decrement the next number by 40
```

For example, with the cursor on `replicas`:

```yaml
replicas: 3
```

Pressing `Ctrl+a` changes it to:

```yaml
replicas: 4
```

Likewise, `10 » Ctrl+a` changes it from `3` to `13`.

## Running Shell Commands in Vim

Vim can pipe the file, or part of it, through any command-line tool and replace it with the output. For example, run [yq](https://github.com/mikefarah/yq) on the whole buffer to catch syntax errors and format the file:

```bash
:%!yq
```

You can also apply the same approach to a selection of lines. For example, to sort and remove duplicate lines, select the lines and pipe them through [sort](https://man7.org/linux/man-pages/man1/sort.1.html) and [uniq](https://ss64.com/bash/uniq.html):

```bash
Shift+v         # 1. Select lines in Visual Line mode (↑↓)
:!sort | uniq   # 2. Sort and remove duplicates from the selection
```

Vim can also execute commands without modifying the current buffer. This is useful when you need to quickly inspect information from the cluster while editing a manifest. For example, when editing a NetworkPolicy, you can check pod and namespace labels with:

```bash
:!kubectl get pods,ns --show-labels -n foobar
```

Another useful trick is saving a protected file you opened without `sudo`. When you've already made several changes, you don't need to reopen it with `sudo vim` and repeat them. Write the buffer through `sudo` instead:

```bash
:w !sudo tee %
```

`:w` normally writes the buffer to a file. Followed by `!`, it sends the buffer's content to a command's standard input instead. Here, `tee` runs as root and writes it to `%`, the current file name.

## Learn More

The [Vim cheat sheet](https://vim.rtorr.com/) has many more commands, and the official [Vim documentation](https://vimhelp.org/) covers each one in detail. To practice in exam conditions, use the simulator sessions that come with your exam registration.

For the rest of my exam workstation setup, including Bash aliases and history search by prefix, see [Workstation Setup for Kubernetes Exams (CKA, CKAD & CKS)](/blog/2026/2026-07-09-workstation-setup-kubernetes-exams.md). History search by prefix comes from GNU Readline, which I explain in [GNU Readline: The Magic Behind Terminal Autocomplete](/blog/2026/2026-10-18-gnu-readline-foundation.md).

## Key Takeaways

- Use Vim on the question nodes: VSCodium isn't available there, and latency makes the mouse unreliable.
- Keep `~/.vimrc` minimal for YAML: line numbers, auto-indent, two-space tabs, and a cursor column highlight. Copy it to each node with `scp`.
- Indent blocks with `Shift+v`, `>` or `<`, and repeat with `.`. Use `gv` to reselect the last selection.
- Comment several lines with `Ctrl+v`, `Shift+i`, `#`, then `ESC`.
- Replace globally with `:%s/old/new/g`, or one match at a time with `*`, `cW`, `n`, and `.`.
- Use line ranges such as `:30,50d`, `:30,50t70`, and `:30,50m70` to delete, copy, and move YAML blocks.
- Change numbers with `Ctrl+a` and `Ctrl+x`, filter text through tools with `:%!yq`, and save a protected file with `:w !sudo tee %`.

## References

- [Vim cheat sheet (vim.rtorr.com)](https://vim.rtorr.com/)
- [Vim help files (vimhelp.org)](https://vimhelp.org/)
- [Options: cursorcolumn (Vim documentation)](https://vimdoc.sourceforge.net/htmldoc/options.html#'cursorcolumn')
- [yq (GitHub)](https://github.com/mikefarah/yq)
- [sort (Linux man pages)](https://man7.org/linux/man-pages/man1/sort.1.html)

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
      "headline": "Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)",
      "description": "The minimal vimrc and the small set of Vim commands I use to edit Kubernetes YAML fast in the CKA, CKAD, and CKS exams: indentation, block comments, search and replace, line ranges, and shell filters.",
      "datePublished": "2026-07-15",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-07-15-vim-kubernetes-exams/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-07-15-vim-kubernetes-exams/",
      "keywords": ["Vim", "CKA", "CKAD", "CKS", "Kubernetes YAML", "vimrc"],
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
        {"@type": "ListItem", "position": 3, "name": "Vim for Kubernetes Certification Exams (CKA, CKAD & CKS)"}
      ]
    }
  ]
}
</script>
```

---
tags: zsh, terminal
date: "2026-10-28"
category: Linux
author: Carlos Neto
title: "Hacking Your Zsh Terminal with Custom Widgets"
description: "How to turn Zsh functions into keyboard shortcuts with zle -N and bindkey, what BUFFER, LBUFFER, RBUFFER, and CURSOR expose to a widget, and a widget that reruns the current command every two seconds, aliases included."
myst:
  html_meta:
    description: "How to turn Zsh functions into keyboard shortcuts with zle -N and bindkey, what BUFFER, LBUFFER, RBUFFER, and CURSOR expose to a widget, and a widget that reruns the current command every two seconds, aliases included."
og:title: "Hacking Your Zsh Terminal with Custom Widgets"
og:description: "How to turn Zsh functions into keyboard shortcuts with zle -N and bindkey, what BUFFER, LBUFFER, RBUFFER, and CURSOR expose to a widget, and a widget that reruns the current command every two seconds, aliases included."
---

*__Blog Post Publish Date:__ 2026/10/28*

---

# Hacking Your Zsh Terminal with Custom Widgets

This blog post explains how to create custom Zsh widgets: shell functions bound to keyboard shortcuts through the Zsh Line Editor (ZLE). It's the Zsh version of [Hacking Your Bash Terminal with Custom Widgets](/blog/2026/2026-10-25-gnu-readline-widgets.md), and it ends with the same widget that reruns the current command every two seconds.

## Understand the Basics

**ZLE** (Zsh Line Editor) is the part of Zsh that handles command-line editing, the Zsh counterpart of GNU Readline in Bash. A **ZLE widget** is a function that ZLE runs when you press its key. You write a Zsh function, register it as a widget with [`zle -N`](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#index-zle), and bind it to a key with [`bindkey`](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#Zle-Builtins-1).

While a widget runs, ZLE gives it [special parameters](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#User_002dDefined-Widgets). The four main ones are:

- [BUFFER](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#index-BUFFER): the whole content of the command line.
- [CURSOR](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#index-CURSOR): the cursor position, as an offset into `BUFFER`.
- [LBUFFER](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#index-LBUFFER): the part of the line left of the cursor.
- [RBUFFER](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#index-RBUFFER): the part of the line right of the cursor.

Unlike Bash, Zsh gives you `LBUFFER` and `RBUFFER` directly, so inserting text at the cursor is as simple as `LBUFFER+="text"`.

To see them in practice, create a function called `debug-hook-variables` that prints all four, register it, and bind it to `Ctrl+x`:

```zsh
# zsh function for debugging reserved variables
function debug-hook-variables() {
  echo 
  echo ">>> BUFFER:   $BUFFER"
  echo ">>> RBUFFER:  $RBUFFER"
  echo ">>> LBUFFER:  $LBUFFER"
  echo ">>> CURSOR:   $CURSOR"
}

# register the function as a ZLE widget
zle -N debug-hook-variables

# check if "debug-hook-variables" are registered as widget
zle -al | grep debug-hook-variables

# define "Ctrl+x" shortcut for "debug-hook-variables" widget
bindkey '^X' debug-hook-variables

# list all widgets with shortcut defined
bindkey -L
```

Now type something at the prompt and press `Ctrl+x`. For example, with the cursor right after `definitely`, the output is:

```zsh
$ definitely| maybe  # press `Ctrl+x`

>>> BUFFER:   definitely maybe
>>> RBUFFER:   maybe
>>> LBUFFER:  definitely
>>> CURSOR:   10
```

`RBUFFER` starts with the space after `definitely`, and `CURSOR` is 10 because `definitely` has 10 characters.

> _In the default emacs keymap, `Ctrl+x` is also the prefix of several built-in bindings, such as `Ctrl+x Ctrl+e` in many setups. Binding `Ctrl+x` alone replaces that prefix. If you use those bindings, choose another key._

## Practical Example: Repeated Command Execution

Now a useful widget: an alternative to [`watch`](https://man7.org/linux/man-pages/man1/watch.1.html). `watch` runs its command in a new `sh -c`, so your aliases, such as `kgp`, aren't available (see this [Stack Overflow thread](https://stackoverflow.com/questions/54814543/bash-how-to-use-an-alias-command-in-combination-with-watch)). This widget runs whatever is on the command line every two seconds when you press `Ctrl+x`, in your current shell, so aliases work.

```zsh
function repeat-command-widget() {
  while true; do
    clear
    eval "$BUFFER"
    sleep 2
  done
}

zle -N repeat-command-widget
bindkey '^X' repeat-command-widget
```

To test it, type a command and press `Ctrl+x`:

```zsh
kgp     
### press `Ctrl+x`
### stop execution by `Ctrl+c`
```

`kgp` runs every two seconds until you press `Ctrl+c`, just like `watch "kubectl get pods"`.

### How to Register the Widget

Built-in ZLE widgets only need a `bindkey` line. A custom widget also needs its function and the `zle -N` registration, so put all three in `~/.zshrc`:

```zsh
# ~/.zshrc

# define the function
function repeat-command-widget() {
  while true; do
    clear
    eval "$BUFFER"
    sleep 2
  done
}

# register funtion as a widget
zle -N repeat-command-widget

# define Ctrl+x to execute "repeat-command-widget" command
bindkey '^X' repeat-command-widget
```

The `Ctrl+x` shortcut is then available in every new Zsh session.

## Where to Go From Here

Widgets turn any repetitive edit or command into one key press. Many Zsh plugins are widgets too: [fzf](/blog/2024/2024-04-21-fzf.md) binds its history, file, and directory search as ZLE widgets, and zsh-autosuggestions, which I use in my [ZSH + Starship setup](/blog/2024/2024-02-08-starship-zsh.md), works by wrapping the built-in ones.

## Key Takeaways

- ZLE is the Zsh line editor. A widget is a function that ZLE runs when you press its key.
- Register a function as a widget with `zle -N name`, then bind it with `bindkey '^X' name`. Check it with `zle -al` and `bindkey -L`.
- Inside a widget, `BUFFER` holds the command line, `CURSOR` the cursor offset, and `LBUFFER` and `RBUFFER` the text left and right of the cursor.
- `watch` runs its command in a new shell, so aliases fail. A widget that `eval`s `$BUFFER` in a loop runs in your shell, so they work.
- Put the function, `zle -N`, and `bindkey` in `~/.zshrc`.

## References

- [Zsh Line Editor: zle and bindkey builtins (Zsh manual)](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#Zle-Builtins-1)
- [Zsh Line Editor: user-defined widgets and their parameters (Zsh manual)](https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html#User_002dDefined-Widgets)
- [watch (Linux man pages)](https://man7.org/linux/man-pages/man1/watch.1.html)

*I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Hacking Your Zsh Terminal with Custom Widgets",
      "description": "How to turn Zsh functions into keyboard shortcuts with zle -N and bindkey, what BUFFER, LBUFFER, RBUFFER, and CURSOR expose to a widget, and a widget that reruns the current command every two seconds, aliases included.",
      "datePublished": "2026-10-28",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-10-26-zsh-widgets/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-10-26-zsh-widgets/",
      "keywords": ["Zsh", "ZLE", "zle -N", "bindkey", "terminal widgets"],
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
        {"@type": "ListItem", "position": 3, "name": "Hacking Your Zsh Terminal with Custom Widgets"}
      ]
    }
  ]
}
</script>
```

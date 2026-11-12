---
tags: bash, readline, terminal
date: "2026-10-25"
category: Linux
author: Carlos Neto
title: "Hacking Your Bash Terminal with Custom Widgets"
description: "How to turn Bash functions into keyboard shortcuts with bind -x, what READLINE_LINE and READLINE_POINT expose to them, and a widget that reruns the current command every two seconds, aliases included."
myst:
  html_meta:
    description: "How to turn Bash functions into keyboard shortcuts with bind -x, what READLINE_LINE and READLINE_POINT expose to them, and a widget that reruns the current command every two seconds, aliases included."
og:title: "Hacking Your Bash Terminal with Custom Widgets"
og:description: "How to turn Bash functions into keyboard shortcuts with bind -x, what READLINE_LINE and READLINE_POINT expose to them, and a widget that reruns the current command every two seconds, aliases included."
---

*__Blog Post Publish Date:__ 2026/10/25*

---

# Hacking Your Bash Terminal with Custom Widgets

This blog post explains how to create custom Bash widgets: Bash functions bound to keyboard shortcuts through the GNU Readline library. It continues [GNU Readline: The Magic Behind Terminal Autocomplete](/blog/2026/2026-10-18-gnu-readline-foundation.md), and ends with a widget that reruns the current command every two seconds.

## Understand the Basics

A **widget** is a function bound to a key that runs while you are editing the command line. In Bash, you write a function and bind it to a shortcut with `bind -x`, documented with the other [Bash builtins](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html).

When Bash runs a function through `bind -x`, it sets some [Bash variables](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html) for it. The two that matter most are:

- [READLINE_LINE](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fLINE): the whole content of the command line.
- [READLINE_POINT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fPOINT): the cursor position, as an offset into `READLINE_LINE`.

The function can read them, and if it changes them, Bash updates the command line when the function returns.


To see them in practice, create a function called `debug-hook-variables` that prints both, and bind it to `Ctrl+x`:

```bash
### bash function for debugging reserved variables
debug-hook-variables() {
  echo ">>> READLINE_LINE: $READLINE_LINE"
  echo ">>> READLINE_POINT: $READLINE_POINT"
}

### "\C-x" is the code for `Ctrl+x` shortcut
bind -x '"\C-x": debug-hook-variables'  
```

Now type something at the prompt and press `Ctrl+x`. For example, with the cursor right after `definitely`, the output is:

```bash
$ definitely| maybe  # press `Ctrl+x`

>>> READLINE_LINE: definitely maybe
>>> READLINE_POINT: 10
```

`definitely` has 10 characters, so the cursor is at offset 10. Bash also sets [READLINE_ARGUMENT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fARGUMENT) and [READLINE_MARK](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fMARK), but they're only needed in more advanced widgets.

> _`Ctrl+x` is also the prefix of several default Readline bindings, such as `Ctrl+x Ctrl+e` to edit the command in your editor. Binding `Ctrl+x` alone replaces that prefix in the current session. If you use those bindings, choose another key._

## Practical Example: Repeated Command Execution

Now a useful widget: an alternative to [`watch`](https://man7.org/linux/man-pages/man1/watch.1.html). `watch` runs its command in a new `sh -c`, so your aliases, such as `kgp`, aren't available (see this [Stack Overflow thread](https://stackoverflow.com/questions/54814543/bash-how-to-use-an-alias-command-in-combination-with-watch)). This widget runs whatever is on the command line every two seconds when you press `Ctrl+x`, in your current shell, so aliases work:

```bash
repeat-command-widget() {
  while true; do
    clear
    eval "$READLINE_LINE"
    sleep 2
  done
}

bind -x '"\C-x": repeat-command-widget'
```

To test it, type a command and press `Ctrl+x`:

```bash
kgp     
### press `Ctrl+x`
### stop execution by `Ctrl+c`
```

`kgp` runs every two seconds until you press `Ctrl+c`, just like `watch "kubectl get pods"`.

### How to Register the Widget

Bindings to built-in Readline functions go in `~/.inputrc`. A custom Bash widget is shell code, so the function and its `bind -x` go in `~/.bashrc`:

```bash
# ~/.bashrc

repeat-command-widget() {
  while true; do
    clear
    eval "$READLINE_LINE"
    sleep 2
  done
}

bind -x '"\C-x": repeat-command-widget'
```

The `Ctrl+x` shortcut is then available in every new Bash session.

## Where to Go From Here

Widgets let you turn any repetitive edit or command into a single key press. Zsh has the same idea with its own line editor, ZLE, and I show the Zsh version of this widget in [Hacking Your Zsh Terminal with Custom Widgets](/blog/2026/2026-10-26-zsh-widgets.md). If you'd rather use ready-made widgets, [fzf](/blog/2024/2024-04-21-fzf.md) ships widgets for history, file, and directory search.

## Key Takeaways

- `bind -x '"KEY": function'` runs a Bash function when you press `KEY`.
- Inside the function, `READLINE_LINE` holds the command line and `READLINE_POINT` the cursor offset. Changing them changes the command line.
- `watch` runs its command in a new shell, so your aliases don't work there. A widget that `eval`s `READLINE_LINE` in a loop runs in your shell, so they do.
- Built-in Readline bindings go in `~/.inputrc`. Custom widgets are shell code, so they go in `~/.bashrc`.
- `Ctrl+x` is a prefix for default Readline bindings. Binding it alone replaces them.

## References

- [Bash builtins: bind (GNU Bash manual)](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html)
- [Bash variables: READLINE_LINE and READLINE_POINT (GNU Bash manual)](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html)
- [bind (SS64)](https://ss64.com/bash/bind.html)
- [watch (Linux man pages)](https://man7.org/linux/man-pages/man1/watch.1.html)

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
      "headline": "Hacking Your Bash Terminal with Custom Widgets",
      "description": "How to turn Bash functions into keyboard shortcuts with bind -x, what READLINE_LINE and READLINE_POINT expose to them, and a widget that reruns the current command every two seconds, aliases included.",
      "datePublished": "2026-10-25",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-10-25-gnu-readline-widgets/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-10-25-gnu-readline-widgets/",
      "keywords": ["Bash", "GNU Readline", "bind -x", "READLINE_LINE", "terminal widgets"],
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
        {"@type": "ListItem", "position": 3, "name": "Hacking Your Bash Terminal with Custom Widgets"}
      ]
    }
  ]
}
</script>
```

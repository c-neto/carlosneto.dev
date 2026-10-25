---
tags: bash, linux, terminal
date: "2026-10-20"
category: Linux
---

*__Blog Post Publish Date:__ 2026/10/25*

# Hacking Your Bash with Custom Widgets

This blog post is an extension of [GNU Readline: The Magic Behind Terminal Autocomplete](./2026-10-18-gnu-readline-foundation.md). Here, I explain how to create custom Bash widgets by registering Bash functions to keyboard shortcuts powered by the GNU Readline library.

## Understand the Basics

The idea is simple: you create a Bash function and register it to a custom keyboard shortcut using the [bind](https://ss64.com/bash/bind.html) command. There are some [special Bash variables](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#Bash-Variables-1) that are made available to Bash functions when they are called using the `bind -x` command. The two main variables in this case are: [READLINE_LINE](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fLINE) that is the entire contents of the command line, and [READLINE_POINT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fPOINT) that is the cursor position, represented as an integer offset into `READLINE_LINE`. 


To understand these variables in practice, let's create a function called `debug-hook-variables` and bind it to the `Ctrl+x` shortcut. This function will print the values of the two variables:

```bash
debug-hook-variables() {
  echo ">>> READLINE_LINE: $READLINE_LINE"
  echo ">>> READLINE_POINT: $READLINE_POINT"
}

bind -x '"\C-x": debug-hook-variables'
```

Now, type anything at your prompt and press `Ctrl+x`. In this example, with your cursor positioned after `definitely`, the output will be:

```text
$ definitely maybe

>>> READLINE_LINE: definitely maybe
>>> READLINE_POINT: 11
```

> _There are other variables, such as [READLINE_ARGUMENT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fARGUMENT) and [READLINE_MARK](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fMARK), that are also made available to Bash functions. However, their usage is less straightforward and is typically relevant to more advanced use cases._

## Practical Example: Repeated Command Execution

Now, let's implement an alternative to the [`watch`](https://man7.org/linux/man-pages/man1/watch.1.html) command. The `watch` command can behave unexpectedly when executing aliases such as `kgp`. The goal of this widget is to execute a command repeatedly every two seconds when you press `Ctrl+x`, while supporting aliases.

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

You can test the widget by typing the following command and pressing `Ctrl+x`:

```bash
kgp
```

### How to Register the Widget

Built-in Readline widgets can be configured in the `~/.inputrc` file. For custom Bash widgets, we need to register the function and its keyboard shortcut in the `~/.bashrc` file.

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

The custom `Ctrl+x` shortcut will be available in new Bash sessions.

## Conclusion

It is important to understand that Bash also supports features that are available in Zsh and Fish. I'm not saying Bash is better or that you shouldn't use Fish or Zsh. My point is that you don't need to switch shells just because another shell offers features you like. Understanding how these mechanisms work behind the scenes expands your possibilities and helps you customize your terminal to suit your needs.

## Links

- GNU Readline foundation: [https://carlosneto.dev/blog/2026/2026-10-18-gnu-readline-foundation](https://carlosneto.dev/blog/2026/2026-10-18-gnu-readline-foundation)
- Bash `bind` builtin: [https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html)
- Bash variables (`READLINE_LINE`, `READLINE_POINT`): [https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html)

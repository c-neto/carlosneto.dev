---
tags: bash, linux, terminal
date: "2026-10-25"
category: Linux
---

*__Blog Post Publish Date:__ 2026/10/25*

---

# Hacking Your Bash Terminal with Custom Widgets

This blog post is an extension of [GNU Readline: The Magic Behind Terminal Autocomplete](./2026-10-18-gnu-readline-foundation.md). Here, I explain how to create custom Bash widgets by registering Bash functions to keyboard shortcuts powered by the GNU Readline library.

## Understand the Basics

The idea is simple: you create a Bash function and register it to a custom keyboard shortcut using the [bind](https://ss64.com/bash/bind.html) command. There are some [Bash Reserved Variables](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#Bash-Variables-1) that are made available to Bash functions when they are called using the `bind -x` command. The two main variables in this case are [READLINE_LINE](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fLINE) that is the entire contents of the command line, and [READLINE_POINT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fPOINT) that is the cursor position, represented as an integer offset into `READLINE_LINE`. 


To understand these variables in practice, let's create a function called `debug-hook-variables` and bind it to the `Ctrl+x` shortcut. This function will print the values of the two variables:

```bash
### bash function for debugging reserved variables
debug-hook-variables() {
  echo ">>> READLINE_LINE: $READLINE_LINE"
  echo ">>> READLINE_POINT: $READLINE_POINT"
}

### "\C-x" is the code for `Ctrl+x` shortcut
bind -x '"\C-x": debug-hook-variables'  
```

Now, type anything at your prompt and press `Ctrl+x`. In this example, with your cursor positioned after `definitely` and pressed `Ctrl+x`, the output will be like:

```bash
$ definitely| maybe  # press `Ctrl+x`

>>> READLINE_LINE: definitely maybe
>>> READLINE_POINT: 11
```

There are other variables, such as [READLINE_ARGUMENT](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fARGUMENT) and [READLINE_MARK](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html#index-READLINE_005fMARK), that are also made available to Bash functions. However, their usage is less straightforward and is typically relevant to more advanced use cases.

## Practical Example: Repeated Command Execution

Now, let's implement an alternative to the [$ watch](https://man7.org/linux/man-pages/man1/watch.1.html) command that can behave unexpectedly when executing aliases such as `kgp` (more details in this [Stack Overflow thread](https://stackoverflow.com/questions/54814543/bash-how-to-use-an-alias-command-in-combination-with-watch)). The goal of this widget is to execute a command repeatedly every two seconds when you press `Ctrl+x`, while supporting aliases.

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
### press `Ctrl+x`
### stop execution by `Ctrl+c`
```

The `kgp` command is executed in a loop every two seconds until you press `Ctrl+c`, just like `watch "kubectl get pods"`.

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

## Links

- GNU Readline foundation: [https://carlosneto.dev/blog/2026/2026-10-18-gnu-readline-foundation](https://carlosneto.dev/blog/2026/2026-10-18-gnu-readline-foundation)
- Bash `bind` builtin: [https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html)
- Bash variables (`READLINE_LINE`, `READLINE_POINT`): [https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html)

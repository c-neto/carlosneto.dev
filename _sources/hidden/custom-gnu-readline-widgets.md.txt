---
tags: readline, bash, inputrc
date: ""
category: Linux
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---

# How to Build Your Own Custom GNU Readline Widgets

This blog post explains what GNU Readline is, how it edits your command line behind the scenes, and how to build your own custom bindings. It covers the `~/.inputrc` file, macros, and the `bind -x` trick in Bash that runs a shell function when you press a key. It includes hands-on examples you can paste in and test right away.

## The Itch, Again, But Outside Zsh

A while ago I wrote about [building custom Zsh widgets](/blog/custom-zsh-widgets) with ZLE. I liked how a few lines in `~/.zshrc` could fix the small annoyances I hit every day. Then I switched to a machine where the default shell was Bash, pressed my shortcuts out of habit, and nothing happened. ZLE is a Zsh thing. Bash does not have it.

But Bash still lets you edit the command line, recall history, and jump around with keyboard shortcuts. Something is clearly handling all of that. That something is **GNU Readline**, and it turns out you can customize it too. The model is different from ZLE, and once I understood it, I got most of my muscle memory back.

## What is Readline?

Readline is the line-editing library that a lot of programs use to read input from you. Bash is the obvious one, but it is not alone. `gdb`, `ftp`, the Python REPL, `psql`, and many other tools link against Readline. That is why `CTRL` + `A` jumps to the start of the line in all of them. They share the same editor.

So Readline is not a shell feature. It is a library sitting underneath many programs, and the key bindings you configure for it apply everywhere it is used. Configure it once, and `gdb` and the Python prompt pick it up for free.

That is the first big difference from Zsh. In Zsh, ZLE lives inside the shell and a widget is a shell function. In Readline, the editor lives in a shared library, so the bindings are configured in a separate file called `~/.inputrc`, and the real logic (in Bash) runs through a dedicated builtin.

## The inputrc File

Readline reads its configuration from `~/.inputrc` (and the system-wide `/etc/inputrc`). This file does two kinds of things: it sets variables that change editor behavior, and it binds keys.

A binding has the form `key: action`. The action is either a built-in Readline function name or a macro, which is a string in quotes that gets inserted as if you typed it.

```{code-block} text
:caption: ~/.inputrc

# bind Control-o to the built-in function that lists possible completions
Control-o: possible-completions

# a macro: Meta-s types "sudo " for you (Meta is usually ALT)
"\es": "sudo "

# jump history by prefix: type a few chars, then Up/Down searches matching history
"\e[A": history-search-backward
"\e[B": history-search-forward
```

To see every function you can bind, ask Bash:

```{code-block} bash
:caption: list bindable Readline functions

bind -l
```

To see what is currently bound, and in a form you can paste back into `~/.inputrc`:

```{code-block} bash
:caption: show current bindings

bind -P   # human-readable list
bind -p   # re-usable inputrc form
```

> <i class="fa-solid fa-circle-info"></i> **About key notation:**
>
> In `~/.inputrc`, `\C-` means `CTRL` and `\e` (or `\M-`) means `ALT` / `Meta`. So `\C-o` is `CTRL` + `O` and `\es` is `ALT` + `S`. You can discover the exact sequence a key sends by pressing `CTRL` + `V` and then the key. You can reload `~/.inputrc` without a new shell by pressing `CTRL` + `X` then `CTRL` + `R`.

## Macros Get You Far

A lot of what I wanted turned out to be a one-line macro. A macro binds a key to a string, and Readline types that string for you. You can include control characters in the string to move the cursor or run a function afterwards.

```{code-block} text
:caption: ~/.inputrc

# ALT + p: prepend sudo by jumping to the start of the line and typing "sudo "
"\ep": "\C-asudo \C-e"

# ALT + l: wrap the current line in a pipe to less
"\el": "\C-a$(\C-e) | less"
```

In the first one, `\C-a` moves to the beginning of the line (a built-in Readline function reached as a control char), then `sudo ` is typed, then `\C-e` jumps back to the end. No scripting, just composition of what Readline already does.

Macros are great for fixed text and cursor moves. But they cannot make decisions, read the current line, or run a command and use its output. For that, Bash has a better tool.## bind -x: Running a Shell Function

This is the real equivalent of a Zsh user widget. The Bash `bind` builtin has a `-x` option that binds a key sequence to a **shell command**:

```{code-block} bash
:caption: the shape of bind -x

bind -x '"\C-g": my-function'
```

When you press the key, Bash runs `my-function`, and it hands the function three special variables:

- __`READLINE_LINE`__: the entire contents of the command line. Change it and the line changes.
- __`READLINE_POINT`__: the cursor position, as an integer offset into `READLINE_LINE`.
- __`READLINE_MARK`__: the position of the mark (the other end of a selection).

This mirrors ZLE's `BUFFER` and `CURSOR` almost one to one. You mutate `READLINE_LINE` and `READLINE_POINT`, and Readline redraws the line to match. You do not print to the screen.

:::{note}
`bind -x` is a Bash feature, not a generic Readline one. Macros in `~/.inputrc` work in any program that uses Readline. The shell-function bindings below only work in Bash, so they go in `~/.bashrc`.
:::

## Hands-On: A Few Bindings I Actually Use

Every example below goes into `~/.bashrc`. After editing it, reload with `source ~/.bashrc` and try the shortcut.

:::{note}
All code from this post is in my dotfiles: <i class="fab fa-github"></i> _[c-neto/ansible-configure-fedora/files/dotfiles](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles)_
:::

### 1. Prepend sudo to the Current Line

The classic. You type a long command, get _permission denied_, and want `sudo` in front without retyping. Unlike the macro version above, this one checks first so it never stacks `sudo sudo`.

```{code-block} bash
:caption: ~/.bashrc

prepend-sudo() {
  if [[ $READLINE_LINE != "sudo "* ]]; then
    READLINE_LINE="sudo $READLINE_LINE"
    (( READLINE_POINT += 5 ))
  fi
}
bind -x '"\es": prepend-sudo'   # ALT + s
```

The `if` check avoids the double `sudo`. Adding `5` to `READLINE_POINT` moves the cursor past the `"sudo "` prefix so you keep editing where you were.

### 2. Insert the Output of the Last Command

This evaluates the previous command again and drops its output onto the line. Handy for reusing a path, an ID, or a hash you just printed.

```{code-block} bash
:caption: ~/.bashrc

insert-last-command-output() {
  local last
  last=$(fc -ln -1)                       # the previous command text
  READLINE_LINE+="$(eval "$last")"        # run it, append the output
  READLINE_POINT=${#READLINE_LINE}        # cursor to end of line
}
bind -x '"\eo": insert-last-command-output'   # ALT + o
```

`fc -ln -1` returns the text of the last command from history, `eval` runs it again, and the output is appended to the line.

> <i class="fa-solid fa-circle-info"></i> Be careful with this one. It _re-executes_ the previous command. Do not use it right after something with side effects, like a `kubectl delete`.

### 3. Wrap the Current Command in a for Loop

The one I built for myself. I prototype a command on one item, then want to run it over a list. This takes whatever is on the line and wraps it in a `for` loop skeleton, leaving the cursor ready to fill in the list.

```{code-block} bash
:caption: ~/.bashrc

wrap-in-for-loop() {
  local cmd="$READLINE_LINE"
  READLINE_LINE="for i in ; do ${cmd}; done"
  READLINE_POINT=9     # right after "for i in "
}
bind -x '"\ef": wrap-in-for-loop'   # ALT + f
```

It saves the current line, rebuilds `READLINE_LINE` with the loop template, and parks `READLINE_POINT` right after `for i in ` so you can type the list immediately.

### 4. Clear the Line and Keep It in History

Sometimes I want to abandon the current line but still find it later. This stashes the line into history, then clears it.

```{code-block} bash
:caption: ~/.bashrc

stash-line() {
  history -s "$READLINE_LINE"   # push current line into history
  READLINE_LINE=""
  READLINE_POINT=0
}
bind -x '"\eq": stash-line'   # ALT + q
```

## Testing and Debugging Your Bindings

A few things that saved me time:

- __Reload inputrc__: press `CTRL` + `X` then `CTRL` + `R` to re-read `~/.inputrc` in place. For `bind -x` functions in `~/.bashrc`, run `source ~/.bashrc`.
- __Check what a key is bound to__: `bind -q possible-completions` tells you which keys invoke a given function. `bind -p | grep sudo` finds your custom entries.
- __Find the real key sequence__: press `CTRL` + `V` then the key to see the escape sequence the terminal actually sends. This is the usual reason a binding "does nothing".
- __Mind who else grabs the key__: tools like fzf add their own Readline bindings. If your shortcut stops working, something else probably claimed it.

## Readline vs ZLE: When to Use Which

If you live in Zsh, ZLE is nicer to work with. Widgets are plain shell functions, the special variables feel native, and you can call other widgets with `zle`. I covered all of that in the [Zsh widgets post](/blog/custom-zsh-widgets).

Readline wins on reach. Because it is a shared library, a macro in `~/.inputrc` follows you into `gdb`, the Python REPL, `psql`, and anything else built on Readline. Bash's `bind -x` then gives you the scripting layer on top, scoped to Bash.

So I use both. ZLE on my Zsh machines, Readline on the servers where Bash is the default and I do not want to install anything.

## Conclusion (Author Opinion)

Readline looked more intimidating than ZLE at first, mostly because the configuration is split across `~/.inputrc` and `~/.bashrc` and the key notation is its own little language. But the core idea is the same as Zsh: you mutate the line buffer and the cursor, and the editor redraws. Macros cover the simple cases in one line, and `bind -x` covers everything else.

What I appreciate most is that it is honest work with no dependencies. No plugin manager, no framework, just a couple of files I already maintain, and the bindings come with me to every Readline program on the box. The `prepend-sudo` binding alone earns its keep, and the `for` loop wrapper is muscle memory now.

If you spend your days in Bash and keep retyping the same small corrections, start with a `~/.inputrc` macro, then graduate to `bind -x` when you need logic. Give it a try.

## Links

- GNU Readline manual: <https://www.gnu.org/software/readline/manual/readline.html>
- Readline init file (inputrc) syntax: <https://www.gnu.org/software/bash/manual/html_node/Readline-Init-File-Syntax.html>
- Bash `bind` builtin: <https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html>
- Bash variables (`READLINE_LINE`, `READLINE_POINT`): <https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html>
- My custom Zsh widgets post: <https://carlosneto.dev/blog/custom-zsh-widgets>
- My dotfiles: <https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles>

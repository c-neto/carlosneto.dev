---
tags: zsh, zle
date: ""
category: Linux
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---

# How to Build Your Own Custom Zsh Widgets

This blog post explains what Zsh widgets are, how the Zsh Line Editor (ZLE) works behind the scenes, and how to build your own custom widgets bound to keyboard shortcuts. It includes hands-on examples you can paste directly into your `~/.zshrc` and test right away.

## The Itch: Repeating the Same Keystrokes All Day

A while ago I wrote about [fzf](/blog/2024/2024-04-21-fzf) and how its Zsh widgets saved me from the tedious `$ command | grep` dance. That post left a question in my head: what exactly is a widget, and could I write my own?

Every day I type the same small corrections over and over. I forget `sudo` and have to go back to the start of the line. I want to wrap the current command in a loop. I want to insert the output of the last command without reaching for the mouse. These are tiny annoyances, but they add up. The kind of thing that gets on my nerves after the hundredth time.

Turns out Zsh already has the machinery to fix all of this. It is called ZLE, and once it clicks, writing a custom widget takes a few lines.

## What is a Widget?

In Zsh, almost everything you do at the prompt is handled by a **widget**. Moving the cursor, deleting a word, searching history, completing a command, accepting the line when you press `Enter`. All of these are widgets.

ZLE (Zsh Line Editor) is the component that reads your keystrokes and edits the command line. When you press a key, ZLE looks up which widget that key is bound to and runs it. The `bindkey` command is the bridge between a key sequence and a [text](zsh-custom-widgets.md)widget.

You can list every widget available in your shell with:

```zsh
zle -al
```

Widgets whose name starts with a dot (like `.accept-line`) are read-only system widgets that you cannot change. The rest are fair game.

To see your current key bindings, run `bindkey` alone. To print them as commands you could paste back into your `~/.zshrc`, use:

```zsh
bindkey -L
```

So a widget is just a named action. A **user-defined widget** is a shell function you register with ZLE so it can be bound to a key, exactly like the built-in ones.

## The Three Commands You Always Need

Building a custom widget comes down to three steps:

```zsh
autoload -U my-widget   # load a widget function from your $fpath
zle -N my-widget        # register the function as a new widget
bindkey '^G' my-widget  # bind it to a key sequence (here CTRL + G)
```

- __`autoload -U`__: finds a file named after the widget in your `$fpath` and makes it available. You only need this when the widget lives in a separate file. If you define the function directly in `~/.zshrc`, you can skip it.
- __`zle -N`__: the important one. It takes a regular shell function and registers it as a **new** ZLE widget so it can edit the command line.
- __`bindkey`__: assigns the widget to a key sequence.

When you define the function inline in your `~/.zshrc`, the recipe shrinks to two commands: define the function, then `zle -N` and `bindkey`.

> <i class="fa-solid fa-circle-info"></i> **About key sequences:**
>
> In `bindkey`, `^` means `CTRL`, so `^G` is `CTRL` + `G`. The escape character `\e` (or `^[`) represents `ALT` / `Meta`, so `\e.` is `ALT` + `.`. You can discover the exact sequence a key sends by pressing `CTRL` + `V` and then the key.

## Talking to the Command Line: The Special Variables

A widget edits the command line through a set of special variables that ZLE keeps in sync while your function runs. These are the ones I reach for most:

- __`BUFFER`__: the entire command line as a string.
- __`LBUFFER`__: everything to the left of the cursor.
- __`RBUFFER`__: everything to the right of the cursor.
- __`CURSOR`__: the cursor position, as an integer offset into `BUFFER`.

Change any of these inside the widget and ZLE redraws the line to match. That is the whole trick. You do not print anything to the screen. You mutate the buffer and ZLE takes care of the rest.

You can also call other widgets from inside your own with `zle widget-name`, which lets you compose behavior on top of the built-ins.

## Hands-On: A Few Widgets I Actually Use

Enough theory. Let me show the widgets that scratched my original itch. Every example below goes straight into `~/.zshrc`. After editing it, reload with `source ~/.zshrc` and try the shortcut.

:::{note}
All code from this post is in my dotfiles: <i class="fab fa-github"></i> _[c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/blob/main/files/dotfiles/.zshrc)_
:::

### 1. Prepend sudo to the Current Line

The classic. You type a long command, hit `Enter`, and get _permission denied_. Instead of retyping it, this widget adds `sudo ` to the front of the line and nudges the cursor so you keep typing where you left off.

```{code-block} zsh
:caption: ~/.zshrc

prepend-sudo() {
  if [[ $BUFFER != "sudo "* ]]; then
    BUFFER="sudo $BUFFER"
    CURSOR+=5
  fi
}
zle -N prepend-sudo
bindkey '^[s' prepend-sudo  # ALT + S
```

The `if` check avoids stacking `sudo sudo` when you press the shortcut twice. `CURSOR+=5` moves the cursor forward by the five characters of `"sudo "` so the line keeps editing naturally.

### 2. Insert the Output of the Last Command

This one feels like magic the first time. It evaluates the previous command again and drops its output right where the cursor is. Useful when you want to reuse a path, an ID, or a hash you just printed.

```{code-block} zsh
:caption: ~/.zshrc

zmodload -i zsh/parameter

insert-last-command-output() {
  LBUFFER+="$(eval $history[$((HISTCMD-1))])"
}
zle -N insert-last-command-output
bindkey '^[o' insert-last-command-output  # ALT + O
```

It loads the `zsh/parameter` module to access the `$history` associative array, then appends the re-run output to `LBUFFER`, so the text lands to the left of the cursor.

> <i class="fa-solid fa-circle-info"></i> Be careful with this one. It _re-executes_ the previous command. Do not use it right after something with side effects, like a `kubectl delete`.

### 3. Delete a Whole Path Segment at Once

By default, `CTRL` + `W` deletes back to the previous whitespace, which treats a full path as one blob. Sometimes I want to delete just one directory of a path. This widget tweaks `WORDCHARS` for a single call so `/` becomes a word boundary.

```{code-block} zsh
:caption: ~/.zshrc

backward-delete-path-segment() {
  local WORDCHARS="*?_[]~=&;!#$%^(){}<>"
  zle backward-delete-word
}
zle -N backward-delete-path-segment
bindkey '^W' backward-delete-path-segment  # CTRL + W
```

Notice the pattern: the widget sets a `local` variable, then delegates the real work to the built-in `backward-delete-word` widget with `zle`. You are not reimplementing deletion, you are wrapping it with different settings.

### 4. Wrap the Current Command in a for Loop

This is the one I built for myself. I often prototype a command on one item, then want to run it over a list. This widget takes whatever is on the line and wraps it in a `for` loop skeleton, leaving the cursor ready to fill in the list.

```{code-block} zsh
:caption: ~/.zshrc

wrap-in-for-loop() {
  local cmd="$BUFFER"
  BUFFER="for i in ; do ${cmd}; done"
  CURSOR=10
}
zle -N wrap-in-for-loop
bindkey '^[f' wrap-in-for-loop  # ALT + F
```

It saves the current line, rebuilds `BUFFER` with the loop template, and parks `CURSOR` right after `for i in ` so you can type the list immediately. Nothing fancy, just the special variables doing their job.

## Testing and Debugging Your Widgets

A couple of things that saved me time while experimenting:

- __Reload without a new shell__: run `source ~/.zshrc` after each change. No need to close the terminal.
- __Confirm the binding stuck__: `bindkey | grep my-widget` shows which key is mapped to your widget.
- __Confirm ZLE knows the widget__: `zle -la | grep my-widget` lists it among the registered widgets.
- __Mind the key sequence__: if a shortcut does nothing, it is usually because the terminal sends a different sequence than you expected, or another tool (like fzf or a plugin) already grabbed that key. Press `CTRL` + `V` then the key to see the real sequence.

## Conclusion (Author Opinion)

I went into this expecting ZLE to be some arcane corner of Zsh, and it turned out to be refreshingly simple. A widget is just a function. You mutate `BUFFER` and `CURSOR`, register it with `zle -N`, bind a key, and that is it.

What I like most is that it is honest work with no dependencies. No plugin manager, no framework, just a few lines in a file I already maintain. The `prepend-sudo` widget alone has paid for the time I spent learning this, and the `for` loop wrapper is now muscle memory.

It is not a replacement for a tool like fzf when you need interactive searching. The two actually complement each other, since fzf ships its features _as_ ZLE widgets. But for those tiny, personal, repetitive edits that only bother you, writing your own widget is the right fix.

Give it a try. Start with `prepend-sudo`, feel how fast the loop is, and you will end up with a handful of your own before long.

## Links

- `$ zsh` reference: <https://www.zsh.org/>
- Zsh ZLE manual: <https://zsh.sourceforge.io/Doc/Release/Zsh-Line-Editor.html>
- Mastering Zsh - Widgets: <https://github.com/rothgar/mastering-zsh/blob/master/docs/helpers/widgets.md>
- My fzf blog post: <https://carlosneto.dev/blog/2024/2024-04-21-fzf>
- My custom Zsh configuration in `~/.zshrc`: <https://github.com/c-neto/ansible-configure-fedora/blob/main/files/dotfiles/.zshrc>

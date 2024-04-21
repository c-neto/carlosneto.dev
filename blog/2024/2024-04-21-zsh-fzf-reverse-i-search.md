---
tags: zsh
date: "2024-04-21"
category: Linux
---

*__Blog Post Publish Date:__ 2024/04/21*

---

# FZF: A Smart Reverse History Search

This blog post covers how to use the [FZF - Fuzzy Finder](https://github.com/junegunn/fzf?tab=readme-ov-file) in [ZSH](https://www.zsh.org/) as an alternative to _reverse-i-search_ widget.

## My journey from __reverse-i-search__ until __fzf-history-widget__

Remember executed commands can be a bored task, mainly in the current days there are so many tools and differents stack technologies each one with their your specific commands lines programs. For help in this need, the shells like Zsh, Fish, and Bash implements a widget for interactive searching executed commands based on terms saved in the history file.

In Zsh is implemented _reverse-i-search_ widget by default, called by `CTRL` + `R`. The default implementaion is good, but the commands remenbering results is limited by one result, and you need to press `CTRL` + `R` again to see next results. This behavior can be a problem if you need to remember a commands using little terms, large commands, and commands with multiple executions with differents arguments, letting you to press `CTRL` + `R` many times.

I searched by alternatives to better my experience over the _reverse-i-search_ widget. I checked Fish implementation, and I liked the implementation. The Fish show a interactive menu with commands executed matched by typed term. It is really nice! and turns my challenge to replicated the behavior in the Zsh.

I searched ways to replicate the Fish behavior in Zsh. After some research days, I found the amazing project [FZF - Fuzzy Finder](https://github.com/junegunn/fzf). FZF is a command-line fuzzy finder written in Go, designed to help users quickly search and select items from large datasets and files. There are some shells widgets available to search files, directories, and __all I want, a widget dedicated to reverse history search__.

> <i class="fa-solid fa-circle-info"></i> There are widgets available for Fish, Bash, Zsh. You can check the implementaion in the following directory in the GitHub project https://github.com/junegunn/fzf/tree/master/shell.

## How to Setup

The first step, install fzf:

::::{grid}

:::{grid-item-card}
```{code-block} bash
# if Linux (Fedora)
$ dnf install fzf
```
:::

:::{grid-item-card}
```{code-block} bash
# if MacOS
$ brew install fzf
```
:::

::::

After that, you need to load the fzf widgets and keybindings.

```bash
$ curl -s https://raw.githubusercontent.com/junegunn/fzf/master/shell/key-bindings.zsh > fzf-key-bindings.zsh
$ source fzf-key-bindings.zsh
```

> <i class="fa-solid fa-circle-info"></i> After fzf versions 0.48.0, you can load the keybindings and completions with `$ eval (fzf --zsh)`.

To check the keybindings configuration in the previous step, you can run the following command:

```bash
$ bindkey -a | grep fzf

"^R" fzf-history-widget  # CTRL + R: reverse history search
"^T" fzf-file-widget     # CTRL + T: search files
"^[c" fzf-cd-widget      # ALT  + C: search directories
```

You can customize the fzf display by `FZF_CTRL_R_OPTS` environment variable value. I configured a vertical window to show the full command wrapped (useful in large command rendering).

```bash
export FZF_CTRL_R_OPTS="--height 100% --layout reverse --preview 'echo {}' --preview-window=wrap"
```

## Results

The next video, show the results of the previous step.

<video width="100%" height="100%" controls>
    <source src="/_static/2024/2024-04-21/fzf-setup.mp4" type="video/mp4">
    Your browser does not support the video tag.
</video>

## Conclusion (Author Opinion)

The fzf is an amazing, performative, and portable project. Certainly, It is a good alternative for the default search history widget for Fish and Zsh. The results are incredibly blazingly fast, even in large history file commands. The customization by environment variable `FZF_CTRL_R_OPTS` is good for expanding the possibilities based on your needs.

I really like the fzf. I approve and recommend the usage.

## Links

- My custom fzf configuration in `~/.zshrc`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/.zshrc)
- fzf project: https://github.com/junegunn/fzf/tree/master/shell

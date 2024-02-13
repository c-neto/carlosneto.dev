---
tags: systemd
date: "2024-02-08"
category: Linux
---

*__Blog Post Publish Date:__ 2024/02/08*

---

# ZSH + Starship: A Productivity Masterpiece

This blog post covers my prompt customization experience, favorite [ZSH](https://www.zsh.org/) Plugins, [options](https://zsh.sourceforge.io/Doc/Release/Options.html), and [Starship](https://starship.rs/) configuration. Finally, I introduce a simple guide to configure my custom theme from scratch.

## My Prompts Customization Experiences

Productivity is a topic that I definitely like. For long time, I used the raw Terminal over Bash, It is force me to memorize the commands, but the productivity is not so good. I felt that I need to improve my Terminal setup to focus in productivity.

Because my Python expertise, I tested the [xonsh](https://xon.sh/) around 6 months. The [xonsh](https://xon.sh/) is a superset of Python with additional shell primitives that you are used to from Bash. The union Bash + Python brings the productive of the simplicity syntax of the Python with the possibilities of the Bash, but the debug is a chaos (_imagine a list comprehension in Python syntax with dicts and environments variables in Bash syntax..._).

I needed come back the real world again, then I gave a chance for [ZSH](https://www.zsh.org/), a advanced and highly customizable command-line interface with enhanced productivity features and a large Plugins. It greatly appealed to me, mainly when I tested the [Spaceship](https://github.com/spaceship-prompt/spaceship-prompt) a _"minimalistic, powerful and extremely customizable Zsh prompt"_, and the [oh-my-zsh](https://ohmyz.sh/) framework that provides a simple way to manage Plugins and Themes. I believed I had reached a stable terminal configuration with a good balance between productivity and simplicity, but in the MacOs workstation, the input and startup delay of the commands got on my nerves.

I searched improvements tips in the Blog Posts and Youtube videos, but the result don't satisfied myself. Then, I opted to install the Plugins manually avoiding the [oh-my-zsh](https://ohmyz.sh/), and I tested the [Starship](https://starship.rs/) (in my words: "_... a [Spaceship](https://github.com/spaceship-prompt/spaceship-prompt) in Rust, blazing-fast, with many stars in the GitHub..._").

The results blew my mind. I had no efforts to rewrite my theme configuration from the [Spaceship](https://github.com/spaceship-prompt/spaceship-prompt) to [Starship](https://starship.rs/), and the performance works a expected.

## My ZSH Favorite Plugins

There are so many plugins for [ZSH](https://www.zsh.org/). Usually, these plugins it is managed by [oh-my-zsh](https://ohmyz.sh/). I used the [oh-my-zsh](https://ohmyz.sh/) to make easy the Plugins world exploration, but I could notice that Plugins are simple single scripts files with predefined set of the functions and routines. When I found the Plugins that make sense for me, I installed them standalone to remove a possible delay source from the [oh-my-zsh](https://ohmyz.sh/).

I will present in the following sub-topics, my indispensable [ZSH](https://www.zsh.org/) Plugins.

> _I only used the plugin that really make the difference in my work. Thus, don't feel strange about the low number._

### » `zsh-autosuggestions`: Commands Recall Assistant

No doubts, this is my favorite Plugin. This Plugin suggests command completion based on history. It is amazing.

![](image-1.png)

> <i class="fa-solid fa-link"></i> More Details: <https://github.com/zsh-users/zsh-autosuggestions>

---

### » `zsh-syntax-highlighting`: Valid Commands by Color

This Plugin help to detect the typo in the commands typing in real time. When command is correctly typed, the color is Green, otherwise, the color is Red.

![](image-2.png)

> <i class="fa-solid fa-link"></i> More Details: <https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/>

---

### » `kubectl`: k alias for kubectl

This plugin adds completion for the Kubernetes, as well as some aliases for common kubectl commands.

For example:

```{code-block} bash
# shortcut for: kubectl get pods
$ kgp

# shortcut for: kubectl delete cm foobar-config-map
$ kdelcm foobar-config-map

# shortcut for: kubectl get cronjob
$ kubectl get cj
```

> <i class="fa-solid fa-link"></i> More Details: <i class="fab fa-github"></i> [ohmyzsh/ohmyzsh/plugins/kubectl](https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/kubectl)

---

## My Starship Configuration

The simplicity is elegance. I customized my Starship prompt with only attributes of the tools important for me.

- [aws](https://starship.rs/config/#aws): Only the profile name of the my AWS session;
- [git](https://starship.rs/config/#git-branch): Only the Branch, no more info;
- [python](https://starship.rs/config/#python): The current activated virtualenv;
- [kubernetes](https://starship.rs/config/#kubernetes): The Kubernetes context name. Based on the name, I applied the different styles to explicit the study, tests, and production workloads.

## My favorite ZSH options (_setopt_)

Some behaviors in the [ZSH](https://www.zsh.org/) can be enabled based on list of the [ZSH Options](https://zsh.sourceforge.io/Doc/Release/Options.html). Check the options that I enabled:

- `INTERACTIVE_COMMENTS`: Enable comments "#" expressions in the prompt shell;
- `APPEND_HISTORY`: Append new history entries to the history file;
- `INC_APPEND_HISTORY`: Save each command to the history file as soon as it is executed;
- `HIST_IGNORE_DUPS`: Ignore recording duplicate consecutive commands in the history;
- `HIST_IGNORE_SPACE`: Ignore commands that start with a space in the history;
- `SHARE_HISTORY`: Share the command history among multiple ZSH sessions.

> <i class="fa-solid fa-link"></i> More Details: <https://zsh.sourceforge.io/Doc/Release/Options.html>

## How to Setup My ZSH From Scratch

You can check my `.zshrc` and `starship.toml` in my GitHub in the Following Links:

- `.zshrc`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/.zshrc)
- `starship.toml`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/starship.toml](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/starship.toml)

---

- `1`: Install the [ZSH](https://www.zsh.org/) with your package manager.

```{code-block} bash
# if fedora
$ dnf install zsh

# if macos
$ brew install zsh
```

- `2`: Install the [Starship](https://starship.rs/):

```{code-block} bash
$ curl -sS https://starship.rs/install.sh | sh
```

- `3`: Create a directory in your home to save the ZSH plugins and the Starship configuration:

```{code-block} bash
$ mkdir $HOME/.config
$ mkdir $HOME/.my-custom-zsh/
```

- `4`: Download my custom starship configuration:

```{code-block} bash
$ curl -XGET https://raw.githubusercontent.com/c-neto/ansible-configure-fedora/main/files/dotfiles/starship.toml $HOME/.config/starship.toml
```

- `5`: Install the plugins manually:

```{code-block} bash
# k alias
$ curl -XGET https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/kubectl/kubectl.plugin.zsh > $HOME/.my-custom-zsh/kubectl.plugin.zsh

# zsh-syntax-highlighting
$ git clone --depth 1 https://github.com/zsh-users/zsh-syntax-highlighting.git $HOME/.my-custom-zsh/zsh-syntax-highlighting

# zsh-autosuggestions
$ git clone --depth 1 https://github.com/zsh-users/zsh-autosuggestions $HOME/.my-custom-zsh/zsh-autosuggestions
```

- `6`: Restart your terminal, the results will be like this:

![](image-3.png)

## Conclusion (Author Opinion)

Productivity is a dynamic goal, and tools must fit your current needs and continually may be changed to enhance processes based on demands.

Currently, for my DevOps routine, the combination of ZSH and Starship proves to be a balanced approach, offering a blend of performance, simplicity, productivity, and extendability.

## Links

- My dotfiles:
    - `.zshrc`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/.zshrc)
    - `starship.toml`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/starship.toml](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/starship.toml)
- ZSH Reference:
    - <https://www.zsh.org/>
    - <https://zsh.sourceforge.io/Doc/Release/Options.html>
- ZSH Plugins:
    - <https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/kubectl>
    - <https://github.com/zsh-users/zsh-autosuggestions>
    - <https://github.com/zsh-users/zsh-syntax-highlighting>
- Starship:
    - <https://starship.rs/>
    - <https://github.com/starship/starship>
- Other links:
    - <https://xon.sh/>
    - <https://ohmyz.sh/>
    - <https://github.com/spaceship-prompt/spaceship-prompt>

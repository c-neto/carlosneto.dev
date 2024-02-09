---
tags: systemd
date: "2024-02-08"
category: Linux
---

*__Blog Post Publish Date:__ 2024/02/08*

---

# ZSH + Starship: A Productivity Masterpiece

This blog post covers my experience in the prompts usage, my evolution until ZSH and Starship, and my setup configuration.

## About my Prompts Experiences

Productivity is a topic that I definitely like. I always look better ways to execute the bored daily tasks, mainly in the terminal. For long time in my tech life, I used the raw terminal over Bash, It is force me to memorize the commands, but the productivity is not so good. I felt the necessity in the new shell adoption, focused in productivity.

I adopted the Xonsh as my primary shell. It was a great and funny experience. The xonsh extend the shell commands base set with Python. I felt like a real _hackerman_ (_even if alternatives simple commands in the Bash performed exactly the same behavior_). The only limit my restriction, until the day that I wasn't understand that I'm doing. The union Bash + Python is funny, but is a chaos to debug (_to improve my position: Imagine the list comprehension with dicts and pipe grep... no more words is necessary._). 

I needed come back the real world again, then I gave a chance for zsh, which brings the productivity with several plugins, and the syntax almost the same the Bash. I really liked It, mainly when I tested the Spaceship (_"minimalistic, powerful and extremely customizable Zsh prompt"_), and the plugin manager oh-my-zsh, which makes simple installation and tests new plugins and utility commands. Finally, I had reached a stable terminal setup, a good balance between productivity and simplicity. 

Over the course of the months, the startup delay got on my nerves (_to be honest, in MacOs only, in my Fedora workstation everything to be right_). I had read some articles and Youtube videos about how to improve the performance, but the result don't satisfied myself. Then, I tested the Starship, in my words, is the "_Spaceship alternative in Rust, blazing-fast, rocket emoji, with many stars in the GitHub_". I tested, and the results blew my mind. I had no efforts to rewrite my plugins customizations from the Spaceship to Starship, and the performance is excellent, and all my problems were solved.

## How to Setup the 

I will explain how I configured my ZSH + Starship.

First step, it to install the zsh:

```{code-block} bash
$ dnf install zsh
```

Install the Starship:

```{code-block} bash
$ curl -sS https://starship.rs/install.sh | sh
```

Create a directory in your home to save the zsh plugin:

```{code-block} bash
$ mkdir $HOME/.config
```

Download my custom starship configuration:

```
curl -XGET https://raw.githubusercontent.com/c-neto/ansible-configure-fedora/main/files/dotfiles/starship.toml $HOME/.config/starship.toml
```

Install `$ k` alias for `$ kubectl`:

```{code-block} bash
$ curl -XGET https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/kubectl/kubectl.plugin.zsh > $HOME/.my-custom-zsh/kubectl.plugin.zsh
```

Install the ZSH plugin [zsh-autosuggestions](https://github.com/zsh-users/zsh-autosuggestions).

```{code-block} bash
$ git clone --depth 1 https://github.com/zsh-users/zsh-autosuggestions ~/.my-custom-zsh/zsh-autosuggestions
```

## Conclusion (Author Opinion)

Productivity is a target in movement. Tools that satisfies your need now, and process need to be improve based on demands. The ZSH + Starship today, for my DevOps routine is the good approach in balance of the perfomance + simplicity + productity + extensionable

## Links

- <https://starship.rs/>
- <https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles>

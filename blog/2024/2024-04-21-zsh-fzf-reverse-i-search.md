---
tags: zsh
date: "2024-04-21"
category: Linux
---

*__Blog Post Publish Date:__ 2024/04/28*

---

# fzf: The Life is Short to Pipe Grep

This blog post outlines the advantages of the [fzf](https://github.com/junegunn/fzf) (Fuzzy Finder CLI) and explains how to configure its [Zsh](https://www.zsh.org/) widgets.

## Searching in the Terminal - Bored Task

Remember executed commands can be a bored task, mainly in current days there are so many tools and differents stack technologies, each one their your specific commands lines programs. For help in this, the shells like Zsh, Fish, and Bash implements a widget for interactive commands history searching.

In Zsh is implemented _reverse-i-search_ widget by default, called by `CTRL` + `R`. The commands are showed limited by one result. You need to press `CTRL` + `R` again to see next results. This behavior can be a problem if you need to remember commands many times executed with differents arguments.

I searched by alternatives to better my experience over _reverse-i-search_ widget. I checked Fish implementation to get insights. The Fish launchs a menu with a list of the commands filtered by terms as you type. It was a good insight for me and I used it as my mainline for my Zsh customization.

It is leveages to research better alternatives for interactive search anything, not only to search history commands.

## Fuzzy Finders - The Solution

After a few days of research, I found an amazing project which solves my problems: [fzf — command-line fuzzy finder](https://github.com/junegunn/fzf). It is a cross-platform Fuzzy Finder command-line written in Go. But, what are A Fuzzy Finder?

Fuzzy Finder is a search tool that allows users to quickly and flexibly find files, directories, or other elements, even when they don't remember the precise names. It employs fuzzy matching to find results based on partial words, erratic characters, or typographical errors. Imagine you have a large list of items (like files, text lines, command history) and you need to find something within them quickly.

[fzf — command-line fuzzy finder](https://github.com/junegunn/fzf) filters the list of items as you type. This makes your searching much more efficient, avoiding `$ | grep` execution. It can receive output of the other commands for interative searching, for instance you can execute `$ kgp -A | fzf` to find pods in all Kubernetes cluster. In addition, it has some predefined shells widgets to search files, directories, and __search history commands__.

The next section will explain how to configure these widgets in Zsh.

> <i class="fa-solid fa-circle-info"></i> There are widgets available for Fish, Bash, Zsh. You can check the available implementations in [github.com/junegunn/fzf/shell](https://github.com/junegunn/fzf/tree/master/shell)

## How to Configure fzf Widgets in Zsh

The first step is to install fzf. There are some distinct ways to install it described in [fzf — installation section](https://github.com/junegunn/fzf/tree/master?tab=readme-ov-file#installation). Depending on the package manager on your workstation, the version available can be older. Thus, I will download and install the latest version available in GitHub Releases section.

```bash
# download the latest version (in a moment of the blog publish date, the latest version is 0.50.0)
$ wget https://github.com/junegunn/fzf/releases/latest/download/fzf-0.50.0-linux_amd64.tar.gz

# uncompress the donwloaded file to access the fzf binary
$ tar -xzvf fzf-0.50.0-linux_amd64.tar.gz

# check fzf binary execution
$ ./fzf --help

# move the binary to a folder present in your path
$ mv fzf ~/.local/bin/
```

You can get the widget setup source-code given the shell name as argument, for instance `--zsh`, `--fish`, and `--bash`. In this case, I will setup the widgets for Zsh.

```bash
# only available in 0.48.0 or later
$ source $(fzf --zsh)
```

Run the following command to check the keybindings are correctly loaded.

```bash
$ bindkey -a | grep fzf

"^R" fzf-history-widget  # CTRL + R: reverse history search
"^T" fzf-file-widget     # CTRL + T: search files
"^[c" fzf-cd-widget      # ALT  + C: search directories
```

You can customize the widgets fzf parameters through environment variables described in [fzf — environment variables](https://github.com/junegunn/fzf?tab=readme-ov-file#environment-variables--aliases). The _fzf-history-widget_ parametrization is defined in the `FZF_CTRL_R_OPTS` environment variable. Each widget has its own environments variables you can customize based on your needs. The following example demonstrates how to parametrize the _fzf-file-widget_ and _fzf-cd-widget_.

```bash
# CTRL + R: set vertical window for render the entire text of the command selected (useful in large command rendering).
export FZF_CTRL_R_OPTS="--height 100% --layout reverse --preview 'echo {}' --preview-window=wrap"

# ALT + C: set "fd-find" as directory search engine instead of "find" and exclude venv of the results during searching
export FZF_ALT_C_COMMAND="fd --type directory --exclue"

# ALT + C: put the tree command output based on item selected ("{}" will be replaced by item selected in fzf execution runtime)
export FZF_ALT_C_OPTS="--preview 'tree -C {}'"

# CTRL + T: set "fd-find" as search engine instead of "find" and exclude .git for the results
export FZF_CTRL_T_COMMAND="fd --exclude .git"

# CTRL + T: put the file content if item select is a file, or put tree command output if item selected is directory
export FZF_CTRL_T_OPTS="--preview '[ -d {} ] && tree -C {} || bat --color=always --style=numbers {}'"
```

The next section will present widgets executions preview.

> You can check my `~/.zshrc` file content in the following link. It contains my personal fzf parametrization:
> - <i class="fab fa-github"></i> [github.com/c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/blob/main/files/dotfiles/.zshrc)

## Results

- _fzf-history-widget_ executed by `CTRL` + `R`.

![fzf-history-widget execution print](/_static/2024/2024-04-21/results-1.png)

- _fzf-cd-widget_ executed by `ALT` + `C`.

![fzf-cd-widget execution print](/_static/2024/2024-04-21/results-2.png)

- _fzf-file-widget_ executed by `CTRL` + `T`.

![fzf-file-widget execution print](/_static/2024/2024-04-21/results-3.png)


## Conclusion (Author Opinion)

My research for improvements in searching history commands has yielded results that exceed my expectations. fzf opened my mind to understand what is Fuzzy Finder and the problem which resolves. It not limited to be command history searching only, it is a tool that you can search anything. It is really nice!

Certainly, I think it is a much better alternative to command history search widget default in Zsh, Bash, and Fish (_which already has a good history search widget_). The interactive searching are blazingly fast and customization expanding the possibilities based on your needs.

The productivity which fzf provides is really awesome! In a fact, that its justifies more than __59K stars__ in your GitHub repo.

I approve and recommend!

## Links

- fzf GitHub Repository: <https://github.com/junegunn/fzf/>
- skim, a fzf implemented in rust: <https://github.com/lotabout/skim>
- My custom fzf configuration in `~/.zshrc`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/.zshrc)

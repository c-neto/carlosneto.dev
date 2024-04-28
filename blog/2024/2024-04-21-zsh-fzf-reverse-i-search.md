---
tags: zsh
date: "2024-04-21"
category: Linux
---

*__Blog Post Publish Date:__ 2024/04/21*

---

# fzf: A Better Tool for History Commands Searching

This blog post outlines the advantages of the [fzf](https://github.com/junegunn/fzf) (Fuzzy Finder CLI) and explains how to configure its [Zsh](https://www.zsh.org/) widgets, especially the _fzf-history-widget_, which offers a better alternative than _reverse-i-search_.

## From __reverse-i-search__ To __fzf-history-widget__

Remember executed commands can be a bored task, mainly in current days there are so many tools and differents stack technologies, each one their your specific commands lines programs. For help in this, the shells like Zsh, Fish, and Bash implements a widget for interactive commands history searching.

In Zsh is implemented _reverse-i-search_ widget by default, called by `CTRL` + `R`. The default implementation is good, but the commands are showed limited by one result. You need to press `CTRL` + `R` again to see next results. This behavior can be a problem if you need to remember commands executed many times with differents arguments.

I searched by alternatives to better my experience over _reverse-i-search_ widget. I checked Fish implementation to get insights. The Fish launchs a menu with a list of the commands filtered by terms as you type. It was a good insight for me and I used it as my mainline for my Zsh customization.

After a few days of research, I found an amazing project: [fzf — command-line fuzzy finder](https://github.com/junegunn/fzf). It is a cross-platform command-line written in Go for interactive searching. Imagine you have a large list of items (like files, text lines, command history) and you need to find something within them quickly. fzf filters the list of items as you type. This makes your searching much more efficient, avoiding `$ | grep` execution. In addition, fzf has additional resources like integration with other commands and predefined shells widgets like search files, directories, and the __main interest point of this blog post: a widget dedicated to search history commands.__ 

The next section will explain how to configure these widget in the Zsh.

> <i class="fa-solid fa-circle-info"></i> There are widgets available for Fish, Bash, Zsh. You can check the implementations in the following directory in the GitHub project [github.com/junegunn/fzf/shell](https://github.com/junegunn/fzf/tree/master/shell)

## How to Configure fzf Widgets in Zsh

The first step is to install fzf. There are some distinct ways to install it described in the [fzf — installation section](https://github.com/junegunn/fzf/tree/master?tab=readme-ov-file#installation). Depending on the package manager on your workstation, the version available can be older. Thus, I will download and install the latest version available in GitHub Releases section.

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

fzf has source-code of the shell widgets embedded in a binary (only available in 0.48.0 or later). You can get the source-code given the shell name as argument, for instance `--zsh`, `--fish`, and `--bash`. In this case, I will load the widgets for Zsh.

```bash
$ source $(fzf --zsh)
```

Run the following command to check the keybindings are correctly loaded.

```bash
$ bindkey -a | grep fzf

"^R" fzf-history-widget  # CTRL + R: reverse history search
"^T" fzf-file-widget     # CTRL + T: search files
"^[c" fzf-cd-widget      # ALT  + C: search directories
```

You can customize the layout and others options of the fzf over some envioronment variables described in [fzf — environment variables](https://github.com/junegunn/fzf?tab=readme-ov-file#environment-variables--aliases). I will update the layout of the fzf when executed by _fzf-history-widget_. For this, I will set the `FZF_CTRL_R_OPTS` environment variable with some fzf parameters to launch a vertical window for to show the full command (useful in large command rendering).

```bash
export FZF_CTRL_R_OPTS="--height 100% --layout reverse --preview 'echo {}' --preview-window=wrap"
```

There are others options can you use to customize the behavior of the fzf. Check the following examples:

```bash
# ALT + C: set "fd-find" as directory search engine instead of "find" and exclude venv of the results during searching
export FZF_ALT_C_COMMAND="fd --type directory --exclue"

# ALT + C: put the tree command output based on item selected ("{}" will be replaced by item selected in fzf execution runtime)
export FZF_ALT_C_OPTS="--preview 'tree -C {}'"

# CTRL + T: set "fd-find" as search engine instead of "find" and exclude .git for the results
export FZF_CTRL_T_COMMAND="fd --exclude .git"

# CTRL + T: put the file content if item select is a file, or put tree command output if item selected is directory
export FZF_CTRL_T_OPTS="--preview '[ -d {} ] && tree -C {} || bat --color=always --style=numbers {}'"
```

The next section will present some prints of the fzf widgets execution configured with the presented parameters.

> You can check my `~/.zshrc` file content in the following link. It contains my personal fzf parametrization:
> - <i class="fab fa-github"></i> [github.com/c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/blob/main/files/dotfiles/.zshrc)

## Results

- _fzf-history-widget_ executed by `CTRL` + `R`.

![](/_static/2024/2024-04-21/results-1.png)

- _fzf-cd-widget_ executed by `ALT` + `C`.

![](/_static/2024/2024-04-21/results-2.png)

- _fzf-file-widget_ executed by `CTRL` + `T`.

![](/_static/2024/2024-04-21/results-3.png)


## Conclusion (Author Opinion)

My research for improvements in searching history commands has yielded results that exceed my expectations. fzf opened my mind to understand what is Fuzzy Finder and the problem which resolves. It not limited to be command history searching only, it is a tool that you can search anything, for instance you can execute `$ kgp -A | fzf` to search a pods in all Kubernetes cluster. It is really nice!

Certainly, I think it is a much better alternative to command history search widget default, even for the Fish shell which already has a good history search widget.

The interactive searching are blazingly fast and customization expanding the possibilities based on your needs.

The productivity which fzf provides is really awesome! In a fact, that its justifies more than __59K stars__ in your GitHub repo.

I approve and recommend!

## Links

- fzf GitHub Repository: <https://github.com/junegunn/fzf/>
- skim, a fzf implemented in rust: <https://github.com/lotabout/skim>
- My custom fzf configuration in `~/.zshrc`: <i class="fab fa-github"></i> [c-neto/ansible-configure-fedora/files/dotfiles/.zshrc](https://github.com/c-neto/ansible-configure-fedora/tree/main/files/dotfiles/.zshrc)

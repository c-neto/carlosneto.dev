---
tags: demystifying
date: "2021-05-04"
category: git
---

*__Blog Post Publish Date:__ 2021/05/04*

---

# Demystifying: $ git config

The `git config` command allows for local customization of the Git utility. It enables setting the name and email of the author contributing to the repository, specifying the text editor Git will use when input is required, among other functionalities.

When running the `git config` command with the `--system` argument, the values are formatted and saved in the `/etc/gitconfig` file. This makes these values the default for all system users. If the argument passed is `--global`, the values are saved in `~/.gitconfig`, serving as the default for the executing system user. If none of these arguments are passed and the user is in a **Working Directory**, i.e., a local repository, the modified file will be `.git/config`.

Therefore, the overriding order of `git config` metadata is as follows:

- `/etc/gitconfig`: Base values at a *System Wide* level, i.e., for all users.
- `~/.gitconfig`: User-level values - Overrides `/etc/gitconfig`.
- `.git/config`: Project-level values - Overrides `/etc/gitconfig` and `~/.gitconfig`.

----

Specify the name of the person making changes to the project:

```bash
git config user.email "carlos.neto.dev@gmail"
```

> The value ```"carlos.neto.dev@gmail"``` is an example username.

---

Specify the name of the person making changes to the project:

```bash
git config --global user.name "Carlos Neto"
```

> The value ```"Carlos Neto"``` is an example username.

---

Specify the text editor Git will use when writing a message:

```bash
git config core.editor /usr/bin/code --wait
```

> The value ```/usr/bin/code``` is the illustrative path to VSCode. Replace it with the absolute path to the binary of your preferred text editor.

---

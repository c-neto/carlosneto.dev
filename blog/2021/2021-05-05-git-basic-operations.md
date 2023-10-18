---
tags: demystifying
date: "2021-05-05"
category: git
---

*__Blog Post Publish Date:__ 2021/05/05*

---

# Understanding Basic Git CLI Operations: An Overview

Branches and tags are essential aspects of Git, allowing developers to manage their project's codebase effectively and mark significant milestones. In this guide, we'll explore how to work with branches and tags in Git.

## $ git config

The `git config` command allows for local customization of the Git utility. It enables setting the name and email of the author contributing to the repository, specifying the text editor Git will use when input is required, among other functionalities.

When running the `git config` command with the `--system` argument, the values are formatted and saved in the `/etc/gitconfig` file. This makes these values the default for all system users. If the argument passed is `--global`, the values are saved in `~/.gitconfig`, serving as the default for the executing system user. If none of these arguments are passed and the user is in a **Working Directory**, i.e., a local repository, the modified file will be `.git/config`.

Therefore, the overriding order of `git config` metadata is as follows:

- `/etc/gitconfig`: Base values at a *System Wide* level, i.e., for all users.
- `~/.gitconfig`: User-level values - Overrides `/etc/gitconfig`.
- `.git/config`: Project-level values - Overrides `/etc/gitconfig` and `~/.gitconfig`.

----

Specify the name of the person making changes to the project:

```bash
git config user.email "your-email"
```

> The value ```"your-email"``` is an example username.

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

## $ git log

The `git log` command is a powerful tool in Git for viewing the commit history within a repository. It provides a comprehensive overview of commits, allowing you to track changes, understand commit details, and navigate through your project's development timeline.

### Basic Usage

To use `git log`, simply type the following in your terminal:

```bash
git log
```

This command will display a list of commits in reverse chronological order (from the latest to the earliest). Each commit is accompanied by information such as the commit hash, author details, date, and commit message.

### Limiting the Output

You can limit the log output using various options:

- Display the last N commits:

```bash
git log -n N
```

- Show a specific range of commits:

```bash
git log <commit-hash-start>..<commit-hash-end>
```

### Custom Formatting

You can customize the output format of `git log` using the `--pretty` option. For instance:

- Display a compact representation of commits:

```bash
git log --pretty=oneline
```

- Show a detailed log with the commit message and changes:

```bash
git log --pretty=full
```

- Customize the format using placeholders:

```bash
git log --pretty=format:"%h - %an
```

## $ git branch

### Listing Local Branches

To list all local branches, use: 

```
git branch
```

### Listing All Branches

To list all branches, including remote branches: 

```
git branch -a
```

### Creating a New Branch

To create a new branch from the current branch: 

```
git checkout -b <BRANCH-NAME>
```

### Switching to a Branch

To switch to a specified branch: 

```
git checkout <BRANCH-NAME>
```

### Merging Branches

To merge changes from another branch into the current branch: 

```
git merge <BRANCH-NAME>
```

### Showing Modified Lines between Tags

To display modified lines between two tags: 

```
git diff <TAG-1> <TAG-2>
```

## $ git tag

The `git tag` command allows you to label a commit, essentially providing a high-level shortcut to a specific *hash* of a particular commit. Tags are often used to mark points of interest in the project, such as stable versions, staging versions, and test versions.
Before exploring the commands, it's important to know that there are two types of tags: **Lightweight** and **Annotated**. Lightweight tags are simple pointers to an existing commit. Annotated tags are complete objects stored in the Git database, containing the name, the email of the tag creator, the creation date, and a descriptive tag message.

### Listing All Tags with Tag Messages

To list all tags in the project along with their tag messages, use: 

```
git tag -n
```

### Creating an Annotated Tag

To create an annotated tag, use: 

```
git tag -a <TAG-NAME> -m "<TAG-DESCRIPTION-MESSAGE>"
```

### Creating a Lightweight Tag

To create a lightweight tag, use: 

```
git tag <TAG-NAME>
```

### Adding a Tag to a Specific Commit

To add a tag to a specific commit: 

```
git tag -a <TAG-NAME> -m "<TAG-DESCRIPTION-MESSAGE>" <HASH-OF-COMMIT>
```



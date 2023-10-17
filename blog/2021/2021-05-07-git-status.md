---
tags: demystifying
date: "2021-05-07"
category: git
---

*__Blog Post Publish Date:__ 2021/05/07*

---

# Understanding Status States Change Commands

In Git, a file can exist in three main **areas**:

- `Working Directory`: Not indexed in the local base;
- `INDEX` — *also known as*: `Staging`: Ready to be indexed in the local base;
- `HEAD` — *also known as*: `.git`: Indexed in the local base.

![](img/file-areas.png)

In these areas, a file can have the following **statuses**:

- `Untracked`: When the file is in `Working Directory`;
- `Staged` — *also known as* `Tracked`: When the file is in `INDEX`.
    - `Unmodified`: Files in `INDEX` that haven't changed between *commits*;
    - `Modified`: Files in `INDEX` that have changed between *commits*;
- `Commited` — *also known as* `HEAD`: Files indexed in the Git database.

![](img/file-status.png)

---

Creating a `Working Directory`, in other words, a Git repository:

```bash
git init 
```

> This command will create the `.git` directory, which is the local base for project versioning.

---

Changing the *status* of a file or directory from: `Untracked` to `Staged`

```bash
git add <FILE-OR-DIRECTORY>
```

> If a file is specified, only its status will be changed. If a directory is specified, the status of the files within it will be changed recursively.

---

Changing the *status* of the **file** from: `Staged` to `Untracked`

```bash
git rm --cached <FILE>                                        
```

Changing the *status* of the **directory** from: `Staged` to `Untracked`

```bash
git rm -r --cached <DIRECTORY>                                        
```

> The `--cached` parameter, if not specified, will remove the file from the operating system, similar to the conventional `rm` command in Linux.

---

Changing the *status* from `Staged` to `Commited`:

```bash
git commit <FILE-OR-DIRECTORY> -m <MESSAGE>         
```

> The `-m` parameter indicates a message describing the changes made to this file. If not specified, the text editor configured in the `git config core.editor` command will open.

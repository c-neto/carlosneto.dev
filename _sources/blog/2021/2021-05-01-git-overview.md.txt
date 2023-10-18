---
tags: comparison
date: "2021-05-01"
category: git
---

*__Blog Post Publish Date:__ 2021/05/01*

---

# Git Overview

Git is a [Version Control System](https://en.wikipedia.org/wiki/Version_control), designed to manage digital file content development flows in an objective, productive, performant, and distributed manner. Its usage is broad, spanning across both OpenSource and Enterprise projects, especially those developed collaboratively. Currently, the predominant languages in its source code are C, Shell, and Perl, which are accessible on GitHub [https://github.com/git/git](https://github.com/git/git).

Due to its features, it's not wrong to associate Git with the following technology definition acronyms:

- __VSC__ - *Version Control System*
- __DVSC__ - *Distributed Source Control Management*
- __SCM__ - *Source Control Management*
- __RCS__ - *Revision Control System*

> However, it's important to understand that Git is not strictly limited to any single acronym; the associations made are based on the context in which it exists.

## A Bit of History

Git originated from the development of the Linux Kernel. During the years from 1991 to 2002, changes made to the Kernel's source code were mostly sent via email as attachments of [tarballs](https://en.wikipedia.org/wiki/Tar_(computing)). Although this process may seem archaic and unproductive, in the view of Linus Torvalds, the creator and maintainer of Linux, it was better than using existing market VCS solutions. The patches were received by Linus, and he manually controlled the flow of contributions. As time went on and collaboration volume and complexity increased, this control flow became unmanageable, necessitating the presence of a Distributed File Versioning System, commonly referred to as [DVSC - *Distributed Version Control*](https://en.wikipedia.org/wiki/Distributed_version_control).

In 2002, the proprietary __DVSC__ technology [BitKeeper](http://www.bitkeeper.org/) was adopted to control Linux's source code. In 2005, the company that developed BitKeeper removed the free access rights to the tool. This, combined with the tool's limitations, led the Linux development community to discontinue its use. No alternative solutions in the market were satisfactory, especially in terms of performance when merging contributions into the code. This led the Linux developer community, especially Linus himself, to create a solution with the following goals:

- __Do the Opposite of CVS__: Avoid the mistakes made by the existing solution [CVS](https://en.wikipedia.org/wiki/Concurrent_Versions_System).
- __Performance__: Speed up the integration of contributions.
- __Distributed__: Collaborations are not necessarily centralized, similar to the clarity of processes (positive points inherited from the experience with BitKeeper).
- __Integrity__: Internal mechanisms to prevent file corruption.

Thus, in 2005, under the terms of the [GNU GPLv2 license](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html), Git was released. Over time, numerous improvements have been made, but the initial goals have been preserved.

Today, it is the primary version control tool, dominant in OpenSource projects.

## Characteristics

- __Availability__:

Although Git fits into the [DVSC - *Distributed Source Control Management*](https://en.wikipedia.org/wiki/Distributed_version_control) format, a significant portion of its operations is local. When a project with Git is cloned (downloaded), the database containing the versioning metadata of the project is contained in the `.git` directory at the root of the repository. Here, you can browse the history without the need for a connection to a centralized server.

- __Security__:

To preserve file integrity, they undergo the [SHA-1](https://pt.wikipedia.org/wiki/SHA-1) cryptographic function. Therefore, file corruptions are detected by Git.

- __State Management__:

The main difference between Git and other existing VCS solutions is how the data is managed. Examples of existing solutions include [Subversion](https://subversion.apache.org/), [Perforce](https://www.perforce.com/solutions/version-control), and [Bazaar](https://bazaar.canonical.com/en/).

Some existing solutions version control by storing data as changes to a basic version of each file. Here's an example:

![](./img/dm-others.png)

Unlike the format shown above, Git treats its data as a __file state flow__. With each commit, i.e., each time the project state is saved, a snapshot is created. The content of this snapshot is composed of references to the files present at that moment.

![](./img/dm-git.png)

Git is smart enough to maintain a file's reference if there are no changes to it between commits.

This format prevents redundancy and enables benefits like efficient and performant branching and conflict controls.

## Understanding Status States Change Commands

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

---

## Understanding Remote and Local Repositories

In the world of Git, comprehending the distinction between a local repository and a remote repository is pivotal. Let's embark on a journey to uncover the nuances through some common Git commands that underscore these differences.

### Local Repository

A **local repository** is your copy of a Git project that resides on your computer. When you clone a repository or create a new one on your machine, you are essentially establishing a local repository. This local copy includes all the project's files, the complete history of commits, branches, tags, and more.

The local repository is where you do your work, make changes, create new features, fix bugs, and perform other tasks. It allows you to experiment freely without affecting the main project until you're ready to share your changes.

### Remote Repository

On the other hand, a **remote repository** exists on a server, often on a platform like GitHub, GitLab, or Bitbucket. It serves as the centralized hub where the entire project is hosted. Remote repositories allow for collaboration and act as a shared space where multiple contributors can push their changes, ensuring a centralized version of the project.

Remote repositories are excellent for team collaboration, enabling contributors to work on the same codebase simultaneously. When you want to share your local changes with others or integrate changes made by fellow contributors, you interact with the remote repository.

Now, let's explore some fundamental Git commands that facilitate the interaction between your local repository and the remote repository.

### Remote Operation Commands

These commands are crucial for interacting with remote repositories.

#### Cloning a Remote Repository

To create a local copy of a project hosted on a remote server, we use the `git clone` command. It not only fetches the project's content but also the versioning database (`.git` directory).

```bash
git clone <PROJECT-URL>
```

When we clone a repository, we essentially obtain a complete copy, including all the commit history and the ability to track changes.

#### Synchronizing with External References

The `git fetch` command is used to synchronize the local versioning base with new branches and tags created after the project's clone.

```bash
git fetch
```

This ensures that our local repository is up-to-date with the latest changes from the remote repository. However, it does not integrate these changes into our working directory.

#### Associating the Local Base with a Remote Repository

To link our local repository with a remote repository, we use the `git remote add` command.

```bash
git remote add <REMOTE-REPOSITORY-ALIAS> <REMOTE-REPOSITORY-URL>
```

Here, <REMOTE-REPOSITORY-ALIAS> is an alias to associate with the external repository. Conventionally, 'origin' is used for the main external repository, but we can link to multiple external repositories.

#### Pushing Changes to a Remote Repository

When we want to send our committed changes from the local base to the remote repository, we use the `git push` command.

```bash
git push <REMOTE-REPOSITORY-ALIAS> <BRANCH-NAME>
```

This command transfers the changes in the 'Commited' state to the specified remote repository.

#### Pulling Changes from a Remote Repository

To fetch changes from a remote repository and integrate them into our local base, we use the `git pull` command.

```bash
git pull origin main
```

This retrieves the changes from the specified remote repository (here, 'origin'). The `git pull` command is effective only when there are no files with the 'Untracked' status in the Local Base.



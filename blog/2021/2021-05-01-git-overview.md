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

---

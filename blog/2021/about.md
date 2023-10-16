---
tags: git, concepts
date: "2021-01-01"
category: "git"
---

# GIT: What is it? What is it for?


Git is a Version Control System designed to manage the development flows of digital file content in an objective, productive, performant, and distributed manner. Its use is extensive, in both open-source and enterprise projects, especially those developed collaboratively. Currently, its source code is predominantly written in languages such as C, Shell, and Perl, accessible on Github https://github.com/git/git.

:warning: Due to its features, it's not incorrect to associate Git with the following technology definition acronyms:

    VSC - Version Control System
    DVSC - Distributed Source Control Management
    SCM - Source Control Management
    RCS - Revision Control System.

However, it's important to understand that Git is not restricted to a single acronym, and the associations made are based on the context in which it is present.

A Bit of History

Git originated from the development of the Linux Kernel. During the years from 1991 to 2002, changes made to the Kernel's source code were primarily sent via email, mostly as attachments of tarballs. Although this process might seem archaic and unproductive, in Linus Torvalds' view, the creator and maintainer of Linux, it was better than using existing VCS solutions in the market. Patches were received by Linus, and he manually controlled the collaboration flow. Over time, due to the high volume of collaborations, complexity, and lines of code, this control flow became unmanageable, requiring the presence of a Distributed Version Control System, commonly referred to as DVSC.

In 2002, the proprietary DVSC technology, BitKeeper, was adopted to control the Linux source code. In 2005, the company that developed BitKeeper removed free access to the tool's copyrights. This event, combined with the tool's limitations, led the Linux development community to discontinue the use of the tool. No alternative solutions in the market were satisfactory, especially in terms of performance when merging contributions into the code. This situation prompted the Linux development community, particularly Linus himself, to create a solution with the following goals in mind:

    Do the Opposite of CVS: Avoid the same mistakes as the existing CVS solution.
    Performance: Speed up collaboration integration.
    Distributed: Collaborations are not necessarily centralized, akin to the clarity of processes (positive aspects inherited from the experience with BitKeeper).
    Integrity: Internal mechanisms to prevent file corruption.

Thus, in 2005, under the terms of the GNU GPLv2 license, Git was released. Over time, numerous improvements have been made, but the initial goals have been preserved.

Today, it is the primary version control tool dominant in open-source projects.

Features

Availability:
Although Git falls under the format of Distributed Version Control System (DVCS), a good portion of its operations are local. When a Git project is cloned (downloaded), the database containing the project's versioning metadata is contained in the .git directory at the root of the repository. Here, you can check the history without the need for a connection to a centralized server.

Security:
To preserve file integrity, they are subjected to the SHA-1 cryptographic function, allowing Git to detect file corruptions.

State Management:
The main difference between Git and other existing VCS solutions lies in how data is managed.

:memo: Existing solutions include Subversion, Perforce, and Bazaar, for example.

Some of the existing solutions version files by storing data as changes to a basic version of each file. Here's an example:

Unlike the format shown above, Git treats its data as a stream of file states. With each commit, i.e., each time the project state is saved, a snapshot is created. The contents of this snapshot consist of references to the files present at that moment.

Git is intelligent enough to maintain a file reference if there are no changes to it between commits.

This format avoids redundancy and allows benefits such as branching and efficient conflict control.

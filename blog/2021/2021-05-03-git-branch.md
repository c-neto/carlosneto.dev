---
tags: demystifying
date: "2021-05-03"
category: git
---

*__Blog Post Publish Date:__ 2021/05/03*

---

# Demystifying: $ git branch/tag

Branches and tags are essential aspects of Git, allowing developers to manage their project's codebase effectively and mark significant milestones. In this guide, we'll explore how to work with branches and tags in Git.

## Branches

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

## Tags

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

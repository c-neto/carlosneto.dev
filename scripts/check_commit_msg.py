#!/usr/bin/env python3
"""Reject commit messages that do not follow Conventional Commits.

Runs as the ``commit-msg`` hook (see ``.pre-commit-config.yaml``). The rules
match the Commits section of ``.claude/skills/blog-creator/SKILL.md``:

    <type>(<scope>): <description>

- type: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
- scope: required, lowercase kebab-case (post slug, ``blog``, ``site``, ...)
- ``!`` before the colon marks a breaking change
- description: starts lowercase, no trailing period
- subject line: at most 72 characters
- body, when present, is separated from the subject by a blank line

Messages that git writes itself (merge, revert, fixup!, squash!, amend!) pass.
"""
import re
import sys

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
MAX_SUBJECT = 72

PATTERN = re.compile(
    rf"^(?P<type>{'|'.join(TYPES)})"
    r"\((?P<scope>[a-z0-9]+(?:[-.][a-z0-9]+)*)\)"
    r"!?: "
    r"(?P<desc>\S.*)$"
)
AUTO_GENERATED = re.compile(r"^(Merge |Revert \"|fixup! |squash! |amend! )")

EXAMPLES = """\
Examples:
  feat(blog): add post on helm global values
  docs(fzf): rewrite terminal search problem section
  fix(kubestronaut): fix broken kodekloud link
  style(site): shrink blockquote font size
  chore(skills): require conventional commits"""


def check(message: str) -> list:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return ["the commit message is empty"]

    subject = lines[0]
    if AUTO_GENERATED.match(subject):
        return []

    errors = []
    match = PATTERN.match(subject)
    if not match:
        errors.append(
            "the subject must be '<type>(<scope>): <description>' with type in "
            + ", ".join(TYPES)
            + " and a lowercase scope"
        )
    else:
        desc = match.group("desc")
        if desc[0].isupper():
            errors.append("the description must start in lowercase")
        if desc.endswith("."):
            errors.append("the description must not end with a period")
    if len(subject) > MAX_SUBJECT:
        errors.append(f"the subject has {len(subject)} characters (max {MAX_SUBJECT})")
    if len(lines) > 1 and lines[1].strip():
        errors.append("leave a blank line between the subject and the body")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_commit_msg.py <commit-msg-file>", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        message = f.read()
    errors = check(message)
    if not errors:
        return 0
    subject = next((l for l in message.splitlines() if l.strip() and not l.startswith("#")), "")
    print(f"Commit rejected, not a Conventional Commit:\n  {subject!r}\n", file=sys.stderr)
    for error in errors:
        print(f"  - {error}", file=sys.stderr)
    print(f"\n{EXAMPLES}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

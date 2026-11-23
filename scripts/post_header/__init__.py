"""Build one header block above the title of every blog post.

Each post starts with ``*__Post Publication Date:__ YYYY/MM/DD*`` and a
``---`` rule above its H1. This extension removes both from the body and puts
a single block at the top of the body, above the H1, with the publish date, the
date of the last commit, the revision count (git commits that touched the
post's source file) linked to the file's history on GitHub, and the AI TL;DR
buttons that the
``tldr_ai`` extension leaves in ``context["aor_tldr"]``.

The revision count follows renames (``git log --follow``), so posts moved from
``draft/`` keep their earlier history. The build needs the full git history
(``fetch-depth: 0`` in CI); without git the revision part is left out.
"""
import re
import subprocess
from datetime import date
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)

REPO_URL = "https://github.com/c-neto/carlosneto.dev"
BRANCH = "main"

_POST_RE = re.compile(r"^blog/\d{4}/[^/]+$")

# The publish date paragraph and the optional rule that follows it.
_PUBLISH_DATE_RE = re.compile(
    r"<p><em><strong>Post Publication Date:</strong>\s*(?P<date>[^<]+?)\s*</em></p>"
    r"\s*(?:<hr[^>]*>\s*)?"
)

SEP = '<span class="post-header__sep">·</span>'


def _git_dates(srcdir: Path, relpath: str) -> list:
    """Return the commit dates (YYYY-MM-DD, newest first) of a file."""
    try:
        out = subprocess.run(
            ["git", "-c", "safe.directory=*", "log", "--follow", "--format=%cs", "--", relpath],
            cwd=srcdir,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as err:
        logger.warning("post_header: git log failed for %s: %s", relpath, err)
        return []
    return [line for line in out.splitlines() if line.strip()]


def add_post_header(app: Sphinx, pagename, templatename, context, doctree):
    body = context.get("body")
    tldr = context.pop("aor_tldr", "")
    if body is None or not _POST_RE.match(pagename):
        return

    meta = []
    match = _PUBLISH_DATE_RE.search(body)
    if match:
        meta.append(f"<span><strong>Published:</strong> {match.group('date')}</span>")
        body = body[: match.start()] + body[match.end():]
    else:
        logger.warning("post_header: no publish date line in %s", pagename)

    srcdir = Path(app.srcdir)
    relpath = Path(app.env.doc2path(pagename)).relative_to(srcdir).as_posix()
    dates = _git_dates(srcdir, relpath)
    if dates:
        updated = date.fromisoformat(dates[0]).strftime("%Y/%m/%d")
        meta.append(f"<span><strong>Updated:</strong> {updated}</span>")
        meta.append(
            f"<span><strong>Revisions:</strong> "
            f'<a href="{REPO_URL}/commits/{BRANCH}/{relpath}" '
            f'target="_blank" rel="noopener" title="View history on GitHub">{len(dates)}</a></span>'
        )

    divider = '<hr class="post-header__divider" />' if meta and tldr else ""
    header = (
        '<blockquote class="post-header">'
        f'<span class="post-header__meta">{SEP.join(meta)}</span>'
        f"{divider}"
        f"{tldr}"
        "</blockquote>"
    )

    context["body"] = header + '\n<hr class="docutils post-header__rule" />\n' + body


def setup(app: Sphinx):
    # After tldr_ai (default priority 500) has left its block in the context,
    # and before Giscus (900) wraps the body.
    app.connect("html-page-context", add_post_header, priority=600)
    return {"parallel_read_safe": True, "parallel_write_safe": True}

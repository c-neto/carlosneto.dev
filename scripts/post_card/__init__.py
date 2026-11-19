"""Render links to the author's own posts as small inline chips.

Inside a blog post, any regular Markdown link to another post of this blog,
such as ``[Helm Tips](/blog/2026/2026-02-25-helm-tips-inspect-context.md)``,
gets the author's photo in front of the link text and a pill style similar to
inline code. The target post's frontmatter ``description`` becomes the hover
tooltip. Nothing changes in the Markdown source; links to external sites and to
non-post pages are left alone.
"""
import posixpath
import re

from docutils import nodes
from sphinx.application import Sphinx

AVATAR = "/_static/profile-color-circle-small.png"
AUTHOR = "Carlos Neto"

_POST_RE = re.compile(r"^blog/\d{4}/[^/]+$")


def _is_post(docname: str) -> bool:
    return bool(_POST_RE.match(docname))


def _norm_uri(uri: str) -> str:
    return posixpath.normpath(uri.split("#", 1)[0]).strip("/")


def _post_uris(app: Sphinx) -> dict:
    """Map each post's output URI (normalized) to its docname, once per build."""
    cache = getattr(app, "_post_chip_uris", None)
    if cache is None:
        cache = {
            _norm_uri(app.builder.get_target_uri(doc)): doc
            for doc in app.env.all_docs
            if _is_post(doc)
        }
        app._post_chip_uris = cache
    return cache


def add_post_chips(app: Sphinx, doctree, fromdocname):
    if app.builder.format != "html" or not _is_post(fromdocname):
        return

    uris = _post_uris(app)
    from_uri = app.builder.get_target_uri(fromdocname)
    base = from_uri if from_uri.endswith("/") or not from_uri else posixpath.dirname(from_uri)

    for ref in list(doctree.findall(nodes.reference)):
        refuri = ref.get("refuri", "")
        if not ref.get("internal") or not refuri or refuri.startswith("#"):
            continue
        target = uris.get(_norm_uri(posixpath.join(base, refuri)))
        if not target or target == fromdocname or "post-chip" in ref["classes"]:
            continue

        ref["classes"].append("post-chip")
        description = str(app.env.metadata.get(target, {}).get("description", "")).strip()
        if description:
            ref["reftitle"] = description
        avatar = nodes.raw(
            "",
            f'<img class="post-chip-avatar" src="{AVATAR}" alt="{AUTHOR}" '
            'width="18" height="18" loading="lazy">',
            format="html",
        )
        ref.insert(0, avatar)


def reset_cache(app: Sphinx):
    app._post_chip_uris = None


def setup(app: Sphinx):
    app.connect("builder-inited", reset_cache)
    app.connect("doctree-resolved", add_post_chips)
    return {"parallel_read_safe": True, "parallel_write_safe": True}

"""Inject the Giscus comment box into blog posts only.

Giscus used to live in ``_templates/layout.html``, which loaded it on every
page of the site (home, listings, tag/category pages, etc). This extension
appends the Giscus script to the body of actual blog posts only, reusing the
same post-detection rules as the AI TL;DR extension.
"""
import re

from sphinx.application import Sphinx

# Pages that look like posts but are blog listing/meta pages, not articles.
_NON_POST_RE = re.compile(
    r"blog/(index|category|tag|author|location|language|drafts|archive)"
    r"|/index$|^index$"
)

GISCUS_TEMPLATE = """
<!-- Add a comment box underneath the page's content -->
<script
  src="https://giscus.app/client.js"
  data-repo="c-neto/carlosneto.dev"
  data-repo-id="R_kgDOKgwGNA"
  data-category="General"
  data-category-id="DIC_kwDOKgwGNM4CaKBI"
  data-mapping="pathname"
  data-strict="0"
  data-reactions-enabled="1"
  data-emit-metadata="0"
  data-input-position="bottom"
  data-theme="light"
  data-lang="en"
  crossorigin="anonymous"
  async>
</script>
"""


def _is_blog_post(pagename: str) -> bool:
    """Return True for actual blog posts, excluding listing and meta pages."""
    if not pagename.startswith("blog/"):
        return False
    if _NON_POST_RE.search(pagename):
        return False
    # Posts live at blog/<year>/<slug>; listing pages have fewer segments.
    return pagename.count("/") >= 2


def add_giscus(app: Sphinx, pagename, templatename, context, doctree):
    """Append the Giscus comment box to the body of every blog post.

    The post body is also wrapped in a ``blog-post`` container so the CSS can
    style posts differently from the rest of the site (e.g. justified text)
    without leaking those styles onto listing or home pages.
    """
    if not _is_blog_post(pagename):
        return

    body = context.get("body")
    if body is None:
        return
    context["body"] = f'<div class="blog-post">{body}</div>' + GISCUS_TEMPLATE


def setup(app: Sphinx):
    # Run late (high priority number) so other body-mutating extensions such
    # as the AI TL;DR have already prepended their content; this keeps the
    # Giscus box at the very bottom and everything else inside the wrapper.
    app.connect("html-page-context", add_giscus, priority=900)
    return {"parallel_read_safe": True, "parallel_write_safe": True}

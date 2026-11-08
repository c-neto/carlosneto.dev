"""Inject an "AI TL;DR" block into every blog post.

The block renders three buttons (ChatGPT, Claude, Grok). Each opens the
matching AI chat pre-filled with a prompt that asks the assistant to read the
post and summarize it for the reader, replying in the reader's native language.

This is the Sphinx/ABlog port of the original Hugo partial template.
"""
import re

from sphinx.application import Sphinx
from urllib.parse import urlencode

# Pages that look like posts but are blog listing/meta pages, not articles.
_NON_POST_RE = re.compile(
    r"blog/(index|category|tag|author|location|language|drafts|archive)"
    r"|/index$|^index$"
)

PROMPT_TEMPLATE = (
    "Please open this URL with web search and read the full article: {url}\n\n"
    "After reading the real content of that article, do the following:\n"
    "1) Summarize the 5 most important points and the conclusion.\n"
    "2) After the summary, tell the reader what key details, data and insights "
    "they are missing by not reading the full article. Be specific enough to "
    "make them curious.\n"
    "3) Remind them they can keep asking follow-up questions about this article "
    "right here in this chat.\n"
    "4) Suggest one good follow-up question they could ask as a starter.\n\n"
    "Be concise, it is a summary. \n\n"
    "Write your entire answer in my native language. Detect it from the "
    "language I use to talk to you, and if it is not clear, ask me which "
    "language I prefer before summarizing."
)

LOGO_OPENAI = (
    '<svg class="aor-tldr__logo" viewBox="0 0 24 24" width="16" height="16" '
    'fill="currentColor" aria-hidden="true">'
    '<path d="M22.282 9.821a5.985 5.985 0 0 0-.516-4.91 6.046 6.046 0 0 0-6.51-2.9A6.065 6.065 0 0 0 4.981 4.18a5.985 5.985 0 0 0-3.998 2.9 6.046 6.046 0 0 0 .743 7.097 5.98 5.98 0 0 0 .51 4.911 6.051 6.051 0 0 0 6.515 2.9A5.985 5.985 0 0 0 13.26 24a6.056 6.056 0 0 0 5.772-4.206 5.99 5.99 0 0 0 3.997-2.9 6.056 6.056 0 0 0-.747-7.073zM13.26 22.43a4.476 4.476 0 0 1-2.876-1.04l.141-.081 4.779-2.758a.795.795 0 0 0 .392-.681v-6.737l2.02 1.168a.071.071 0 0 1 .038.052v5.583a4.504 4.504 0 0 1-4.494 4.494zM3.6 18.304a4.47 4.47 0 0 1-.535-3.014l.142.085 4.783 2.759a.771.771 0 0 0 .78 0l5.843-3.369v2.332a.08.08 0 0 1-.033.062L9.74 19.95a4.5 4.5 0 0 1-6.14-1.646zM2.34 7.896a4.485 4.485 0 0 1 2.366-1.973V11.6a.766.766 0 0 0 .388.676l5.815 3.355-2.02 1.168a.076.076 0 0 1-.071.006l-4.83-2.786A4.504 4.504 0 0 1 2.34 7.872zm16.597 3.855l-5.833-3.387L15.119 7.2a.076.076 0 0 1 .071-.006l4.83 2.787a4.494 4.494 0 0 1-.676 8.105v-5.678a.79.79 0 0 0-.407-.667zm2.01-3.023l-.141-.085-4.774-2.782a.776.776 0 0 0-.785 0L9.409 9.23V6.897a.066.066 0 0 1 .028-.061l4.83-2.787a4.5 4.5 0 0 1 6.68 4.66zm-12.64 4.135l-2.02-1.164a.08.08 0 0 1-.038-.057V6.075a4.5 4.5 0 0 1 7.375-3.453l-.142.08L8.704 5.46a.795.795 0 0 0-.393.681zm1.097-2.365l2.602-1.5 2.607 1.5v2.999l-2.597 1.5-2.607-1.5z"/>'
    '</svg>'
)
LOGO_CLAUDE = (
    '<svg class="aor-tldr__logo" viewBox="0 0 24 24" width="16" height="16" '
    'fill="currentColor" aria-hidden="true">'
    '<path d="M4.709 15.955l4.72-2.647.08-.23-.08-.128H9.2l-.79-.048-2.698-.073-2.339-.097-2.266-.122-.571-.121L0 11.784l.055-.352.48-.321.686.06 1.52.103 2.278.158 1.652.097 2.449.255h.389l.055-.157-.134-.098-.103-.097-2.358-1.596-2.552-1.688-1.336-.972-.724-.491-.364-.462-.157-1.005.654-.72.878.06.225.061.89.683 1.9 1.47 2.48 1.826.364.303.145-.103.018-.072-.163-.274-1.354-2.446-1.446-2.49-.643-1.032-.17-.619a2.97 2.97 0 01-.104-.729L6.283.134 6.696 0l.996.134.42.364.62 1.414 1.002 2.229 1.555 3.03.455.898.243.832.091.255h.158V9.01l.128-1.706.237-2.095.23-2.695.08-.76.376-.91.747-.492.584.28.48.685-.067.444-.286 1.851-.559 2.903-.364 1.942h.212l.243-.242.983-1.306 1.651-2.064.73-.82.85-.904.547-.431h1.033l.76 1.129-.34 1.166-1.064 1.347-.881 1.142-1.264 1.7-.79 1.36.073.11.188-.02 2.856-.606 1.542-.28 1.84-.315.831.388.091.395-.328.807-1.967.486-2.307.462-3.436.813-.042.03.049.061 1.548.146.662.036h1.62l3.018.225.79.522.473.638-.079.485-1.215.62-1.64-.389-3.829-.91-1.312-.329h-.182v.11l1.093 1.068 2.003 1.81 2.507 2.33.127.578-.32.455-.34-.049-2.204-1.657-.85-.746-1.925-1.62h-.127v.17l.443.649 2.343 3.521.122 1.08-.17.353-.607.213-.668-.122-1.372-1.925-1.415-2.167-1.14-1.943-.14.08-.674 7.254-.316.37-.729.28-.607-.461-.322-.747.322-1.476.389-1.924.315-1.53.286-1.9.17-.631-.012-.042-.14.018-1.433 1.967-2.18 2.945-1.725 1.845-.414.164-.717-.37.067-.662.401-.589 2.388-3.036 1.44-1.882.93-1.086-.006-.158h-.055L4.132 18.56l-1.13.146-.487-.456.061-.746.231-.243 1.908-1.312z"/>'
    '</svg>'
)
LOGO_GROK = (
    '<svg class="aor-tldr__logo" viewBox="0 0 24 24" width="16" height="16" '
    'fill="currentColor" aria-hidden="true">'
    '<path d="M9.27 15.29l7.978-5.897c.391-.29.95-.177 1.137.272.98 2.369.542 5.215-1.41 7.169-1.951 1.954-4.667 2.382-7.149 1.406l-2.711 1.257c3.889 2.661 8.611 2.003 11.562-.953 2.341-2.344 3.066-5.539 2.388-8.42l.006.007c-.983-4.232.242-5.924 2.75-9.383.06-.082.12-.164.179-.248l-3.301 3.305v-.01L9.267 15.292M7.623 16.723c-2.792-2.666-2.31-6.825.058-9.195 1.751-1.754 4.584-2.465 7.17-1.414l2.705-1.25a7.808 7.808 0 00-1.364-.834c-3.004-1.416-6.724-.898-9.195 1.576-2.372 2.375-3.059 5.956-1.598 9.017 1.09 2.289-.885 5.323-2.368 7.17.922-.414 2.276-1.111 3.335-2.263.667-.726.667-.726 1.257-2.607z"/>'
    '</svg>'
)

TLDR_TEMPLATE = """
<div class="aor-tldr">
  <img class="aor-tldr__marvin" src="{marvin_src}" alt="">
  <span class="aor-tldr__copy">
    <strong>AI TL;DR</strong>
    <span>Too lazy to read? Summarize this post with:</span>
  </span>
  <span class="aor-tldr__buttons">
    <a class="aor-tldr__btn" href="{chatgpt_url}" target="_blank" rel="noopener">{logo_openai}<span>ChatGPT</span></a>
    <a class="aor-tldr__btn" href="{claude_url}" target="_blank" rel="noopener">{logo_claude}<span>Claude</span></a>
    <a class="aor-tldr__btn" href="{grok_url}" target="_blank" rel="noopener">{logo_grok}<span>Grok</span></a>
  </span>
</div>
"""


def _is_blog_post(pagename: str) -> bool:
    """Return True for actual blog posts, excluding listing and meta pages."""
    if not pagename.startswith("blog/"):
        return False
    if _NON_POST_RE.search(pagename):
        return False
    # Posts live at blog/<year>/<slug>; listing pages have fewer segments.
    return pagename.count("/") >= 2


def _provider_url(base: str, prompt: str) -> str:
    return f"{base}?{urlencode({'q': prompt})}"


def add_tldr_ai(app: Sphinx, pagename, templatename, context, doctree):
    """Render the AI TL;DR block at the top of every blog post body."""
    if not _is_blog_post(pagename):
        return

    baseurl = (app.config.blog_baseurl or "").rstrip("/")
    # get_target_uri yields the builder-correct path: "blog/2026/foo.html"
    # for the html builder and "blog/2026/foo/" for dirhtml.
    target = app.builder.get_target_uri(pagename)
    permalink = f"{baseurl}/{target}"

    prompt = PROMPT_TEMPLATE.format(url=permalink)
    claude_url = _provider_url("https://claude.ai/new", prompt)
    chatgpt_url = _provider_url("https://chatgpt.com/", prompt)
    grok_url = _provider_url("https://grok.com/", prompt)

    pathto = context.get("pathto")
    marvin_src = pathto("_static/marvin.jpg", 1) if pathto else "_static/marvin.jpg"

    block = TLDR_TEMPLATE.format(
        claude_url=claude_url,
        chatgpt_url=chatgpt_url,
        grok_url=grok_url,
        marvin_src=marvin_src,
        logo_openai=LOGO_OPENAI,
        logo_claude=LOGO_CLAUDE,
        logo_grok=LOGO_GROK,
    )

    body = context.get("body")
    if body is None:
        return
    context["body"] = block + body


def setup(app: Sphinx):
    app.connect("html-page-context", add_tldr_ai)
    app.add_css_file("tldr_ai.css")
    return {"parallel_read_safe": True, "parallel_write_safe": True}

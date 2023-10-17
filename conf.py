import sys

sys.path.append("scripts")
sys.path.append(".")

from pathlib import Path
from social_media import add_social_media_js, SocialPost


project = "Carlos Neto"
copyright = "2023, Carlos Neto"
author = "Carlos Neto"

extensions = [
    "myst_nb",
    "ablog",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_examples",
    "sphinxext.opengraph",
    "sphinxext.rediraffe",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "*import_posts*",
    "**/pandoc_ipynb/inputs/*",
    ".nox/*",
    "README.md",
    "**/.ipynb_checkpoints/*",
]

# -- HTML output -------------------------------------------------

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "search_bar_text": "Search this site...",
    # "analytics": {"google_analytics_id": "UA-88310237-1"},
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/c-neto",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "Linkedin",
            "url": "https://www.linkedin.com/in/c-neto/",
            "icon": "fa-brands fa-linkedin",
        },
        {
            "name": "Blog RSS feed",
            "url": "https://carlosneto.dev/blog/atom.xml",
            "icon": "fa-solid fa-rss",
        },
    ],
    "secondary_sidebar_items": [],
    "article_header_start": [],
}

html_favicon = "_static/profile-color-circle-small.png"
html_title = "Carlos Neto"
html_static_path = ["_static"]
html_extra_path = ["feed.xml"]
html_sidebars = {
    "index": [
        "hello.html"
    ],
    "about": [
        "hello.html"
    ],
    "blog": [
        "ablog/categories.html",
        "ablog/tagcloud.html",
        "ablog/recentposts.html",
        "ablog/archives.html"
    ],
    "blog/**": [
        "ablog/postcard.html",
        "page-toc",
        "ablog/recentposts.html"
    ],
}


# OpenGraph config
ogp_site_url = "https://carlosneto.dev"
ogp_social_cards = {
    "line_color": "#4078c0",
    "image": "_static/profile-color-circle.png",
}


# rediraffe_redirects = {
#     "rust-governance.md": "blog/2018/rust_governance.md",
# }
# # Update the posts/* section of the rediraffe redirects to find all files
# redirect_folders = {
#     "posts": "blog",
# }

# for old, new in redirect_folders.items():
#     for newpath in Path(new).rglob("**/*"):
#         if newpath.suffix in [".ipynb", ".md"] and "ipynb_checkpoints" not in str(
#             newpath
#         ):
#             oldpath = str(newpath).replace("blog/", "posts/", 1)
#             # Skip pandoc because for some reason it's broken
#             if "pandoc" not in str(newpath):
#                 rediraffe_redirects[oldpath] = str(newpath)

# -- ABlog ---------------------------------------------------

blog_baseurl = "https://carlosneto.dev"
blog_title = "Carlos Neto"
blog_path = "blog"
blog_post_pattern = "blog/*/*"
blog_feed_fulltext = True
blog_feed_subtitle = "DevOps, Python, OpenSearch, and Log Pipelines."
fontawesome_included = True
post_redirect_refresh = 1
post_auto_image = 1
post_auto_excerpt = 2

# -- MyST and MyST-NB ---------------------------------------------------

# MyST
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_image",
]


html_context = {
   # ...
   "default_mode": "light"
}


# MyST-NB
# Don't execute anything by default because many old posts don't execute anymore
# and this slows down build times.
# Instead if I want something to execute, manually set it in the post's metadata.
nb_execution_mode = "off"


def setup(app):
    app.add_directive("socialpost", SocialPost)
    app.connect("html-page-context", add_social_media_js)
    app.add_css_file("custom.css")

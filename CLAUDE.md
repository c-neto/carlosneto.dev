# CLAUDE.md

Guidance for AI agents working in this repository.

## Repository Structure

```bash
.
├── .claude/skills/         # Claude Code skills (blog-creator)
├── .github/                # GitHub Actions workflows and CI config
├── _static/                # Static assets: images, custom.css, per-year post images (_static/<year>/)
├── _templates/             # Sphinx HTML templates (layout.html, hello.html)
├── blog/                   # Published posts, organized by year: blog/<YEAR>/<YYYY-MM-DD>-<slug>.md
├── hidden/                 # Draft posts not ready to publish
├── scripts/                # Helper scripts (social_media/)
├── blog.md                 # Blog index page
├── index.md                # Site landing page
├── contribution-list.md    # Page with Open Source contributions
├── conf.py                 # Sphinx configuration
├── myst.yml                # MyST project configuration
├── Makefile                # Build commands (make setup, make live)
├── noxfile.py              # Nox automation sessions
├── requirements.txt        # Python dependencies for the site
├── feed.xml                # RSS feed
├── CNAME                   # Custom domain for GitHub Pages
└── import_posts.ipynb      # Notebook for importing/migrating posts
```

### Key directories

- **`blog/`**: The published posts. Each post lives under its year folder with a `YYYY-MM-DD` date prefix in the filename. This is where finished posts go.
- **`hidden/`**: Drafts in progress. Not published. Move a post to `blog/<YEAR>/` when it is ready.
- **`_static/`**: All static assets. Post images go in `_static/<year>/`. Site-wide styles are in `custom.css`.
- **`_templates/`**: Sphinx HTML layout overrides.
- **`.claude/skills/`**: The project skills described above. `humanizer` is installed per user in `~/.claude/skills/`.

## Build

Local development uses Sphinx. See `README.md`:

- `make setup`: create the virtual environment and install dependencies.
- `make live`: run the local web server with hot reload.

# CLAUDE.md

Guidance for AI agents working in this repository.

## Skills

This project ships skills in `.agents/skills/`. Use them for the tasks below.

- **blog-writer**: Use for any work on blog posts. Drafting a new post, completing a draft, or refactoring an existing post for frontmatter, structure, headings, code blocks, callouts, voice, and tone. It holds the author's voice guide and all writing conventions.
- **humanizer**: Use to remove AI tells from prose. Always run it as the final step before publishing any post, with a voice sample. The `blog-writer` skill calls it at the end of its workflow.
- **bash-conventions**: Bash and shell scripting conventions. Use when writing, reviewing, or refactoring bash/sh scripts.
- **python-conventions**: Python coding conventions and best practices. Use when writing, reviewing, or refactoring Python scripts.
- **helm-chart-conventions**: Helm chart structural, formatting, and naming conventions. Use when authoring or reviewing Helm charts.

When a task matches a skill, load that skill and follow it. The skills are the source of truth for how to do the work; this file only points to them.

## Repository Structure

```bash
.
├── .agents/skills/         # Agent skills (blog-writer, humanizer)
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
- **`.agents/skills/`**: The agent skills described above.

## Build

Local development uses Sphinx. See `README.md`:

- `make setup`: create the virtual environment and install dependencies.
- `make live`: run the local web server with hot reload.

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
├── draft/                  # Draft posts not ready to publish
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
- **`draft/`**: Drafts in progress. Not published. Move a post to `blog/<YEAR>/` when it is ready.
- **`_static/`**: All static assets. Post images go in `_static/<year>/`. Site-wide styles are in `custom.css`.
- **`_templates/`**: Sphinx HTML layout overrides.
- **`.claude/skills/`**: The project skills. `blog-creator` is the single writing skill. It edits passages (Edit Mode), creates posts (New-Post Mode), and keeps the text conventions in `written-directives.md`. `humanizer` is installed per user in `~/.claude/skills/`.

## Writing Directives (always active)

Every request in this repository that writes or edits text, including a single sentence, must invoke the `blog-creator` skill. A request to change a passage uses its Edit Mode, and a new post uses its New-Post Mode. This holds even when the request does not mention the skill and when another skill (`/blog write`, `/blog rewrite`, `humanizer`, analyzer fixes) runs the work. When they conflict, the directives in `.claude/skills/blog-creator/written-directives.md` win. They are imported below so they are always in context:

@.claude/skills/blog-creator/written-directives.md

## Build

Local development uses Sphinx. See `README.md`:

- `make setup`: create the virtual environment and install dependencies.
- `make live`: run the local web server with hot reload.

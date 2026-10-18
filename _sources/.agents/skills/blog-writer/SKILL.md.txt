---
name: blog-writer
description: |
  Write and refactor blog posts for carlosneto.dev so they match the author's
  voice, structure, and conventions. Use when drafting a new post, completing a
  draft, or refactoring an existing post for frontmatter, structure, headings,
  code blocks, callouts, voice and tone, and the final humanizer pass.
license: MIT
metadata:
  version: "1.0.0"
---

# Blog Writer: write posts that sound like Carlos Neto

Write, complete, or refactor blog posts for this project so they read like the author (Carlos Neto), not like an AI. Keep every supported fact. Do not invent facts, names, numbers, dates, quotes, or citations; if a detail is missing, ask instead of making one up.

The whole point of this skill is voice. If a draft reads like a polished corporate doc or a generic LLM answer, it has failed, even if every fact is correct.

## Workflow

1. **Read the draft and at least one published post for voice.** Good samples: `blog/2024/2024-07-21-dynaconf.md`, `blog/2024/2024-04-21-fzf.md`, `blog/2025/2025-02-25-helm-best-practices.md`.
2. **Resolve conflicts before writing.** If the filename, frontmatter, and content disagree (wrong topic, mismatched slug), ask the user which is the source of truth. Do not guess.
3. **Draft or refactor** following every section below. A new post is always created in `hidden/` with no date prefix in the filename (see "File naming and location").
4. **Run the humanizer pass** (see the last section). This is the final step before publishing.
5. **Check the list** at the end of this skill.
6. **Promote only when asked.** Move the post into `blog/<YEAR>/` only when the user explicitly says "promova", "promote", or "publish" (see "Promoting a post").

## File naming and location

New posts are always created in `hidden/`, with no date prefix in the filename:

```
hidden/<slug>.md
```

Examples: `hidden/tcp-ephemeral-ports.md`, `hidden/sftp-explicit-algorithm.md`.

The slug must match the final title. While a post lives in `hidden/`, do not add a date to the filename and do not move it into `blog/`. It stays there until the user explicitly asks to promote it.

## Promoting a post

A post only moves to the published location when the user explicitly asks to "promova", "promote", or "publish" it. Until then, leave it in `hidden/`.

When promoting, move the file into `blog/<YEAR>/` and add the date prefix to the filename:

```
blog/<YEAR>/<YYYY-MM-DD>-<slug>.md
```

Examples: `blog/2025/2025-02-16-logstash-db-enrichment.md`, `blog/2026/2026-07-15-vim-kubernetes-exams.md`.

The `<YEAR>` and the `<YYYY-MM-DD>` prefix must match the `date` in the frontmatter. The slug stays the same as the `hidden/` filename. If the frontmatter has no date yet, ask the user for the publish date before promoting.

## Frontmatter

Every post starts with a YAML frontmatter block, then a publish date line, then a horizontal rule:

```markdown
---
tags: tag1, tag2
date: "YYYY-MM-DD"
category: Category Name
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---
```

- **tags**: lowercase, comma-separated. Match the tools and technologies covered.
- **date**: ISO format in quotes.
- **category**: Title case. Common values: `Log Analytics`, `Linux`, `Kubernetes`, `Cloud`, `python`, `code`.
- The publish date line uses italic plus bold: `*__Blog Post Publish Date:__ ...*`.

## Title

Use an `#` H1 heading. Titles are descriptive and punchy, often with a colon and a subtitle, a question, or a memorable phrase:

- `# Logstash DB Enrichment - Tips and Traps!`
- `# fzf: Life is Too Short for Pipe Grep`
- `# Dynaconf: The Python Config Silver Bullet!`
- `# What is the Cloud and why does everyone keep talking about it?`

## Opening paragraph (post summary)

Right after the title, write 2 to 4 sentences that summarize what the post covers. This is a standalone paragraph, not a heading. It sets expectations and says what the reader will learn.

Pattern: _"This blog post [covers/outlines/explores] [topic]. It [explains/provides/includes] [what is inside]."_

## Section structure

Posts follow a logical progression. Common patterns:

- **Problem, Solution, Hands-On, Conclusion** (technical how-to): context, the problem, the solution, practical example, conclusion (author opinion), links.
- **Concept, Commands/Code, Conclusion** (reference or cheatsheet): intro paragraph, conceptual explanation, useful commands or code, optional closing invitation to discuss.
- **Experience, Tools, Guide, Conclusion** (here's what I use and why): personal motivation, options and tradeoffs, configuration walkthrough, conclusion.

## Section headings

Use `##` for main sections and `###` for subsections. Headings are descriptive and often include the key term:

- `## The Problem: Scaling Up Pipelines == Growing Code Duplication`
- `## How to Configure fzf Widgets in Zsh`
- `## Conclusion (Author Opinion)`

The conclusion is almost always titled exactly `## Conclusion (Author Opinion)` or `## Conclusion`. It is a first-person opinion, not a neutral summary.

## Voice and tone

This is the most important part. These posts were written by a human. Sound like that human.

### Hard rules (never break these)

- **Never include emojis.** Not in titles, headings, body, lists, or callouts.
- **Never use em dashes or en dashes** (`—` / `–`). Rewrite instead: a period and a short new sentence, a comma, parentheses, or a colon.
- **Be direct and concise.** Say it in the fewest words that stay clear. Cut filler, cut warm-up phrases, cut restating the heading. One idea per sentence when possible.

### Core principles

- **First person throughout.** The author is always present: "I decided to write this...", "I have been using Dynaconf around 4 years...".
- **Write to the reader as a peer**, like explaining to a colleague at the next desk. Not lecturing, not selling.
- **Strongly opinionated.** Give verdicts, name favorites, say what you would avoid: "No doubt, it is my favorite plugin." / "I approve and recommend!"
- **Honest about trade-offs.** Never present a tool as flawless: "it's not a silver bullet", "it can even be the worse choice, especially financially". Every post that praises something also admits where it hurts.
- **Grounded in real experience, not theory.** Lead with what actually happened to the author: "In the last quarter of 2024, I delved deep into the world of Helm Charts...".
- **Personality and light humor are welcome.** Honest reactions like "Oh my God, this is so complex, am I just introducing unnecessary complexity?". Do not force jokes, but do not sand off the personality either.

### The story or motivation hook

Many of the best posts open or pivot with a small personal story: why the author cared enough to write this. A real frustration, a real meeting, a real "this got on my nerves" moment makes it human. Reuse that move.

### Sentence rhythm

- Mix sentence lengths. A long explanatory sentence followed by a short, punchy one: "The results were astonishing." / "That's the Cloud." / "I approve and recommend!"
- Let a one-line paragraph land on its own when it earns the emphasis.
- Use short asides the way people speak, with commas or parentheses, never em dashes.
- Rhetorical questions are fine, especially to set up a section: "But, what is Fuzzy Finder?"

### Keep the natural imperfections

The author is a non-native English speaker, and the posts have small grammatical quirks (for example "It is force me to memorize", "a advanced and highly customizable"). Do not aggressively correct the voice into flawless textbook English. Fix genuine typos and clarity problems, but keep the slightly informal, direct phrasing and prefer the author's real wording over a smoother rewrite. When in doubt, match the imperfect-but-clear tone of existing posts.

### Anti-patterns (do NOT do these)

- Emojis of any kind.
- Em dashes or en dashes.
- Empty hype adjectives with no substance: "powerful", "seamless", "robust", "game-changing", "cutting-edge", "leverage synergies". A little "awesome/amazing/really nice" is on-brand when it is a genuine personal reaction. The difference is sincerity, not a vocabulary ban.
- The "In today's fast-paced world..." / "In the ever-evolving landscape of..." opener. Start with a concrete problem or a personal story.
- Perfectly balanced "On one hand... on the other hand..." neutrality. The author takes sides.
- Padding sentences that restate the heading or say nothing.
- Closing with a vague "In conclusion, this is a great tool that can help you."
- Over-correcting the English into native marketing prose. That erases the author's voice.
- Bullet lists where flowing prose is clearer. Use lists for genuinely parallel items (steps, features, options), not to avoid writing sentences.

### Thank collaborators

When someone helped with the content, thank them by name (and sometimes LinkedIn). This reinforces the human, community voice.

## Writing conventions

### Inline formatting

- **Bold** for key terms, tool names, and important concepts on first mention.
- _Italic_ sparingly, for emphasis or to quote a tool description.
- `code` inline for commands, file paths, parameters, and values.

### Callout notes

Use the MyST `:::{note}` directive for important side information:

```markdown
:::{note}
All code is in the following GitHub repository: ...
:::
```

### Info callouts

Blockquote with a font-awesome icon for "More Details" links:

```markdown
> _<i class="fa-solid fa-link"></i> More Details: [Link text](url)_
```

Or for info tips:

```markdown
> <i class="fa-solid fa-circle-info"></i> **About something:**
>
> Explanation text here.
```

### Code blocks

Use MyST fenced code blocks with language and optional caption:

````markdown
```{code-block} bash
:caption: $ cat /path/to/file

content here
```
````

Plain fenced blocks are fine when no caption is needed.

### Side-by-side grids

For showing two things in parallel (for example, default vs override):

```markdown
::::{grid}

:::{grid-item-card}
- **Label**
```code block here```
:::

:::{grid-item-card}
- **Label**
```code block here```
:::

::::
```

### Numbered step-by-step guides

Steps use bold numbers, optional _(optional)_ markers, and descriptive inline labels:

```markdown
- __1__ _optional_: Description here

- __2__: Description here
```

### Bullet lists for advantages or features

Use a bold label, a colon, and an explanation:

```markdown
- __Avoid Code Duplication__: Allows to use modules across multiple pipelines...
- __Reusable Code__: Allows a simple configurable way...
```

## Code examples

- Code blocks are central to most posts. Make them complete, runnable, and commented where needed.
- Show command output in the same block or a separate one labeled with a comment like `# output expected:` or `# >>> output`.
- Use real file paths as captions (for example `:caption: ~/.vimrc`).
- Environment variable names are uppercase and descriptive.
- Examples are often paired with a Docker Compose lab in the author's GitHub for hands-on testing.

## Links to personal GitHub

Posts frequently link to the author's GitHub for labs, dotfiles, and code examples:

- Labs: `https://github.com/c-neto/my-devops-labs/`
- Code examples: `https://github.com/c-neto/my-code-playground/`
- Dotfiles: `https://github.com/c-neto/ansible-configure-fedora/`

Use the GitHub icon pattern when linking:

```markdown
<i class="fab fa-github"></i> [c-neto/repo/path](https://github.com/...)
```

## Conclusion section

The conclusion is always first-person and opinionated. It:

1. Reflects on using the solution or approach in practice.
2. States the author's recommendation or verdict.
3. Acknowledges that context matters ("every case is unique").
4. Sometimes ends with a direct call to action ("I recommend...", "Give it a try!").

Pattern: _"I have been using [X] for [time/context], and I really appreciate how [it addresses recurring challenges]. [Caveat or nuance]. [Recommendation]."_

## References or links section

Posts end with a `## References` or `## Links` section: raw URLs or markdown links, one per line. No prose, just the list.

## Categories and tags reference

| Category | Common tags |
|---|---|
| Log Analytics | logstash, opensearch, fluentbit, logs, observability |
| Linux | zsh, systemd, fzf |
| Kubernetes | helm, cka, ckad, cks, kubernetes |
| Cloud | aws, gcp, azure, cloud |
| python / code | python, dynaconf |

## Humanizer pass (final step)

Run the **humanizer** skill as the last step before publishing any post, after the draft follows everything above. It rewrites text to remove AI tells and is based on Wikipedia's "Signs of AI writing".

Keep the author's voice, not a neutral rewrite:

1. Load the humanizer skill.
2. Always give it a voice sample. Without one it falls back to neutral prose. Point it at this skill plus one or two existing posts, for example `blog/2024/2024-07-21-dynaconf.md` and `blog/2025/2025-02-25-helm-best-practices.md`.
3. Ask it to humanize the prose of the draft, for example: "Humanize the prose in `blog/<year>/<file>.md`, matching the voice in this skill and `blog/2024/2024-07-21-dynaconf.md`."

The humanizer edits prose only. It leaves code blocks, inline code, commands, paths, YAML frontmatter, and link targets unchanged, and it will not invent facts. Where the humanizer and this skill disagree, this skill and the author's real voice win. This skill shares the same hard rules: no em dashes, no emojis, direct and concise prose.

## Checklist before publishing

- [ ] Frontmatter has `tags`, `date`, `category`.
- [ ] Publish date line is present after the frontmatter.
- [ ] Title is punchy and descriptive.
- [ ] Opening paragraph summarizes the post.
- [ ] Problem and solution are clearly stated.
- [ ] Code blocks have captions where relevant.
- [ ] Conclusion is first-person and includes a recommendation.
- [ ] Voice sounds like the author: first-person, opinionated, honest about trade-offs, no empty hype, no "In today's landscape..." openers.
- [ ] No emojis anywhere.
- [ ] No em dashes or en dashes (`—` / `–`) anywhere.
- [ ] Writing is direct and concise, with no filler.
- [ ] Ran the humanizer skill as a final pass with a voice sample.
- [ ] References section is present.
- [ ] While in draft, the file is in `hidden/` with no date prefix in the filename, and the slug matches the title.
- [ ] Only promote to `blog/<YEAR>/` (adding the `<YYYY-MM-DD>` date prefix) when the user explicitly asks to "promova", "promote", or "publish".

# Blog Layout

## Frontmatter, category, and tags

Every post in `blog/<YEAR>/` follows the same taxonomy. Check it whenever you create or refactor a post.

### Category

Use exactly one category, written exactly as one of these values:

| Category | Scope |
| --- | --- |
| `Observability` | Logs, metrics, traces, OpenSearch, Logstash, Fluent Bit, OpenTelemetry |
| `Kubernetes` | Kubernetes, Helm, CNCF certifications |
| `Linux` | Shell, terminal, systemd, CLI tools |
| `Python` | The language and its libraries |
| `Cloud` | Cloud concepts and providers |

Do not create a new category without the author's approval. When a post fits two categories, pick the one that matches its main subject.

### Tags

- Write tags in lowercase kebab-case, based on the official name of the tool (`fluent-bit`, `opentelemetry`).
- Use 1 to 4 tags. Put the main technology first.
- Do not repeat the category as a tag. For example, an `Observability` post never gets an `observability` tag.
- Reuse the vocabulary below. Add a new tag only when it will group at least two posts. Keep narrow concepts in the text, not in tags.
  - Tools: `opensearch`, `logstash`, `fluent-bit`, `opentelemetry`, `prometheus`, `kubernetes`, `helm`, `aws`, `gcp`, `azure`, `python`, `dynaconf`, `bash`, `zsh`, `readline`, `starship`, `fzf`, `vim`, `systemd`
  - Subjects: `logs`, `metrics`, `sharding`, `terminal`, `certification`

Format: `tags: opensearch, sharding, logs` (a comma-separated string).

### Frontmatter template

Every post starts with this frontmatter, then the publish date line and the H1. Fill in every field, and keep the field order:

```markdown
---
tags: opensearch, sharding, logs
date: "YYYY-MM-DD"
category: Observability
author: Carlos Neto
title: "<Post title, identical to the H1>"
description: "<One or two sentences summarizing the post>"
myst:
  html_meta:
    description: "<Same text as description>"
og:title: "<Same text as title>"
og:description: "<Same text as description>"
---

*__Blog Post Publish Date:__ YYYY/MM/DD*

---

# <Post title, identical to the title field>
```

| Field | Rule | Used by |
| --- | --- | --- |
| `tags` | Follow the tag rules above. Comma-separated string. | ABlog tag pages |
| `date` | Quoted `"YYYY-MM-DD"`, matching the filename prefix and the "Blog Post Publish Date" line (`YYYY/MM/DD`). | ABlog ordering and the RSS feed |
| `category` | One value from the category table above. | ABlog category pages |
| `author` | Always `Carlos Neto`. | ABlog author archive |
| `title` | Identical to the H1. | Page metadata |
| `description` | A specific summary of what the post covers, about 150 to 200 characters. No generic openings. | Search snippets |
| `myst.html_meta.description` | Same text as `description`. | `<meta name="description">` |
| `og:title` | Same text as `title`. | `sphinxext-opengraph` social cards |
| `og:description` | Same text as `description`. | `sphinxext-opengraph` social cards |

Rules:

- Keep `title`, `og:title`, and the H1 identical. Keep `description`, `myst.html_meta.description`, and `og:description` identical. When you change one, change all of them, and also the matching values in the JSON-LD block below.
- Quote any value that contains `: `, such as a title with a colon. Without quotes, MyST drops the whole frontmatter and logs only a "Malformed YAML" warning. Quoting every string value is the safest default.
- Never set an `image` key. ABlog reads it as the number of images in the excerpt, and a path breaks the build.
- Do not add keys that nothing on the site uses, such as `slug` or `canonical`.
- When you rename or remove a category or tag that was already published, add a redirect to `rediraffe_redirects` in `conf.py`.

### End of the post

Close every post in this order. Use `blog/2026/2026-11-10-opensearch-scale-down.md` as the reference.

1. `## Key Takeaways`: short bullets with the main points. This replaces a separate conclusion section. Fold the author's opinion into the body or the last section.
2. `## References`: titled links in the form `[Page title (Project)](url)`, mostly official documentation.
3. The author footer. Posts about OpenSearch, Logstash, Fluent Bit, or log pipelines use:

   ```markdown
   
---

> *I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*
   ```

   Every other post uses:

   ```markdown
   
---

> *I'm Carlos Neto, and this blog is where I share my experiences and open source contributions. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*
   ```

4. A `---` rule, then the JSON-LD block. `headline`, `description`, and `datePublished` must match the frontmatter. The slug in `url` and `mainEntityOfPage` is the filename without `.md`. Add `"image"` only when the post has a diagram in `_static/<year>/<date>/`, using its absolute URL.

   ````markdown
   ```{raw} html
   <script type="application/ld+json">
   {
     "@context": "https://schema.org",
     "@graph": [
       {
         "@type": "BlogPosting",
         "headline": "<title>",
         "description": "<description>",
         "datePublished": "YYYY-MM-DD",
         "inLanguage": "en",
         "url": "https://carlosneto.dev/blog/<YEAR>/<filename-without-.md>/",
         "mainEntityOfPage": "https://carlosneto.dev/blog/<YEAR>/<filename-without-.md>/",
         "keywords": ["<Main technology>", "<Topic>", "<Topic>"],
         "author": {"@id": "https://carlosneto.dev/#person"}
       },
       {
         "@type": "Person",
         "@id": "https://carlosneto.dev/#person",
         "name": "Carlos Neto",
         "url": "https://carlosneto.dev/",
         "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
       },
       {
         "@type": "BreadcrumbList",
         "itemListElement": [
           {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
           {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
           {"@type": "ListItem", "position": 3, "name": "<title>"}
         ]
       }
     ]
   }
   </script>
   ```
   ````

### Code blocks

- Use ` ```opensearch ` for every OpenSearch API call (request line plus optional JSON body). Write the request line inside the block, not in a `:caption:`. The lexer lives in `scripts/opensearch_lexer/`.
- Use only lexer names that Pygments knows. For log lines and Prometheus exposition output, use ` ```text `. For PromQL, use ` ```promql `.


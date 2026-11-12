---
name: blog-writer
description: Create or refactor technical blog posts to improve clarity, structure, flow, and conciseness while preserving the author's voice, technical accuracy, and original intent.
---

# Technical Post Refactor

## Purpose

Act as an experienced technical editor. Make them clearer, more concise, easier to read, and more useful to their intended audience.

The goal is to improve the article as a whole, not simply rewrite individual sentences.

Preserve the author's ideas, technical knowledge, opinions, personal experience, and writing style. Remove unnecessary complexity without removing meaningful substance.

The result should read like a well-written article by an experienced engineer, not like generic AI-generated content or academic writing.

## Core principles

### 1. Preserve the author's intent and voice

- Understand the main argument before making changes.
- Preserve the author's opinions, conclusions, personal experiences, and technical observations.
- Keep first-person experiences when they add credibility or context.
- Do not replace specific experiences with generic statements.
- Do not introduce marketing language, exaggerated claims, or artificial enthusiasm.
- Prefer natural, direct language.
- Do not make the text sound more formal than the original.
- Preserve the author's preferred terminology and vocabulary.

The author's original material is the source of truth. Editing must not change what they are trying to communicate.

### 2. Reduce unnecessary content

Be aggressive about removing content that does not help the reader understand the subject.

Look for:

- Repeated explanations across different sections.
- Paragraphs that restate the previous paragraph.
- Introductions that take too long to reach the point.
- Conclusions that repeat the entire article.
- Excessive background information.
- Generic statements that do not add technical value.
- Examples that are more complicated than the concept they explain.
- Unnecessary qualifiers and disclaimers.
- Sentences that explain something the reader can already infer.

Every paragraph should contribute new information, explain a concept, support an argument, or provide a useful example.

If two paragraphs communicate the same idea, combine them.

If a sentence does not add meaningful information, remove it.

### 3. Prefer concise writing

Use fewer words whenever the meaning remains intact.

- Prefer short, direct sentences.
- Remove unnecessary introductory phrases.
- Avoid explaining the same concept multiple times.
- Replace vague descriptions with concrete statements.
- Prefer simple verbs over unnecessarily elaborate expressions.
- Avoid long sentences with multiple unrelated ideas.
- Vary sentence length naturally.

Do not confuse conciseness with oversimplification. Technical details that are necessary to understand the argument must remain.

### 4. Avoid excessive subsections

Do not organize the article into a large number of small sections.

Use headings only when they help readers understand the article's structure or navigate distinct topics.

Prefer:

- Combining closely related sections.
- Explaining related concepts in the same section.
- Using transitions between paragraphs instead of creating a new heading.
- Keeping examples close to the concepts they illustrate.

Do not create a separate subsection for every technical detail.

A section should represent a meaningful part of the argument, not an individual observation.

There is no mandatory article structure. Choose the structure that best fits the content.

### 5. Prefer explanatory prose over excessive lists

Technical articles should generally read as connected explanations rather than collections of disconnected statements.

Use prose when explaining:

- How a system works.
- Why a design decision was made.
- The relationship between different technical components.
- Trade-offs and limitations.
- Cause-and-effect relationships.

Use bullet points when they genuinely improve readability, such as:

- Comparing independent characteristics.
- Listing requirements or configuration options.
- Summarizing distinct recommendations.
- Presenting several items that do not need individual explanations.

Do not turn every paragraph into a list. Do not use lists as a substitute for explaining relationships between ideas.

### 6. Make examples practical

Examples should help readers understand how a concept applies in a real situation.

When an explanation feels abstract:

- Introduce a realistic scenario.
- Use concrete numbers when they are available and relevant.
- Explain what happens step by step.
- Connect configuration parameters to their actual effects.
- Explain why the behavior matters operationally.

Avoid unnecessarily complex examples.

A good example should make the concept easier to understand, not introduce additional concepts that require further explanation.

Do not invent production experiences, measurements, benchmark results, or numerical values.

## Technical accuracy and references

### 7. Validate technical claims

Treat technical accuracy as a priority.

During the refactor:

- Identify claims that require evidence.
- Distinguish documented behavior from personal experience and interpretation.
- Verify important technical details against authoritative documentation when necessary.
- Preserve existing references whenever they support the claims.
- Add references when a claim needs support and a reliable source is available.
- Remove claims that cannot be verified or appropriately qualified.
- Do not present assumptions as documented behavior.
- Do not turn a specific observation into a universal statement.

Prefer primary sources:

1. Official product documentation.
2. Official specifications and standards.
3. Official engineering blogs and technical publications.
4. Reputable third-party technical sources.

Avoid adding references merely to make the article look more authoritative.

A reference must support the specific claim associated with it.

### 8. Preserve important limitations and trade-offs

Do not make the article more persuasive by hiding disadvantages.

Keep relevant information about:

- Operational complexity.
- Failure scenarios.
- Performance limitations.
- Cost implications.
- Compatibility.
- Reliability and availability.
- Configuration requirements.

When a recommendation depends on specific conditions, make those conditions clear.

Avoid absolute statements when the actual behavior depends on configuration or environment.

## Article structure

### 9. Improve the narrative flow

The article should have a clear progression.

A useful general approach is:

1. Introduce the problem or observation.
2. Explain why the problem matters.
3. Present the proposed approach.
4. Explain how it works.
5. Discuss practical considerations and trade-offs.
6. End with the main takeaways.

This is a guideline, not a mandatory template.

Reorder sections when it improves the argument.

Avoid introducing technical details before readers understand why they matter.

Each section should naturally lead to the next one.

### 10. Write stronger introductions

An introduction should quickly establish:

- The context.
- The problem or motivation.
- The author's perspective or experience, when relevant.
- What the article intends to explain.

Avoid generic openings such as "In today's fast-paced technological landscape."

Do not spend several paragraphs explaining background information that can be covered later.

Get to the central idea quickly.

### 11. Write useful conclusions

The conclusion should reinforce the article's main takeaways without repeating every section.

Avoid generic closing paragraphs, motivational statements, and exaggerated claims.

Prefer concrete observations and practical implications.

If the author requests a specific conclusion format, follow it. For example, a short list of ten independent sentences may be more appropriate than a conventional concluding paragraph.

Do not impose a conclusion format without considering the author's preference.

## Language and style

### 12. Avoid generic AI writing patterns

The final article must sound natural and specific to its subject.

Avoid:

- "In today's world..."
- "It is important to note that..."
- "This highlights the importance of..."
- "At its core..."
- "The key takeaway is..."
- "Not only X, but also Y" when the contrast adds no real information.
- Repetitive one-line paragraphs.
- Artificially dramatic conclusions.
- Forced groups of three examples.
- Excessive em dashes.
- Unnecessary bold text.
- Marketing expressions such as "game-changing", "revolutionary", and "powerful solution".

Do not replace these expressions mechanically. Rewrite the surrounding sentences when necessary.

### 13. Keep the writing accessible

Assume the reader has technical knowledge but may not be familiar with the specific subject.

- Explain specialized concepts when they first become relevant.
- Avoid unnecessary jargon.
- Do not explain basic concepts that the intended audience is expected to know.
- Use precise technical terminology.
- Prefer practical explanations over academic definitions.

The article should be easy to follow without becoming superficial.

## Refactoring workflow

Follow this process before delivering the final article.

### Phase 1: Understand

Read the entire article before editing.

Identify:

- Its central argument.
- The intended audience.
- The author's motivation.
- The most important technical points.
- Personal experiences and observations.
- Claims that require references.
- Repeated or unnecessary explanations.

Do not start rewriting after reading only the introduction.

### Phase 2: Evaluate

Assess the article's current structure and identify:

- Sections that can be merged.
- Paragraphs that can be shortened.
- Explanations that are repeated.
- Abstract examples that need improvement.
- Unsupported technical claims.
- Content that does not contribute to the central argument.
- Missing transitions or context.

Prioritize structural improvements before sentence-level polishing.

### Phase 3: Refactor

Rewrite the article using the principles above.

You may:

- Reorder sections.
- Merge or remove subsections.
- Rewrite paragraphs.
- Replace abstract examples with practical ones.
- Remove redundant content.
- Simplify explanations.
- Improve transitions.
- Shorten the introduction and conclusion.

You must not:

- Invent experiences or results.
- Change the author's position.
- Remove important technical qualifications.
- Introduce unsupported claims.
- Change code, commands, configuration values, or URLs without a clear reason.

### Phase 4: Verify

Review the complete rewritten article.

Check that:

- The central argument remains intact.
- All important information from the original is preserved.
- No explanations are unnecessarily repeated.
- The article flows naturally from beginning to end.
- Technical claims are accurate and appropriately qualified.
- References support the claims they accompany.
- Examples are understandable and realistic.
- The article does not contain unnecessary subsections.
- The writing is concise without losing technical depth.
- The author's voice is still recognizable.

### Phase 5: Deliver

Present the complete refactored article.

After the article, provide a brief summary of the most relevant editorial changes, such as:

- Sections merged or removed.
- Redundant explanations eliminated.
- Technical claims corrected or qualified.
- Examples improved.
- References added or adjusted.

Do not provide a lengthy explanation of every sentence-level change unless requested.

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
3. The author footer:

   ```markdown
   *I'm Carlos Neto, and I've been running OpenSearch on EKS for over five years. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/).*
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

## Interaction guidelines

- If the user provides the complete article, begin the review without asking unnecessary questions.
- If the article is available through a URL, read its actual content before editing.
- If only part of the article is available, clarify whether the user wants to refactor that portion or provide the complete article.
- If a technical claim cannot be verified, flag it rather than silently inventing a correction.
- If the user's feedback conflicts with an earlier editorial decision, follow the latest explicit instruction.
- Preserve formatting, code blocks, links, and metadata unless the requested refactor requires changing them.

## Final editorial standard

The final article should communicate the same ideas with less friction.

Readers should reach the main point faster, understand technical concepts more easily, and retain the important details without having to navigate unnecessary explanations.

**The goal is not to make the article shorter at any cost. The goal is to make every part of it worth reading.**

# Notes

- The last topic is the `Key Takeaways` with bullet points with summary of the article's main points, not a generic conclusion.
- The first paragraph is a summary of the article. It is used as a preview in search results and social media. It should be concise, clear, and informative. Avoid generic statements that do not convey the article's specific content.
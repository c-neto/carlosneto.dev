# Writing Directives

Best practices for writing and editing content for carlosneto.dev. Part of the `blog-creator` skill.

## When these directives apply

Always. They apply to every request in this repository that writes or edits text, from a single sentence to a whole post: edits to a passage, new posts, rewrites, drafts in `draft/`, refactor rounds, analyzer fixes, `humanizer` passes, site pages such as `index.md` and `blog.md`, and copy produced by `scripts/social_media/`. They also apply when the request does not mention them, and when the work runs through another skill (`blog-write`, `blog-rewrite`, `blog-analyze`, `humanizer`, or any `/blog` subcommand).

When another skill, template, or analyzer suggestion conflicts with these directives, the directives win. Mention the skipped suggestion and the directive that blocked it in the report to the author.

Before delivering any written content, check it against the hard rules at the end of this file.

The goal is to make the article clear, concise, easy to read, and useful to its intended audience, improving the article as a whole rather than individual sentences.

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

Do not use bullet points in the body of a post. Write connected prose, even for independent items such as perks, skills, requirements, or recommendations. Bullets belong only in `## Key Takeaways` and `## References`, which the layout requires. Tables are acceptable when they compare data. Analyzer suggestions to add lists "for structure" lose to this rule.

Do not use lists as a substitute for explaining relationships between ideas.

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

The introduction is a single paragraph with a single sentence, placed between the H1 and the first H2. It starts with "This blog post covers" and says what the post covers and what the reader ends up with (the final result, example, or conclusion). It is the preview in link-sharing thumbnails, so it only tells the reader what the post contains. Do not add a second introductory paragraph. Background, context, and motivation belong in the first section.

Example: "This blog post covers how Helm's `global` key passes values from a parent chart to its subcharts, ending with an umbrella chart that sets one image tag for five modules in a single place."

Avoid generic openings such as "In today's fast-paced technological landscape."

### 11. Write useful conclusions

The conclusion should reinforce the article's main takeaways without repeating every section.

Avoid generic closing paragraphs, motivational statements, and exaggerated claims.

Prefer concrete observations and practical implications.

On this site the conclusion is the `## Key Takeaways` section. Write each item as advice or a general statement, never in first person ("I", "my", "me"). The body keeps the author's first-person voice.

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
- Colons in the middle of a sentence, such as "it gave me what I wanted: a deeper understanding". Split it into two sentences or rewrite it with a comma or a connecting word. This does not apply to code, commands, URLs, frontmatter, times, or bold labels at the start of a paragraph (`__Go to the Gym__:`).
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

## Hard rules

Always:

- Write all site content in English, whatever language the author uses in the chat or the draft.
- Keep the author's first-person experience in the body.
- Open every post with a single one-sentence paragraph that starts with "This blog post covers" and states what the post covers and its final result, followed directly by the first H2 (see directive 10).

Never:

- Invent experiences or results.
- Add bullet lists to the body of a post.
- Use first person in Key Takeaways.
- Use a colon in the middle of a sentence (see directive 12).
- Change the author's position.
- Remove important technical qualifications.
- Introduce unsupported claims.
- Change code, commands, configuration values, or URLs without a clear reason.

## Final editorial standard

The final article should communicate the same ideas with less friction.

Readers should reach the main point faster, understand technical concepts more easily, and retain the important details without having to navigate unnecessary explanations.

**The goal is not to make the article shorter at any cost. The goal is to make every part of it worth reading.**

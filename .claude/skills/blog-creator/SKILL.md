---
name: blog-creator
description: Writing skill for carlosneto.dev, with the author's text conventions in written-directives.md. Use it on EVERY request that writes or edits text in this repository, including small ones like "rewrite this sentence", "add this to the post", "mention X in section Y", or "this paragraph sounds wrong". Edit mode applies the conventions to the requested passage and finishes with the humanizer skill. New-post mode runs the interview, /blog write, /blog analyze, 3 refactor rounds, and humanizer. Use new-post mode when the user invokes /blog-creator or asks to create a new blog post.
---

# Blog Creator

This blog shares the author's own experience with the subjects, not generic technical guides. Every post must carry the author's personality: what they ran into, what they decided, what went wrong, and what they think.

The skill has two modes. Both follow [written-directives.md](./written-directives.md), the author's text conventions. Read it before writing or changing any text, even a single sentence.

## Edit Mode

Use this mode when the author asks to edit, rewrite, add, or remove a passage of an existing post or page. It is the default for any request that changes text and is not a new post.

1. Read [written-directives.md](./written-directives.md) in this turn, even if it was read earlier in the conversation, since the author may have changed it.
2. Read the current version of the file around the passage. The author often edits files between requests, so never rely on an earlier read.
3. Change only what the author asked for. Keep the surrounding text, unless the change makes it inconsistent (for example, "my main motivation" when a second motivation is added). When the request is a rewrite or refactor of a post, or touches its introduction, also apply the opening sentence rule from Post Rules. If the introduction is not a single sentence starting with "This blog post covers", rewrite it, and move any context it held into the first section.
4. Before saving, check the new text against the hard rules at the end of [written-directives.md](./written-directives.md). Then check the language and style rules, such as no colons in the middle of a sentence, no bullets in the body, and no first person in Key Takeaways.
5. Run the `humanizer` skill on the changed passage as the last step. Use the rest of the same post as the voice sample. Pass only the passage, not the whole post, and keep its meaning and the author's wording where they asked for it. Check the result against [written-directives.md](./written-directives.md) again, since the humanizer can reintroduce what the directives forbid. If the `humanizer` skill is not available in the session, stop and tell the author instead of skipping the step.
6. Reply with the final text quoted and a short note on the choices that changed the meaning or tone. If the request is ambiguous (for example, "this sentence" without saying which one), say which passage was changed.

Do not run the interview, `/blog write`, or `/blog analyze` in this mode unless the author asks.

## New-Post Mode

The flow below exists to collect the author's material before any writing starts. Follow the steps in order. Do not skip a step, and do not start writing before the interview is done.

## Step 1: Get the Draft

Ask the author for a draft: an open text where they describe, loosely, what the post is about. Offer two options:

- Write the draft in the chat.
- Use a file from the repository.

Wait for the answer. Read the chosen file completely if the author picks one.

## Step 2: Interview the Author

Analyze the draft and identify where it reads like a generic guide instead of the author's experience. Then ask **at least 3 questions** about the author's personal experience with what they wrote. Good questions ask for:

- The real situation that led to the topic (the incident, the project, the cost problem).
- Decisions the author made, the alternatives they rejected, and why.
- What went wrong, what surprised them, or what they would do differently.
- Concrete numbers from their environment (cluster size, data volume, cost, time), only if they have them.
- Their opinion on the trade-offs.

Ask the questions as open text in the chat and wait for the answers. Ask follow-up questions when an answer opens a better story. Do not proceed until the author has answered.

The answers are the source of every first-person statement in the post. Never invent experiences, incidents, numbers, or opinions. If something is missing, ask.

## Step 3: Create the Post File

- Get today's date with `date +%F`. The post uses the date it was created.
- Create the file at `blog/<YEAR>/<YYYY-MM-DD>-<slug>.md`, with a short kebab-case slug.
- Diagrams, if any, go in `_static/<YEAR>/<YYYY-MM-DD>/`.

## Step 4: Write with /blog write

The writing must be done with the `blog-write` skill (`/blog write`). Pass it:

- The draft from Step 1 and the interview answers from Step 2, labeled as the author's own material.
- The target file path from Step 3.

The repository layout wins over `blog-write` conventions:

- Use the frontmatter from `blog-layout.md` exactly. Never add `image`, `slug`, `canonical`, `coverImage`, `ogImage`, or hero fields.
- No generated hero image and no paid image or audio calls.
- Markdown for Sphinx/MyST, not MDX.

## Step 5: Analyze with /blog analyze

Run the `blog-analyze` skill on the new file. Record the total score and the score of each category.

## Step 6: Refactor 3 Times

Do exactly 3 refactor rounds. In each round:

1. Pick the fixes from the latest analysis that raise the lowest-scoring categories.
2. Apply them to the post.
3. Run `blog-analyze` again and record the scores.

Constraints for every round:

- Keep the author's experience, opinions, and voice. Never trade them for points.
- Never add invented experience, statistics, or numbers. Statistics and technical claims need a real source, preferably official documentation.
- Keep the layout from `blog-layout.md` intact.
- Keep the opening sentence rule from Post Rules. The introduction stays a single sentence that starts with "This blog post covers", with no second introductory paragraph, even when an analyzer suggests a different opening.
- Follow [written-directives.md](./written-directives.md). When an analyzer fix conflicts with a directive (for example, adding subsections or lists that break the explanatory prose), the directive wins.
- Some analyzer points are not worth chasing on this site: a frontmatter `slug` or `canonical`, hero images, and links added only to reach tier-1 domains. Skip those and say so.
- If a round lowers the score, revert that round's changes and try a different fix.

## Step 7: Humanize

Run the `humanizer` skill on the final post as the last step. Give it a voice sample: one or two recent posts by the author from `blog/<YEAR>/`. Keep code blocks, commands, configuration values, frontmatter, and the JSON-LD block unchanged.

If the `humanizer` skill is not available in the session, stop and tell the author instead of skipping the step.

## Step 8: Report

Show the author:

- The path of the new post.
- A table with the scores from the first analysis and after each refactor round.
- The main changes of each round, and the analyzer suggestions that were skipped and why.
- Any claim that still needs a source or the author's confirmation.

## Post Rules

- Write every post, and all content created for the site, in English, regardless of the language the author uses in the chat or in the draft.
- The introduction is a single paragraph with a single sentence, between the H1 and the first H2. It starts with "This blog post covers" and says what the post covers and what the reader ends up with (the final result, example, or conclusion). It is the preview shown in link-sharing thumbnails, search results, and social media. Do not add a second introductory paragraph. Background and context belong in the first section. Example: "This blog post covers how Helm's `global` key passes values from a parent chart to its subcharts, ending with an umbrella chart that sets one image tag for five modules in a single place."
- Write in first person where the author's experience is involved. The post should read as someone who did this work, not as documentation.
- The last section before References is `## Key Takeaways`, with bullet points summarizing the main points, not a generic conclusion.
- Read [blog-layout.md](./blog-layout.md) for the frontmatter template, the end-of-post order, the author footer, the JSON-LD block, and the code block rules. They are required for every post.

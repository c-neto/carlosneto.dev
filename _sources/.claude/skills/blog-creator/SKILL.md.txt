---
name: blog-creator
description: Create a new post for carlosneto.dev from the author's draft and personal experience. Runs an interview (draft, then at least 3 questions about the author's experience), writes the post with /blog write, scores it with /blog analyze, refactors it 3 times against the analyzer's metrics, and finishes with the humanizer skill. Use when the user invokes /blog-creator or asks to create a new blog post.
---

# Blog Creator

This blog shares the author's own experience with the subjects, not generic technical guides. Every post must carry the author's personality: what they ran into, what they decided, what went wrong, and what they think. The flow below exists to collect that material before any writing starts.

Follow the steps in order. Do not skip a step, and do not start writing before the interview is done.

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
- The rules from [blog-layout.md](./blog-layout.md) and the "Post Rules" section below, stating that they override `blog-write` defaults where they conflict.

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

- The first paragraph is a summary of the post. It is used as a preview in search results and social media. Make it concise, clear, and specific. Avoid generic statements that do not convey the post's content.
- Write in first person where the author's experience is involved. The post should read as someone who did this work, not as documentation.
- The last section before References is `## Key Takeaways`, with bullet points summarizing the main points, not a generic conclusion.
- Read [blog-layout.md](./blog-layout.md) for the frontmatter template, the end-of-post order, the author footer, the JSON-LD block, and the code block rules. They are required for every post.

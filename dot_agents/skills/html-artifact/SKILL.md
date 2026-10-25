---
name: html-artifact
description: Use when the user asks for an HTML artifact or HTML page of a plan, workflow, analysis, comparison, or results, to visualise one as a web page, or for an interactive figure or explorer, in a page or inline in a T3 thread. Produces one concise, visual, house-styled HTML file from the template; not for Markdown documents.
---

# HTML artifact

One self-contained page in the house style: a sticky table of contents on the
left, a lead paragraph, and sections that show their point with a diagram,
chart, table, or tiles before they say it in prose. The template is fixed; you
supply content and visuals only. A figure may be interactive: sliders, toggles
and hover readouts drawn by the template's own runtime.

## 1. Collect

Read every source the ask names (plan, spec, results, transcript) in full.
Done when you can state the page's single claim in one sentence.

## 2. Outline

The title names the subject. One lead paragraph. Each h2 is a TOC entry and a
claim, not a topic. Pick the section shape for the ask from
[references/writing.md](references/writing.md). Done when the outline fits the
ask with no section you could cut.

## 3. Choose visuals first

For each section pick the one visual that shows the point, using the table in
[references/visuals.md](references/visuals.md), or none when a sentence is
faster. Done when every section has a visual decision written down.

When the point is how a result responds to an input, or the reader needs exact
values across series, make the figure interactive following
[references/interactive.md](references/interactive.md). For what changed, what
became of each planned item, the evidence behind a claim, how a mechanism
works step by step, when work ran, or what the reader must decide, use the
components in [references/components.md](references/components.md); it is a
guide, not a checklist.

Diagrams are Excalidraw. For a huge diagram you may offer hand-drawn Mermaid,
and use it only when the user explicitly chooses it. Generate diagrams with the bundled Bun command in
[references/excalidraw.md](references/excalidraw.md). It installs locked packages
outside the skill and repository; do not reconstruct the setup or vendor dependencies.

## 4. Write concisely

Follow `references/writing.md`. Prose covers only what the visual cannot.
Read the sibling skill `../humanizer/SKILL.md` (it is manual-only, so read the
file rather than invoking it) and apply its rules to the finished text. Done
when no paragraph restates its neighbouring figure.

## 5. Fill the template

Copy `assets/template.html` to the destination, replace every
`<!-- SLOT: ... -->`, and leave the tokens, layout CSS, and scripts untouched.
Fill the favicon slot with the line `scripts/favicon.py --dir <project>` prints.
It hashes the repository name into a dot pattern and accent, so pages from
one project share a tab icon; pass `--project` outside a repository. When the
user wants a specific look for a project, pin it once with
`git config zendots.favicon "<accent> <pattern>"` (either part may be left
out); every worktree reads it. Pass `--color` or `--pattern` only for a
one-off page.
Give each h2 an id. Every visual sits in a `<figure>` with a manuscript-style
caption (tables in `<figure class="table">`, caption first); the template
numbers them. Embed Excalidraw SVG exports as described in `references/visuals.md`.
User-chosen Mermaid goes in `<pre class="mermaid">`, a Vega-Lite spec in
`<div class="vega"><script type="application/json">`, an interactive figure's
`<div class="viz" id="...">` fragment before its `<figcaption>`. A diff view
is the output of `scripts/diff.py`, pasted as it stands. `assets/example.html`
is a component catalogue, not a model for length. It includes an Excalidraw
figure and a hand-drawn Mermaid example explicitly labelled as opt-in.

To update an existing page, edit its `<main>` in place and leave its copied
CSS and script alone; regenerate from the template only when the user asks
for the current house style.

## 6. Check

```bash
python3 <skill-dir>/scripts/check.py <file>
```

Fix every `ERROR`. Done when the checker prints `OK`. The checker reads the
file and never renders it, so it cannot see a Mermaid block that fails to
parse or a chart that comes out empty; re-read those specs yourself.
Open the final page in T3's built-in browser when available and check both
themes, labels, arrow bindings, and narrow-screen scrolling. Drive every
interactive figure as `references/interactive.md` describes. If browser review
is unavailable, report that limit rather than treating the checker as visual proof.

## 7. Deliver

Use the project's established ignored artifact folder, such as
`docs/superpowers/` or `docs/drafts/<feature>/`. Otherwise use
`docs/drafts/<slug>/<slug>.html` and add `/docs/drafts/` to Git's local
exclude file, located by `git rev-parse --git-path info/exclude`.
Change tracked `.gitignore` rules only when the project or user requests it.
Keep required local assets and diagram sources together in that folder;
check each path with `git check-ignore <path>`. Personal artifacts stay out
of commits. Preserve maintained published documentation and product HTML;
publishing a personal artifact on GitHub requires explicit user approval.
Honor an explicit destination, ensuring personal output there stays ignored.

When working in a worktree, report the paths needed to preserve a useful
feature-summary HTML before worktree removal. Merge cleanup copies it and
its required dependencies to an ignored folder in the main checkout; this
does not put it on the main branch. Completed test screenshots, raw reports,
and logs are disposable even when earlier messages linked them.

Report the absolute HTML path. For a visual the user wants in the conversation, wrap
the fragment with `scripts/render.py` and show it with T3's `html_render`, as
`references/interactive.md` describes. Publish only
when the user asks for a link and the harness has an artifact tool, following
the publishing note in `references/writing.md`.

Locally maintained. Draws on Claude's artifact-design and dataviz guidance,
[nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer)
for the navigation and Mermaid theming, and Theo Browne's html-communication
skill for density.

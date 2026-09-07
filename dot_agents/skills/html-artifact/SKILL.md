---
name: html-artifact
description: Use when the user asks for an HTML artifact or HTML page of a plan, workflow, analysis, comparison, or results, or to visualise one as a web page. Produces one concise, visual, house-styled HTML file from the template; not for Markdown documents.
---

# HTML artifact

One self-contained page in the house style: a sticky table of contents on the
left, a lead paragraph, and sections that show their point with a diagram,
chart, table, or tiles before they say it in prose. The template is fixed; you
supply content and visuals only.

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

## 4. Write concisely

Follow `references/writing.md`. Prose covers only what the visual cannot.
Apply the `unslop` rules as you draft. Then read the sibling skill
`../humanizer/SKILL.md` (it is manual-only, so read the file rather than
invoking it) and apply its rules to the finished text. Done when no paragraph
restates its neighbouring figure.

## 5. Fill the template

Copy `assets/template.html` to the destination, replace every
`<!-- SLOT: ... -->`, and leave the tokens, layout CSS, and scripts untouched.
Give each h2 an id. Every visual sits in a `<figure>` with a manuscript-style
caption (tables in `<figure class="table">`, caption first); the template
numbers them. Mermaid goes in `<pre class="mermaid">`, a Vega-Lite spec in
`<div class="vega"><script type="application/json">`. `assets/example.html`
shows every component once; it is a catalogue, not a model for length.

To update an existing page, edit its `<main>` in place and leave its copied
CSS and script alone; regenerate from the template only when the user asks
for the current house style.

## 6. Check

```bash
python3 <skill-dir>/scripts/check.py <file> --screenshot
```

Fix every `ERROR`; read the screenshot and fix what looks wrong. The capture
waits for the CDN libraries; pass `--size 1400,900` when the ask was one
screen. Done when the checker prints `OK`.

## 7. Deliver

Write to the project's docs directory as `docs/<slug>.html`, or the location
the project already uses for artifacts. Report the absolute path. Publish only
when the user asks for a link and the harness has an artifact tool, following
the publishing note in `references/writing.md`.

Locally maintained. Draws on Claude's artifact-design and dataviz guidance,
[nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer)
for the navigation and Mermaid theming, and Theo Browne's html-communication
skill for density.

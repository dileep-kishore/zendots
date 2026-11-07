---
name: build-reveal-deck
description: Use when the user asks for a talk, slide deck or presentation, including turning a PowerPoint file into one, or to change, check, or export to PDF or Notion an existing reveal.js deck. Not for producing .pptx files.
---

# Build reveal.js deck

This skill builds a light, animated reveal.js deck. The user presents it by
sharing a browser tab.

A deck is a folder:

- `index.html` holds the slides.
- `brief.md` holds the interview answers.
- `deck.css` holds this deck's own styles.
- `base.css`, `theme.css`, `deck.js` and `lib/` are copied from the template.

`scripts/deck.py` creates, checks and exports the deck. Before the outline,
read [references/preferences.md](references/preferences.md). It holds the
user's standing asks, and most past rework came from breaking one of them.

## 1. Gather, then ask

Read every source the user named, such as the agenda, meeting notes, earlier
decks or reports. Then interview the user as
[references/interview.md](references/interview.md) describes. Ask one pointed
question at a time with the host's question tool, and only about what the
sources leave open. Record the answers in the deck's `brief.md`.

For research-heavy talks, run the web research in parallel subagents. Ask the
other vendor's model (Codex from Claude, Claude from Codex) to critique the
outline and, later, the rendered screenshots.

Done when `brief.md` states the audience, the goal and the one sentence the
audience should remember.

## 2. Choose where it lives, then create it

Put the deck where html-artifact pages go:

- **In a git project:** use the project's established ignored artifact
  folder, such as `docs/superpowers/<topic>/` or `docs/drafts/<slug>/`.
  Otherwise use `docs/drafts/<slug>/` and add `/docs/drafts/` to the file
  `git rev-parse --git-path info/exclude` prints. Change tracked `.gitignore`
  rules only when the project or user asks. Never commit a deck unless asked.
- **When the user asks for the Presentations folder:** use a subfolder for
  this deck, `/Volumes/WorkSSD/Work/Presentations/<Topic>_<YYYY>_<Mon>/`.
- **Anywhere else:** use the destination the user names.

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py new <deck folder> \
  --template default|kbase --title "<title>" [--date "6 November 2026"]
```

`new` refuses a folder that is not empty. Inside a git work tree it also
refuses a folder git would track; pass `--tracked` only when the user wants
the deck committed.

In a worktree, report the deck path before the worktree is removed, so the
deck can be copied to the main checkout's ignored folder.

Use `kbase` for a KBase audience or host, and `default` otherwise. The
starter's slides only show layouts to copy: a title slide, a diagram, a text
slide, a comparison, numbers and a bullet summary. Replace them with the
talk's own slides.

To build from a PowerPoint file, extract it first:

```bash
uv run --with python-pptx python3 ~/.agents/skills/build-reveal-deck/scripts/pptx_extract.py <file.pptx> <out folder>
```

This writes `outline.md`, which has each slide's text and notes, plus the
images in `media/`. Rebuild the slides in reveal.js from those, rather than
copying the PowerPoint layout.

To restyle a deck to an organisation's template, back it up first, to
`backups/deck-before-<change>-<YYYYMMDD-HHMM>.tgz`. Copy the template's
look (colours, header, logos) and favour clean aesthetics over a pixel-exact
copy.

## 3. Outline, then write the slides

Show the outline as one line per slide: its title, its purpose and its
layout. Ask the outline questions in
[references/interview.md](references/interview.md) before you build.

Then follow [references/components.md](references/components.md) for the
frame, the components, colour roles, density and animation. Arrows are the
most common defect:

- An arrowhead appears exactly when its line finishes drawing.
- No arrow appears before both of its boxes.

Put each slide in an `<!-- N Name -->` comment block.

## 4. Look at it, check it, fix it

Look at the slides in a real browser, choosing by where you run:

- **T3 Code:** use T3's built-in browser preview. Serve the deck first with
  `python3 -m http.server <port> --bind 127.0.0.1` from the deck folder,
  open `http://127.0.0.1:<port>/`, and take screenshots or snapshots.
- **Anywhere else:** use Chrome through the Claude in Chrome extension when
  it is connected, or another browser tool the host provides.

Click through each slide you changed from its first state to its last. Check
the animation order, the arrow timing and the text against the logos. Close
any tab you opened, and stop the server you started.

Then run the headless audit, at the presenting size and at least once at a
projector shape:

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py check <deck> [--size 1280x960]
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py steps <deck> <slide>
```

`check` screenshots every slide after its last click and reports these
problems:

- titles that run past one line;
- text overflowing its box;
- anything off the slide or over the footer logos;
- missing or broken arrowheads;
- boxes that vanish after leaving a slide and coming back;
- images, page errors and requests that fail to load.

`steps` screenshots one slide at every click. When no browser tool is
available, these screenshots are the visual check, so open them and look.

Loop until `check` exits 0 and the slides look right in the browser. After a
round of fixes, ask the post-render questions from the interview guide.

## 5. Export when asked

`deck.py pdf <deck>` writes one page per slide, each in its final state.
`deck.py bundle <deck>` writes one self-contained HTML file.
[references/export.md](references/export.md) covers putting them on a Notion
page.

## Output

Report:

- the deck path, and whether git ignores it;
- one line per slide;
- the `check` result;
- what you inspected in the browser, and what you did not.

For each claim about other tools, and for each number, give the source you
checked it against.

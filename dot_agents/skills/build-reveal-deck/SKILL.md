---
name: build-reveal-deck
description: Use when the user asks for a talk, slide deck or presentation (animated reveal.js, default or KBase theme), or to change, check, or export to PDF or Notion a deck under /Volumes/WorkSSD/Work/Presentations. Not for PowerPoint files.
---

# Build reveal.js deck

This skill builds a light, animated reveal.js deck. The user presents it by
sharing a browser tab.

A deck is a folder. `index.html` holds the slides and `deck.css` holds this
deck's own styles. `base.css`, `theme.css`, `deck.js` and `lib/` are copied
from the template. `scripts/deck.py` creates, checks and exports the deck.

Before the outline, read
[references/preferences.md](references/preferences.md). It holds the user's
standing asks, and most past rework came from breaking one of them.

## 1. Gather and frame

Read every source the ask names, such as the agenda, meeting notes, earlier
decks or reports. Work out four things:

- who the audience is;
- which organisation hosts the talk;
- how long the slot is;
- what the audience should leave with.

If the slot length is unknown, ask the user before drafting.

For research-heavy talks, run the web research in parallel subagents. Ask the
other vendor's model (Codex from Claude, Claude from Codex) to critique the
outline and, later, the rendered screenshots. Save each round to a file.

Done when you can state the talk's claim in one sentence.

## 2. Create the deck

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py new \
  "/Volumes/WorkSSD/Work/Presentations/<Topic>_<YYYY>_<Mon>" \
  --template default|kbase --title "<title>" [--date "6 November 2026"]
```

Use `kbase` for a KBase audience or host, and `default` otherwise. `new`
refuses a folder that is not empty.

The starter's slides only show layouts you can copy: a title slide, a diagram,
a text slide, a comparison, numbers, and a bullet summary. Replace them with
the talk's own slides. Use as many slides as the slot needs.

To restyle a deck to an organisation's template, back it up first, to
`backups/deck-before-<change>-<YYYYMMDD-HHMM>.tgz`. Copy the template's look
(colours, header, logos) and favour clean aesthetics over a pixel-exact copy.

## 3. Write the slides

Follow [references/components.md](references/components.md) for the slide
frame, components, colour roles and animation rules. Arrows are the most
common defect:

- An arrowhead appears exactly when its line finishes drawing.
- No arrow appears before both of its boxes.

Put each slide in an `<!-- N Name -->` comment block, so it can be found and
edited on its own.

## 4. Look at it, check it, fix it

Look at the slides in a real browser, choosing by where you run:

- **T3 Code:** use T3's built-in browser preview. Serve the deck first with
  `python3 -m http.server <port> --bind 127.0.0.1` from the deck folder,
  open `http://127.0.0.1:<port>/`, and take screenshots or snapshots.
- **Orca:** use Orca's embedded browser through the `orca-cli` skill. Do not
  drive Orca when you run under another host.
- **Anywhere else:** use Chrome through the Claude in Chrome extension when
  it is connected, or another browser tool the host provides.

Click through each slide you changed from its first state to its last. Check
the animation order, the arrow timing and the text against the logos. Close
any tab you opened, and stop the server you started.

Then run the headless audit:

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py check <deck>
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
available, these screenshots are the visual check. Open them and look.

Loop until `check` exits 0 and the slides look right in the browser. A clean
report alone does not prove the slides look right.

## 5. Export when asked

`deck.py pdf <deck>` writes one page per slide, each in its final state.
`deck.py bundle <deck>` writes one self-contained HTML file.
[references/export.md](references/export.md) covers putting them on a Notion
page.

## Output

Report:

- the deck path;
- one line per slide;
- the `check` result;
- what you inspected in the browser, and what you did not.

For each claim about other tools, and for each number, give the source you
checked it against.

---
name: build-reveal-deck
description: Use when the user asks for a talk, slide deck or presentation (animated reveal.js, default or KBase theme), or to change, check, or export to PDF or Notion a deck under /Volumes/WorkSSD/Work/Presentations. Not for PowerPoint files.
---

# Build reveal.js deck

Builds a light, animated reveal.js deck the user presents by sharing a browser
tab. A slide is a title, one visual that fills the stage, and at most one or
two takeaway bullets. The deck is a folder: `index.html`, `deck.css` for this
deck's own styles, plus `base.css`, `theme.css`, `deck.js` and `lib/` copied
from the template. `scripts/deck.py` creates, checks and exports it.

Read [references/preferences.md](references/preferences.md) before the
outline. It holds the user's standing asks, and most past rework came from
breaking one of them.

## 1. Gather and frame

Read every source the ask names: the agenda, meeting notes (Granola), earlier
decks, project reports. When the talk is for a meeting, map each agenda
objective to the slide that answers it. Write down the objection the room is
most likely to raise ("if we have X, why do we need Y?"). One slide must
answer it. Done when you can state the talk's claim in one sentence and name
the audience and host organisation.

For research-heavy talks, run the web research in parallel subagents. Ask the
other vendor's model (Codex from Claude, Claude from Codex) to critique the
outline, and later the rendered screenshots. Save each round to a file and
fix what it confirms.

## 2. Create the deck

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py new \
  "/Volumes/WorkSSD/Work/Presentations/<Topic>_<YYYY>_<Mon>" \
  --template default|kbase --title "<title>" [--date "6 November 2026"]
```

Use `kbase` for any talk to a KBase audience or hosted by KBase, and `default`
otherwise. `new` refuses a non-empty folder. The starter has five example
slides: title, flow, gaps-to-plan, real-data evidence and summary. Keep the
patterns you need, delete the rest, and aim for 10 to 12 slides for a short
talk.

To restyle an existing deck to an organisation's template, first back it up
(`backups/deck-before-<change>-<YYYYMMDD-HHMM>.tgz`). Copy the look of the
template (colours, header, logos) and favour clean aesthetics over a
pixel-exact copy.

## 3. Write the slides

Follow [references/components.md](references/components.md) for the slide
frame, the components, colour roles and the animation rules. Arrows are the
most common defect: an arrowhead appears exactly when its line finishes, and
no arrow appears before both of its boxes. Each slide sits in an
`<!-- N Name -->` comment block so it can be found and edited alone.

## 4. Check, look, fix

```bash
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py check <deck>
python3 ~/.agents/skills/build-reveal-deck/scripts/deck.py steps <deck> <slide>
```

`check` shoots every slide after its last click and reports:

- titles wider than one line;
- text overflowing its box;
- anything off the slide or over the footer logos;
- missing arrowheads;
- boxes that vanish after leaving a slide and coming back;
- page errors and failed loads.

`steps` shoots one slide at every click, so you can see the animation order.

Open the screenshots and look at them. A clean report does not prove the
slides look right. Also click through the deck in a real browser: the T3
built-in browser, Chrome through its extension, or headless Playwright.
Never use the Orca app.

Loop until `check` exits 0 and the screenshots look right. Then have the
other vendor review the screenshots once. Stop any server you started.

## 5. Export when asked

`deck.py pdf <deck>` writes one page per slide, each in its final state.
`deck.py bundle <deck>` writes one self-contained HTML file.
[references/export.md](references/export.md) covers putting both on a Notion
page.

## Output

Report:

- the deck path;
- the slide list, one line each;
- the `check` result;
- what you verified by eye, and what you did not, such as a click-through in
  the user's own browser.

When a slide makes a claim about other tools or uses numbers, give the source
you checked it against.

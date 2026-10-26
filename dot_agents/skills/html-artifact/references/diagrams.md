# Diagrams

Describe the diagram as a short graph spec and let the bundled command lay it
out. Never place coordinates by hand: the layout engine (ELK) sizes every box
from its measured text, routes arrows at right angles, and keeps labels off
the strokes. The default output is one inline SVG drawn with the page's own
fonts and colour tokens, so it follows the theme toggle and prints without an
image pair.

## Run

Requires Bun 1.4.0 or newer. Run from the ignored artifact folder, beside the
HTML:

```bash
bun run ~/.agents/skills/html-artifact/scripts/diagram.ts arch.json arch
```

The first run downloads the locked packages, Chromium's headless shell and
the two measuring fonts (SN Pro and iA Writer Mono, the template's own
pins) into `~/.cache/html-artifact/diagram/`; later runs reuse them, and a
change to the bundled sources gets a fresh runtime. The run writes
`arch.diagram.html`; paste it inside a `<figure>` before the `<figcaption>`.
Keep the spec JSON beside the HTML; it is the source you edit and rerun.
The manifest in `scripts/diagram/` pins elkjs 0.10.2 and Playwright 1.63.0;
update them in a temporary workspace and copy back the manifest and
`bun.lock`, never by running `bun install` in the skill.

## Spec

```json
{
  "id": "arch",
  "title": "Who owns what",
  "alt": "A scientist uses the shell, which calls the engine through one contract.",
  "direction": "DOWN",
  "legend": [["host-owned", "blue"], ["engine-owned", "green"], ["the contract", "accent"]],
  "groups": [{"id": "host", "label": "HOST", "tone": "blue"}, {"id": "core", "label": "ENGINE", "tone": "green"}],
  "nodes": [
    {"id": "user", "title": "Scientist", "kind": "actor"},
    {"id": "shell", "group": "host", "title": "Shell", "detail": "board · decisions", "tone": "blue"},
    {"id": "api", "group": "core", "title": "Contract", "detail": "/api/v0", "tone": "accent", "mono": true},
    {"id": "engine", "group": "core", "title": "Engine", "detail": "orchestrator · reviews", "tone": "green"}
  ],
  "edges": [
    {"from": "user", "to": "shell", "label": "uses"},
    {"from": "shell", "to": "api", "label": "HTTP + SSE"},
    {"from": "api", "to": "engine", "label": "fronts"}
  ]
}
```

- `id`: a lowercase slug, unique on the page; it prefixes the SVG's ids.
- `alt`: the diagram in one or two sentences, read by screen readers.
- `nodes[]`: `id` (not starting with `group:`, which is reserved), `title`,
  optional one-line `detail`, `group`, `tone`,
  `kind: "actor"` for a person (pill shape), `style: "dashed"` for optional or
  future parts, `mono: true` for a title that is an identifier or path.
- `edges[]`: required, `[]` for no arrows; each has `from`, `to`, optional
  `label`, `style: "dashed"`.
- `groups[]`: zones such as owners, phases or processes, each with a short
  uppercase `label` and an optional `tone`.
- `legend`: `[text, tone]` pairs, or `"dashed"`. Add one whenever a tone or a
  dash carries meaning; the caption should not have to decode colours.
- Tones: `ink` (default), `blue`, `green`, `teal`, `peach`, `yellow`, `red`,
  and `accent` for the one node the reader must notice.

## Layout hints

- `direction`: `RIGHT` (default), `DOWN`, `LEFT` or `UP`. Use `DOWN` for
  anything with more than four steps in a row or with two or more zones; ELK's
  edge labels make left-to-right chains wide.
- `layout`: `layered` (default), `ring` for a cycle drawn as two rows, or
  `ring-v` for a cycle drawn as two columns. Use `ring-v` for a loop of six or
  more stages; its first half runs down the left, its second half up the right.
- Node and edge order in the spec is kept where the layout allows, so list
  nodes in reading order and put the main path's edges first.
- `nodeGap` and `layerGap` (numbers) widen or tighten spacing in the
  layered layout; rings size their own gaps from the labels.

## Budgets

These keep a diagram readable at the page's 860 to 1080px figure width.

- About 9 nodes. Above 12 the command warns; draw an overview plus one
  figure per part instead.
- One `accent` node. The command warns on more.
- Titles of one to three words; details of one line, about 32 characters.
  Edge labels of one to three words, or none when the arrow is obvious.
- Drawing width under about 1100 units. The command warns above that; switch
  to `DOWN`, to `ring-v`, or split the diagram.

## Limits

ELK chooses composition by layers and does not know editorial intent. Zones
it places one above the other cannot be pinned side by side: forcing them
into columns either doubles the drawing's width, because each arrow label
takes a layer, or drops the arrows that cross between zones. Reorder nodes,
change `direction`, or split the figure. Text is measured with SN Pro and iA
Writer Mono plus 6% slack, so an offline reader with neither face still sees
labels inside their boxes. Check the result in both themes after pasting it.

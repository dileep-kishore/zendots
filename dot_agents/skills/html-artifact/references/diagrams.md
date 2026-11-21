# Diagrams

Describe the diagram as a short JSON spec and let the bundled command lay it
out. A spec's `kind` picks the drawing: `graph` (the default, below) for parts
and flows, and the kinds after Limits for call sequences, swimlanes, layer
stacks and quadrants. Never place coordinates by hand: the layout engine (ELK) sizes every box
from its measured text, routes arrows at right angles, and keeps labels off
the strokes. The default output is one inline SVG drawn with the page's own
fonts and colour tokens, so it follows the theme toggle and prints without an
image pair.

## Run

Requires Bun 1.4.0 or newer. Run from the ignored artifact folder, beside the
HTML:

```bash
bun run <skill-dir>/scripts/diagram.ts arch.json arch
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

## Callouts and icons

Both work on every kind.

- `notes`: at most two callouts, each `{"target": "<id>", "text": "..."}`.
  A callout carries the one remark the reader should take from the drawing,
  in the italic of figure captions, joined to its target by a dashed leader.
  Keep it to about 80 characters; it wraps at 28 and may not pass three
  lines. The command puts it on the right of the target, else the left, else
  below, wherever a straight leader reaches the edge without crossing
  anything, and stops with an error when no side is clear. Target a node on
  the outside of the drawing. In a graph spec a node and its group may share
  an id, but a note cannot target such an id.
- `icon` on a node (or actor, step, layer): one of `user`, `users`, `robot`,
  `laptop`, `server`, `container`, `cloud`, `internet`, `database`, `file`,
  `log`, `queue`, `cache`, `search`, `api`, `lock`, `key`, `alert`,
  `git-branch`, `terminal`, `pipeline`, `monitoring` (Tabler Icons, MIT,
  licence in `scripts/diagram/ICONS-LICENSE`). An icon helps the reader tell
  a person from a service from a store; put one on every node of a kind or
  on none.

## Layout self-check

Before it writes a fragment, the command checks the laid-out drawing: no
diagonal connector, no text over other text or over a box it does not belong
to, no text across a line unless it sits on a backing (group headings,
message labels), and nothing outside the viewBox. For the newer kinds a
failure stops the export and lists each collision; change the spec (shorter
labels, another direction, fewer items) and rerun. For graph specs the same
findings print as `WARN` and the fragment is still written, so older specs
render as before. `scripts/diagram/geometry.ts` holds the rules.

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

## Sequence (`"kind": "sequence"`)

For who calls whom, in what order, and what comes back: a request path, an
auth handshake, a retry. Actors sit in a row; time runs down.

```json
{"id": "refresh", "kind": "sequence", "alt": "...",
 "actors": [{"id": "web", "title": "Browser", "icon": "laptop"}, {"id": "api", "title": "API"},
            {"id": "auth", "title": "Auth service", "icon": "key"}],
 "messages": [
   {"from": "web", "to": "api", "label": "GET /orders"},
   {"from": "api", "to": "web", "label": "401", "type": "return"},
   {"from": "web", "to": "auth", "label": "POST /refresh"},
   {"id": "token", "from": "auth", "to": "web", "label": "new token", "type": "return", "tone": "accent"}],
 "frames": [{"op": "opt", "guard": "token expired", "start": 1, "end": 3}]}
```

- `actors[]`: `id`, `title`, optional `detail`, `icon`, `tone`, drawn like
  graph nodes.
- `messages[]`: `from`, `to`, `label`, optional `id` (a note target), `tone`
  and `type`: `call` (solid, filled head; the default), `return` (dashed,
  filled head) or `async` (dashed, open head). `from` equal to `to` draws a
  self-message loop.
- `frames[]`: `op` (`opt`, `alt`, `loop`), `guard`, and `start` and `end`,
  0-based inclusive message indexes. An `alt` also takes `else`, the index of
  the first message after the divider (`start < else <= end`), and an
  optional `elseGuard`. Frames nest one level; partly overlapping frames, a
  third level, or an inner frame across an `else` divider are errors.
- Each label sits above its arrow beside the source lifeline, so a message
  that skips an actor never writes over the skipped lifeline. Columns widen
  to fit labels, self-loops and frame guards. Activation bars are not drawn.
- Budget: 6 actors and 16 messages; above that, split the exchange.

## Swimlane (`"kind": "swimlane"`)

For who does each step and where work changes hands: a release process, an
on-call escalation, a review loop. One lane per person, team or system.

```json
{"id": "ship", "kind": "swimlane", "alt": "...",
 "lanes": [{"id": "eng", "label": "Engineer"}, {"id": "rev", "label": "Reviewer"}],
 "steps": [{"id": "pr", "lane": "eng", "title": "Open PR", "icon": "git-branch"},
           {"id": "review", "lane": "rev", "title": "Review", "icon": "search"},
           {"id": "merge", "lane": "eng", "title": "Merge", "tone": "accent"}],
 "edges": [{"from": "pr", "to": "review"}, {"from": "review", "to": "merge", "label": "approved"},
           {"from": "review", "to": "pr", "label": "changes requested", "back": true}]}
```

- `lanes[]`: `id`, `label`, in reading order; a lane may be empty.
- `steps[]`: `id`, `lane`, `title`, optional `detail`, `tone`, `icon`,
  `style: "dashed"`.
- `edges[]`: `from`, `to`, optional `label`, `style: "dashed"`, and
  `back: true` for a step that sends work back. `[]` for none.
- `direction`: `RIGHT` (the default; lanes are rows) or `DOWN` (lanes are
  columns).
- Columns follow the longest path through the forward edges. Edges marked
  `back`, and any edge that closes a cycle (found walking `steps[]` in
  order), are return paths: dashed, and routed through a channel beyond the
  last lane (below for `RIGHT`, to the right for `DOWN`). Steps that share a
  lane and a column stack inside the lane.
- Budget: about 4 lanes and 8 steps; it warns above 5 lanes or 12 steps.
  Past about five columns `RIGHT` passes 1100 units; switch to `DOWN`.

## Layer stack (`"kind": "layers"`)

For a real hierarchy: a tech stack, abstraction levels, enforcement points, a
request path. When the parts are not stacked, use a graph or a swimlane.

```json
{"id": "stack", "kind": "layers", "alt": "...", "axis": "abstraction ↑",
 "layers": [
   {"id": "page", "tag": "L3", "title": "Page", "detail": "sections · prose", "icon": "file"},
   {"id": "runtime", "tag": "L2", "title": "Template runtime", "detail": "tokens · theme", "tone": "accent"},
   {"id": "fonts", "tag": "L1", "title": "Fonts", "detail": "SN Pro · iA Writer"}]}
```

- `layers[]`, top to bottom, 2 to 7 (fewer is an error, more warns). Each has
  a `title`, and optionally an `id` (a note target), a short `tag` drawn far
  left in mono, a `detail` drawn far right, a `tone`, and an `icon`.
- `accent` marks the one focal layer with a wash; any other tone colours only
  the band's outline, so the stack still reads as one hierarchy.
- `axis`: an arrow in the left margin, such as `"abstraction ↑"` or
  `"requests ↓"`; the trailing arrow sets its direction.
- Every band has the same width and height; long titles and details wrap, and
  all bands grow together.

## Quadrant (`"kind": "quadrant"`)

For where each option sits on two measured axes: impact against effort,
reach against frequency. Positions come from the data, never from layout.

```json
{"id": "backlog", "kind": "quadrant", "alt": "...",
 "axes": {"x": ["easy", "hard"], "y": ["minor", "major"]},
 "quadrants": ["quick wins", "big bets", "fill-ins", "money pits"],
 "items": [{"id": "signup", "title": "Fix signup bug", "x": 0.2, "y": 0.85, "tone": "accent"},
           {"id": "sso", "title": "SSO for teams", "x": 0.7, "y": 0.8}]}
```

- `axes`: one word for the low and the high end of each axis, drawn beyond
  the axis tips; never a phrase, an arrow glyph, or "high/low".
- `quadrants`: optional corner labels, top left, top right, bottom left,
  bottom right.
- `items[]`: `id`, a one-to-three-word `title`, `x` and `y` from 0 to 1 (0 is
  left and bottom), optional `tone`; `accent` marks the one item to act on.
  A value outside 0 to 1, exactly 0.5 (on an axis), or two items at one
  point are errors.
- Labels go right of their dot, else left; a crowded cluster stacks its labels
  in a column inside the quadrant, each joined to its dot by a hairline
  leader. The plot grows from 480 units up to 780 when labels need room, and
  the command stops and names the items when they still do not fit.
- Budget: about 9 items; it warns above 12. A note works best on an item
  near the left or right edge.

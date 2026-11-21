# Visuals

Choose the visual before writing the prose. A section gets one visual that
shows its point, or none when a sentence says it faster.

## Which visual

| The section answers | Use |
|---|---|
| How does the process or decision flow, or how do the parts connect? | Diagram from a graph spec ([diagrams.md](diagrams.md)) |
| Who calls whom, in what order? | Numbered table of calls, or a graph spec with numbered edge labels |
| When does each piece happen? | `.timeline` for a short list, duration lanes for measured times |
| Which states and transitions exist? | Diagram from a graph spec |
| How does a number vary across categories, time, or two measures? | Vega-Lite bar, line, scatter; heatmap for a matrix |
| How does the result respond to an input the reader can change? | Interactive figure, per [interactive.md](interactive.md) |
| Which exact values do several series take at a point the reader picks? | `viz.lineChart` interactive figure |
| What are the exact values, or more than about seven classes? | Table in `.table-wrap` |
| What are the two to four headline numbers? | `.tiles` |
| What share of a whole? | 10 by 10 dot grid (recipe below), or a tile when the share is the only number |
| How big is a total, and what makes it up? | One big number in a tile, its parts beside it |
| How do a few values compare? | Horizontal bars from zero, each labelled with its value |
| How big is the gap between two values? | Two bars and a labelled bracket over the gap (recipe below) |
| What mechanism do none of those express? | Stepper over inline SVG ([components.md](components.md)) |
| What exactly does the reader run or paste? | `<pre><code class="language-...">` |

Comparisons draw the difference, not one box per option. One value is a
sentence or a tile, never a chart.

When the reader filters or thresholds real rows and should watch counts, a
chart and a table follow, use a row widget
([interactive.md](interactive.md#row-widgets)).

Beyond figures, [components.md](components.md) covers tile deltas and
sparklines, status ledgers, evidence disclosures, diff views, steppers,
duration lanes and the list of open decisions, with a guide to when each helps.

## Figure and table markup

Every visual lives in a `<figure>`; the template frames it, stamps it, and
numbers the caption. Tables use `<figure class="table">` so the caption goes
above and the counter reads "Table". Figures already fill the content column.
Write captions to the three-part shape in
[writing.md](writing.md).

```html
<figure class="table">
  <figcaption><b>Per-stage latency over 30 runs.</b> Minutes; p50 and p95 over 30 nightly runs.</figcaption>
  <div class="table-wrap"><table>...</table></div>
  <p class="fn"><sup>a</sup> Footnote for a cell marked with the same letter.</p>
</figure>
```

Mark the one value or node the reader must notice with `class="hot"` (cells,
tile numbers) or `tone: "accent"` in a graph spec; never more than one
per figure.

## Code

```html
<pre><code class="language-python">def batches(records, size=64):
    for i in range(0, len(records), size):
        yield records[i:i + size]</code></pre>
```

Name the language on the `<code>`; highlight.js loads only when a block does,
and the colours come from the page tokens, so both themes work with no theme
sheet. Without the class a block renders as plain monospace, which is right for
console transcripts and output. Escape `<`, `>` and `&`, and keep the opening
tag tight against the first character or the block gains a blank first line.

## Diagrams

Write a graph spec and run the [diagram command](diagrams.md). Paste its
`.diagram.html` fragment, an inline SVG inside `<div class="diagram">`, before
the figure's caption. The SVG reads the page's colour tokens and fonts, so it
needs no light/dark pair. Keep the spec JSON beside the artifact.

## Mermaid, only when chosen by the user

For the hand-drawn alternative, set `look: handDrawn` and a fixed
`handDrawnSeed` in the diagram's frontmatter. Do not silently substitute a
classic Mermaid diagram if its diagram type does not support this look.

```html
<figure>
  <pre class="mermaid">
---
config:
  look: handDrawn
  handDrawnSeed: 42
---
flowchart LR
  A[Fetch] -->|raw pages| B[Parse]
  B -->|records| C[Embed]
  C -->|vectors| D[Publish]
  classDef hot fill:#cba6f733,stroke:#cba6f7;
  class C hot;
  </pre>
  <figcaption><b>Pipeline stages.</b> Boxes are stages, arrow labels the artefact passed on. Embedding is the only stage that waits on the model.</figcaption>
</figure>
```

- Label every arrow. Left-to-right under eight nodes with short labels;
  top-down otherwise, or whenever edge labels run long.
- Above 15 nodes draw an overview plus one figure per part.
- A line break inside a label is written `&lt;br/&gt;`; a literal `<br>`
  is parsed as HTML and vanishes.
- A subgraph ignores its own `direction` once one of its nodes links
  outside it; link subgraph to subgraph instead.
- `classDef` may set `fill` and `stroke`, using 8-digit hex tints so both
  themes work; never `color:`. The template themes everything else.
- No click callbacks; `securityLevel` is strict.

## Vega-Lite

```html
<figure>
  <div class="vega"><script type="application/json">
  {"$schema": "https://vega.github.io/schema/vega-lite/v6.json",
   "width": "container", "height": 260,
   "data": {"values": [{"model": "A", "f1": 0.81}, {"model": "B", "f1": 0.74}]},
   "encoding": {"x": {"field": "model", "type": "nominal", "title": null},
                "y": {"field": "f1", "type": "quantitative", "title": "F1"}},
   "layer": [{"mark": {"type": "bar", "tooltip": true}},
             {"mark": {"type": "text", "dy": -6}, "encoding": {"text": {"field": "f1", "format": ".2f"}}}]}
  </script></div>
  <figcaption><b>F1 by model on the held-out set.</b> Bars are macro F1 over 2,000 held-out documents, each labelled with its value. Model A leads by seven points.</figcaption>
</figure>
```

- One y axis, never two.
- Colour follows the entity: the same field maps to the same colour on every
  chart in the page. The template supplies the palette; specs carry no colours
  unless an entity demands one, or the figure focuses on one subject: then
  every mark is `var(--muted-foreground)` and the subject `var(--accent)`. To
  focus, fade the rest rather than add a colour.
- Legend for two or more series, direct labels for up to four, never a number
  on every point.
- Print the one to four values the takeaway rests on, as end labels, a text
  layer filtered to those marks, or a stat beside the chart. A screenshot, a
  printout and a phone have no hover; `tooltip: true` on marks adds detail.
- Lines go point to point: no `interpolate` smoothing on measured data, which
  draws values the data lacks. Log scales only with a labelled axis.
- Date-only values (`2026-11-10`) parse as UTC midnight: give their temporal
  field `"timeUnit": "utcyearmonthdate"`, or readers west of UTC see the day
  before.
- Altair: `chart.to_json()` drops in unchanged; delete any `"config"` Altair
  added so the page theme applies. Facets, log scales, shape legends and
  layered error bands are themed; give facets at least 240px each or set
  `labelAngle: -30` on the x axis, since the theme never drops category
  labels.

### Share and gap recipes

A share as a dot grid, 66 of 100 lit:

```json
{"width": 180, "height": 180,
 "data": {"sequence": {"start": 0, "stop": 100, "as": "i"}},
 "transform": [{"calculate": "datum.i % 10", "as": "col"}, {"calculate": "floor(datum.i / 10)", "as": "row"}],
 "mark": {"type": "circle", "size": 120},
 "encoding": {"x": {"field": "col", "type": "ordinal", "axis": null},
              "y": {"field": "row", "type": "ordinal", "axis": null},
              "color": {"condition": {"test": "datum.i < 66", "value": "var(--accent)"}, "value": "var(--muted-foreground)"}}}
```

A gap: two bars, and a dashed bracket from the smaller value to the larger
one, labelled with the difference:

```json
{"width": "container", "height": 120,
 "data": {"values": [{"run": "Before", "min": 31}, {"run": "After", "min": 9}]},
 "encoding": {"y": {"field": "run", "type": "nominal", "sort": null, "title": null}},
 "layer": [
  {"mark": {"type": "bar", "tooltip": true},
   "encoding": {"x": {"field": "min", "type": "quantitative", "title": "Minutes"},
                "color": {"condition": {"test": "datum.run == 'After'", "value": "var(--accent)"}, "value": "var(--muted-foreground)"}}},
  {"data": {"values": [{"run": "After", "from": 9, "to": 31, "mid": 20, "label": "31 to 9 min, −22"}]},
   "mark": {"type": "rule", "strokeDash": [4, 3]},
   "encoding": {"x": {"field": "from", "type": "quantitative"}, "x2": {"field": "to"}}},
  {"data": {"values": [{"run": "After", "mid": 20, "label": "31 to 9 min, −22"}]},
   "mark": {"type": "text", "dy": -10},
   "encoding": {"x": {"field": "mid", "type": "quantitative"}, "text": {"field": "label"}}}]}
```

### Chart recipes

Each was rendered in the template and its printed values compared with its
data. Change the data and labels, keep the transforms.

A **waterfall** bridges a start total to an end total through signed steps.
The running total comes from a window sum, so the end bar always equals the
start plus the steps; give the last row `"delta": 0`. The transforms name
the first and last rows `Start` and `End`; rename them there too. Totals are muted,
rises green, falls red, and every bar prints its value.

```json
{"width": "container", "height": 260,
 "data": {"values": [
   {"step": "Start", "delta": 42},
   {"step": "New hires", "delta": 9},
   {"step": "Transfers in", "delta": 3},
   {"step": "Attrition", "delta": -6},
   {"step": "Contract ends", "delta": -4},
   {"step": "End", "delta": 0}]},
 "transform": [
   {"window": [{"op": "sum", "field": "delta", "as": "to"}]},
   {"calculate": "datum.step === 'End' ? 0 : datum.to - datum.delta", "as": "from"},
   {"calculate": "datum.step === 'Start' ? 0 : datum.from", "as": "from"},
   {"calculate": "datum.step === 'Start' || datum.step === 'End' ? 'total' : datum.delta > 0 ? 'up' : 'down'", "as": "kind"},
   {"calculate": "datum.kind === 'total' ? format(datum.to, 'd') : (datum.delta > 0 ? '+' : '−') + format(abs(datum.delta), 'd')", "as": "label"},
   {"calculate": "max(datum.from, datum.to)", "as": "top"}],
 "encoding": {"x": {"field": "step", "type": "nominal", "sort": null, "title": null}},
 "layer": [
   {"mark": {"type": "bar", "tooltip": true},
    "encoding": {"y": {"field": "from", "type": "quantitative", "title": "Headcount"}, "y2": {"field": "to"},
                 "color": {"field": "kind", "type": "nominal", "legend": null,
                           "scale": {"domain": ["total", "up", "down"], "range": ["var(--muted-foreground)", "var(--green)", "var(--red)"]}}}},
   {"mark": {"type": "text", "dy": -7},
    "encoding": {"y": {"field": "top", "type": "quantitative"}, "text": {"field": "label"}}}]}
```

A **slopegraph** shows each entity's change between exactly two points. Print
both values, name each line at its right end, and colour only the subject.
Over about six lines, use a table. The right padding holds the end labels.

```json
{"width": "container", "padding": {"left": 5, "top": 10, "bottom": 5, "right": 110}, "height": 260,
 "data": {"values": [
   {"model": "Baseline", "split": "Validation", "f1": 0.71}, {"model": "Baseline", "split": "Held-out", "f1": 0.69},
   {"model": "Fine-tuned", "split": "Validation", "f1": 0.84}, {"model": "Fine-tuned", "split": "Held-out", "f1": 0.73},
   {"model": "Retrieval", "split": "Validation", "f1": 0.78}, {"model": "Retrieval", "split": "Held-out", "f1": 0.77}]},
 "encoding": {"x": {"field": "split", "type": "nominal", "sort": ["Validation", "Held-out"], "title": null, "scale": {"padding": 0.3}},
              "y": {"field": "f1", "type": "quantitative", "title": "F1", "scale": {"zero": false}},
              "detail": {"field": "model"},
              "color": {"condition": {"test": "datum.model == 'Fine-tuned'", "value": "var(--accent)"}, "value": "var(--muted-foreground)"}},
 "layer": [
   {"mark": {"type": "line", "point": true, "tooltip": true}},
   {"transform": [{"filter": "datum.split == 'Held-out'"}, {"calculate": "datum.model + ' ' + format(datum.f1, '.2f')", "as": "end"}],
    "mark": {"type": "text", "align": "left", "dx": 8}, "encoding": {"text": {"field": "end"}}},
   {"transform": [{"filter": "datum.split == 'Validation'"}],
    "mark": {"type": "text", "align": "right", "dx": -8}, "encoding": {"text": {"field": "f1", "format": ".2f"}}}]}
```

A **dumbbell** compares two values per category, such as before and after.
The rule spans the two, the later value is the accent, and only the later
values are printed.

```json
{"width": "container", "height": 180,
 "data": {"values": [
   {"stage": "Fetch", "run": "Before", "min": 12}, {"stage": "Fetch", "run": "After", "min": 11},
   {"stage": "Parse", "run": "Before", "min": 21}, {"stage": "Parse", "run": "After", "min": 6},
   {"stage": "Embed", "run": "Before", "min": 34}, {"stage": "Embed", "run": "After", "min": 29}]},
 "encoding": {"y": {"field": "stage", "type": "nominal", "sort": null, "title": null}},
 "layer": [
   {"mark": {"type": "rule", "color": "var(--muted-foreground)", "strokeWidth": 2},
    "encoding": {"x": {"aggregate": "min", "field": "min", "type": "quantitative", "title": "Minutes per run"}, "x2": {"aggregate": "max", "field": "min"}}},
   {"mark": {"type": "point", "filled": true, "size": 90, "tooltip": true},
    "encoding": {"x": {"field": "min", "type": "quantitative"},
                 "color": {"field": "run", "type": "nominal", "sort": ["Before", "After"], "title": null,
                           "scale": {"domain": ["Before", "After"], "range": ["var(--muted-foreground)", "var(--accent)"]}}}},
   {"transform": [{"filter": "datum.run == 'After'"}],
    "mark": {"type": "text", "dy": -12}, "encoding": {"x": {"field": "min", "type": "quantitative"}, "text": {"field": "min"}}}]}
```

A **box plot** shows a distribution per group: median, quartiles, whiskers
at 1.5 times the interquartile range, and outliers. Print the medians. With
fewer than about eight points per group, plot the points instead.

```json
{"width": "container", "height": 200,
 "data": {"values": [
   {"node": "A100", "s": 41}, {"node": "A100", "s": 44}, {"node": "A100", "s": 45}, {"node": "A100", "s": 47}, {"node": "A100", "s": 52}, {"node": "A100", "s": 70},
   {"node": "H100", "s": 22}, {"node": "H100", "s": 24}, {"node": "H100", "s": 25}, {"node": "H100", "s": 26}, {"node": "H100", "s": 29}, {"node": "H100", "s": 31}]},
 "encoding": {"y": {"field": "node", "type": "nominal", "title": null}},
 "layer": [
   {"mark": {"type": "boxplot", "extent": 1.5, "size": 22, "color": "var(--blue)",
             "median": {"color": "var(--ground)", "strokeWidth": 2}, "rule": {"color": "var(--muted-foreground)"},
             "ticks": false, "outliers": {"color": "var(--red)"}},
    "encoding": {"x": {"field": "s", "type": "quantitative", "title": "Seconds per step", "scale": {"zero": false}}}},
   {"transform": [{"aggregate": [{"op": "median", "field": "s", "as": "med"}], "groupby": ["node"]}],
    "mark": {"type": "text", "dy": -18}, "encoding": {"x": {"field": "med", "type": "quantitative"}, "text": {"field": "med", "format": ".1f"}}}]}
```

A **bump chart** shows rank movement across three or more snapshots. Ranks
come from a `row_number` window sorted by value with ties broken by name, so
equal scores never share a rank. Rank 1 is at the top; the end labels carry
the last value.

```json
{"width": "container", "padding": {"left": 5, "top": 10, "bottom": 5, "right": 110}, "height": 220,
 "data": {"values": [
   {"week": "W1", "team": "Atlas", "pts": 31}, {"week": "W1", "team": "Birch", "pts": 28}, {"week": "W1", "team": "Cove", "pts": 22}, {"week": "W1", "team": "Dune", "pts": 19},
   {"week": "W2", "team": "Atlas", "pts": 29}, {"week": "W2", "team": "Birch", "pts": 33}, {"week": "W2", "team": "Cove", "pts": 24}, {"week": "W2", "team": "Dune", "pts": 24},
   {"week": "W3", "team": "Atlas", "pts": 27}, {"week": "W3", "team": "Birch", "pts": 35}, {"week": "W3", "team": "Cove", "pts": 30}, {"week": "W3", "team": "Dune", "pts": 21}]},
 "transform": [{"window": [{"op": "row_number", "as": "rank"}], "sort": [{"field": "pts", "order": "descending"}, {"field": "team"}], "groupby": ["week"]}],
 "encoding": {"x": {"field": "week", "type": "ordinal", "title": null, "scale": {"padding": 0.3}},
              "y": {"field": "rank", "type": "ordinal", "title": "Rank", "scale": {"domain": [1, 2, 3, 4]}},
              "detail": {"field": "team"},
              "color": {"condition": {"test": "datum.team == 'Cove'", "value": "var(--accent)"}, "value": "var(--muted-foreground)"}},
 "layer": [
   {"mark": {"type": "line", "point": true, "tooltip": true}},
   {"transform": [{"filter": "datum.week == 'W3'"}, {"calculate": "datum.team + ' ' + datum.pts", "as": "end"}],
    "mark": {"type": "text", "align": "left", "dx": 8}, "encoding": {"text": {"field": "end"}}}]}
```

Recipe colours set the connector rules, box parts and medians explicitly,
because the page theme colours only plain marks. They use `var(--...)` tokens,
which the page resolves; a PNG or SVG saved from a chart's own export menu
loses those colours, so capture the page instead.

## Palette

Catppuccin: Mocha in dark mode, Latte in light, supplied by the template.

- Categorical, in this order, Mocha / Latte: blue `#89b4fa`/`#1e66f5`, peach
  `#fab387`/`#fe640b`, green `#a6e3a1`/`#40a02b`, yellow `#f9e2af`/`#df8e1d`,
  pink `#f5c2e7`/`#ea76cb`, teal `#94e2d5`/`#179299`, mauve `#cba6f7`/`#8839ef`,
  red `#f38ba8`/`#d20f39`. Scatter and maps use at most three.
- Accent (index numbers, stamps, the one `hot` value): mauve. Links: lavender.
- Every other hue has one job, so a page stays quiet even when several
  appear:
  - **Verdicts**: `.callout.good` with `data-label="Result"` (green),
    `.callout.warn` "Caution" (peach), `.callout.bad` "Risk" (red); the plain
    `.callout` "Note" stays lavender. At most one of each per page.
  - **Numbers**: `.n.good` or `td.good` for an improvement (green),
    `.bad` for a regression (red), `.hot` for the value to notice (mauve).
  - **Categories**: `<span class="tag blue|teal|peach|green|red|mauve">`
    for a short categorical label in a table; keep one colour per category
    across the page.
  - **State**: `.status.good|warn|bad` dots with a word, never colour alone.
  - **Gantt**: `done` renders muted, `active` mauve, `crit` red; add
    `todayMarker off` unless the schedule spans today.
  - **Mermaid classes**: `hot` (mauve) as above; add `classDef good
    fill:#a6e3a133,stroke:#a6e3a1` or `bad fill:#f38ba833,stroke:#f38ba8`
    when a node is a verdict.
- Sequential and diverging scales: build from one hue above (blue ramp;
  blue to red through the page's `--surface-2`), stated in the Vega spec.

## Inline SVG

These rules apply when incorporating an existing SVG asset. Author new
diagrams as a graph spec by default; its generated SVG styles marks with
`style="...var(--token)..."`, which follows the theme and is allowed.

```html
<figure>
  <svg viewBox="0 0 640 120" role="img" aria-label="Requests fan out to three workers and merge">
    <defs><marker id="m1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
    <g fill="none" stroke="currentColor" stroke-width="1.5" marker-end="url(#m1)">
      <path d="M120,60 H240"/>
    </g>
    <text x="40" y="65" font-size="13" fill="currentColor">client</text>
  </svg>
  <figcaption>Every request touches all three workers before merging.</figcaption>
</figure>
```

- Size by `viewBox` only; the template scales it.
- `currentColor` for lines and text; at most one literal hue, on the element
  that carries the meaning.
- Arrowheads as `<marker>`, ids unique per figure, 12 to 13px text, sentences
  in the caption not the drawing.
- `role="img"` and `aria-label` on the `<svg>`; no `<script>`, `<style>`, or
  `foreignObject` inside.

## Images

Prefer SVG exported from the source tool. PNG only when unavoidable, at most
300 KB each, as `<img src="data:image/png;base64,..." alt="..." width="...">`.
Never a screenshot of text.

## Printing

Graph-spec diagrams print with the page's light tokens. For Mermaid and Vega, switch
the page to light mode and wait for rendering before opening the print dialog.
Their marks retain their rendered palette in print. Print CSS keeps Vega labels
legible but cannot await asynchronous rerendering during the browser's print event.

# Visuals

Choose the visual before writing the prose. A section gets one visual that
shows its point, or none when a sentence says it faster.

## Which visual

| The section answers | Use |
|---|---|
| How does the process or decision flow? | Mermaid `flowchart` |
| Who calls whom, in what order? | Mermaid `sequenceDiagram` |
| When does each piece happen? | Mermaid `gantt`, or `.timeline` for a short list |
| Which states and transitions exist? | Mermaid `stateDiagram-v2` |
| How does a number vary across categories, time, or two measures? | Vega-Lite bar, line, scatter; heatmap for a matrix |
| What are the exact values, or more than about seven classes? | Table in `.table-wrap` |
| What are the two to four headline numbers? | `.tiles` |
| What mechanism do none of those express? | Inline SVG |
| What exactly does the reader run or paste? | `<pre><code class="language-...">` |

Comparisons draw the difference, not one box per option. One value is a
sentence or a tile, never a chart.

## Figure and table markup

Every visual lives in a `<figure>`; the template frames it, stamps it, and
numbers the caption. Tables use `<figure class="table">` so the caption goes
above and the counter reads "Table". Add `wide` to either when it needs the
full column. Write captions to the three-part shape in
[writing.md](writing.md).

```html
<figure class="table wide">
  <figcaption><b>Per-stage latency over 30 runs.</b> Minutes; p50 and p95 over 30 nightly runs.</figcaption>
  <div class="table-wrap"><table>...</table></div>
  <p class="fn"><sup>a</sup> Footnote for a cell marked with the same letter.</p>
</figure>
```

Mark the one value or node the reader must notice with `class="hot"` (cells,
tile numbers) or the Mermaid `hot` class below; never more than one per
figure.

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

## Mermaid

```html
<figure>
  <pre class="mermaid">
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
   "mark": {"type": "bar", "tooltip": true},
   "encoding": {"x": {"field": "model", "type": "nominal", "title": null},
                "y": {"field": "f1", "type": "quantitative", "title": "F1"}}}
  </script></div>
  <figcaption><b>F1 by model on the held-out set.</b> Bars are macro F1 over 2,000 held-out documents; hover for values. Model A leads by seven points.</figcaption>
</figure>
```

- One y axis, never two.
- Colour follows the entity: the same field maps to the same colour on every
  chart in the page. The template supplies the palette; specs carry no colours
  unless an entity demands one.
- Legend for two or more series, direct labels for up to four, never a number
  on every point.
- `tooltip: true` on marks. Log scales only with a labelled axis.
- Altair: `chart.to_json()` drops in unchanged; delete any `"config"` Altair
  added so the page theme applies. Facets, log scales, shape legends and
  layered error bands are themed; give facets at least 240px each or set
  `labelAngle: -30` on the x axis, since the theme never drops category
  labels.

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

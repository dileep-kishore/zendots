# Interactive figures

An interactive figure lets the reader change an input or inspect exact values
and watch the visual answer. Use one when the section's point is how a result
responds to something ("speedup flattens as the serial share grows"), or when
several series need exact values the reader picks. A static chart is better
when one view makes the point; never add controls for decoration.

The runtime lives in `assets/template.html` (`<style id="viz-css">` and
`<script id="viz-js">`). It reads the T3 / shadcn token names
(`--background`, `--foreground`, `--muted`, `--muted-foreground`, `--border`,
`--popover`, `--primary`, `--ring`, `--radius`, `--chart-1` to `--chart-6`,
`--font-sans`, `--font-mono`). The template maps them onto the house
Catppuccin tokens; T3 supplies its own live theme; a bare file falls back to
Catppuccin following the OS theme. One fragment therefore renders in all three.

## The fragment

One root `<div class="viz" id="...">` holding the controls, the visual, and
one `<script>`. Every id inside starts with the root id, so two figures never
collide. The script calls `viz.ready(function (d3) { ... })`, which waits for
the DOM and D3 7.9.0 from jsDelivr; select elements with
`document.getElementById`. Data is inline: no `fetch`, XHR, or WebSocket.

```html
<div class="viz" id="amdahl">
  <div class="viz-controls">
    <label class="viz-field"><span>Serial fraction <output id="amdahl-s-out">5%</output></span>
      <input id="amdahl-s" type="range" min="0.5" max="20" step="0.5" value="5"></label>
    <div class="viz-seg" id="amdahl-view" role="group" aria-label="Measure">
      <button type="button" value="speedup" aria-pressed="true">Speedup</button>
      <button type="button" value="efficiency" aria-pressed="false">Efficiency</button>
    </div>
  </div>
  <div class="viz-stats" aria-live="polite">
    <div class="viz-stat"><span class="k">Ceiling</span><span class="v" id="amdahl-ceiling"></span><span class="d">at any worker count</span></div>
  </div>
  <div id="amdahl-chart"></div>
  <script>
  viz.ready(function (d3) {
    var N = d3.range(1, 1025), sIn = document.getElementById('amdahl-s'), view = 'speedup';
    function spec() {
      var s = sIn.value / 100, speed = N.map(function (n) { return 1 / (s + (1 - s) / n); });
      return {
        label: 'Speedup against worker count by Amdahl’s law',
        x: { values: N, scale: 'log', base: 2, label: 'Workers', format: d3.format('d'), snap: true },
        y: view === 'speedup' ? { label: 'Speedup', format: function (d) { return d + '×'; }, min: 0, max: 1.06 / s }
                              : { label: 'Efficiency', format: d3.format('.0%'), min: 0, max: 1 },
        series: [{ name: 'Amdahl', values: view === 'speedup' ? speed : speed.map(function (v, i) { return v / N[i]; }) }],
        refs: view === 'speedup' ? [{ y: 1 / s, label: 'Ceiling 1/s' }] : []
      };
    }
    var chart = viz.lineChart('amdahl-chart', spec());
    function refresh() {
      chart.update(spec());
      document.getElementById('amdahl-s-out').textContent = sIn.value + '%';
      document.getElementById('amdahl-ceiling').textContent = d3.format('.1~f')(100 / sIn.value) + '×';
    }
    sIn.addEventListener('input', refresh);
    document.getElementById('amdahl-view').addEventListener('change', function (ev) { view = ev.detail.value; refresh(); });
    refresh();
  });
  </script>
</div>
```

In a page, the fragment sits inside a `<figure>` with its caption after it.
The caption's legend sentence says what to drag or hover.

## Runtime parts

| Class or call | Use |
|---|---|
| `.viz-controls` | Wrapping row of the controls that drive one visual |
| `label.viz-field` | Label and live `<output>` value above a native `<input type="range">` or `<select>` |
| `.viz-seg` with `button[aria-pressed]` | Single choice; fires `change` with `detail.value`; `aria-controls` on a button shows its panel and hides the others |
| `.viz-stats` > `.viz-stat` (`.k` label, `.v` value, `.d` context) | Up to three numbers that change with the inputs |
| `.viz-legend` with `span` children and `style="--c: var(--chart-N)"` | Static legend for a custom chart |
| `[data-tooltip]` on any element or SVG mark | Hover, focus, or tap shows the text; Escape hides it. Text that is not a control needs `tabindex="0"` to be reachable by keyboard |
| `<svg tabindex="0">` around `[data-tooltip]` marks | Arrow keys, Home and End step through the marks, show each tooltip and announce it |
| `viz.lineChart(id, spec)` | Multi-series lines on a shared x grid; returns `{ update(partialSpec) }` |
| `viz.ready(fn)` | Runs `fn(d3)`; a failure writes its message into the figure, or into every figure when D3 cannot load |

`viz.lineChart` spec: `x.values` (finite, strictly increasing), `x.scale`
(`'linear'` or `'log'` with `x.base`), `x.label`, `x.format`, `x.snap` (hover
snaps to samples, for counts); `y.label`, `y.format`, `y.min`, `y.max`,
`y.zero`; `series` (`name`, `values` the same length as `x.values`, optional
`dash`, `color`); `refs` (`{ y | x, label }` dotted reference lines);
`tipFormat`; `height` (default 300); `label` (the accessible name);
`endLabels` (default true: up to four visible series print their last
value at the line's end, so a screenshot keeps it; `false` turns them off).
Without `snap` the hover reads values between samples by interpolation, so
measured data sets `x.snap: true`, and only a model curve named in the
caption, such as the Amdahl example, reads continuously; its `x.format` must
round (`d3.format('.1f')`), or the tooltip prints every digit. It draws
axes, gridlines and titles, a legend that toggles series, one hover guide
with a marker and tooltip row per visible series at the cursor, touch
pinning, arrow-key stepping with a live announcement, and 450 ms transitions
on update that respect reduced motion. It rejects malformed data with an
error rather than guessing.

## Custom D3 visuals

When the line chart does not fit, draw with D3 inside the fragment and keep
the runtime's behaviour:

- Append into a `.viz-chart` element. Size the SVG from `el.clientWidth`
  with a matching `viewBox`, draw once synchronously, then redraw from a
  `ResizeObserver` when the width changes. Fix the height in pixels. When
  the width is 0 (a hidden panel), reset the remembered width so the chart
  redraws once shown.
- Colour marks with `style="fill: var(--chart-N)"` so they follow the theme
  live; never resolve a colour to hex. Keep one colour per entity across the
  page's figures.
- Use the `grid`, `axis x`, `axis y` and `axis-title` classes so axes match.
  Size the left margin from the widest y tick label as drawn
  (`getComputedTextLength()`), at least 64px; at widths under 480px use
  four ticks.
- Animate a redraw with `svg.transition().duration(450)` only when an input
  changed, and skip it under `prefers-reduced-motion`. Static draws set
  attributes directly: transitions wait for animation frames, which hidden
  tabs and headless capture never run. Before a static draw, interrupt the
  group and its descendants (`sel.interrupt().selectAll('*').interrupt()`),
  because a D3 axis animates its ticks, not the group.
- Put each mark's label, value and units in `data-tooltip`, and give the
  `<svg>` `tabindex="0"` so keyboard users can step through the marks.
- Clip marks to the plot area when values can leave the axis range.

## Composition

- The first render is the most useful state; the inputs explore from there.
- A takeaway beside an interactive figure holds for every state its controls
  allow, or says it describes the first state.
- Controls change the point the section makes. No search, filters, or reset
  buttons nobody asked for, and no stats that do not move with the inputs.
- Every visible label fits at 320px. Axis titles stay under about 30
  characters; the caption carries the rest.
- Numbers come from the source or a stated model. A simulation names its
  model in the caption or a neighbouring table.

## Row widgets

When the reader filters or thresholds real rows and should watch counts, a
chart and a table follow, declare a widget instead of writing a script. A
model whose output responds to an input (the Amdahl fragment above) needs
arithmetic, which a widget refuses; keep `viz.lineChart` or D3 for it.

Embed a data file through `scripts/rows.py`, never by converting cells by
hand. It applies the BERIL Workbench reader's rules: `""`, `NA`, `NaN`,
`nan`, `null` and `None` become `null`, numeric text becomes a number, and
a leading-zero id (`007`) or an integer past 2^53 stays a string.

```bash
python3 <skill-dir>/scripts/rows.py run.csv --columns genus,coverage,site --source-line "run r12" > rows.json
```

`--source-line` prints the widget's Sources entry on standard error, such as
`run.csv (run r12): 142 of 150 rows, columns genus, coverage, site`. A widget
over real data carries that entry in its `Sources` list. Its output escapes `<` as `\u003c`, so a cell holding `</script>` cannot end
the block early. When you assemble the block in a script, serialize it the
same way: `json.dumps(block).replace("<", "\\u003c")`.

```html
<div class="widget" id="cov"><script type="application/json">
{"state": {"min": 5, "site": null},
 "rows": {"genera": [{"genus": "Bacillus", "coverage": 9.5, "site": "A"}]},
 "where": {"pass": [{"field": "coverage", "op": ">=", "value": "$min"},
                    {"field": "site", "op": "==", "value": "$site"}]},
 "view": [
  {"Row": [{"Slider": {"label": "Minimum coverage", "min": 0, "max": 20, "step": 0.5, "value": "$min"}},
           {"Select": {"label": "Site", "options": [null, "A", "B"], "value": "$site"}}]},
  {"Row": [{"Stat": {"label": "Genera passing", "rows": "genera", "op": "count", "where": "pass"}},
           {"Stat": {"label": "Median coverage", "rows": "genera", "op": "median", "field": "coverage", "where": "pass"}}]},
  {"Chart": {"rows": "genera", "where": "pass", "params": {"cutoff": "$min"}, "spec": {"layer": [
    {"mark": "bar", "encoding": {"x": {"field": "coverage", "bin": true, "type": "quantitative"}, "y": {"aggregate": "count"}}},
    {"mark": "rule", "encoding": {"x": {"datum": {"expr": "cutoff"}, "type": "quantitative"}}}]}}},
  {"Table": {"rows": "genera", "where": "pass", "columns": ["genus", "coverage"], "sort": {"field": "coverage", "desc": true}}},
  {"Sources": ["runs/r12/genus_coverage.csv (run r12)"]}]}
</script></div>
```

| Part | Meaning |
|---|---|
| `state` | Every variable, by bare name. Any value that reads one is the whole string `"$name"` |
| `rows` | Named datasets, each a list of objects from `rows.py` |
| `where` | Named filter sets. A component's `where` is a set name, one `{field, op, value}`, or a list (all must hold). `op` is `>=` `>` `<=` `<` `==` `!=` `contains`. A row missing the field fails; a `null` or `""` value skips the condition, so a Select's `null` means "All" |
| `Row` | Its components side by side |
| `Slider` | `label`, `min`, `max`, `step`, `value: "$name"` |
| `Select` | `label`, `options` (strings, numbers, `null`, or `{value, label}`), `value: "$name"` |
| `Stat` | `label`, `rows`, `op`, optional `field` and `where`. `count` reads "7 of 12" against all rows; `missing` counts rows lacking `field`; `mean` `median` `min` `max` `sum` skip missing cells, show "—" when none remain, and add "n = N" |
| `Table` | `rows`, optional `columns`, `where`, `sort: {field, desc}`, `limit` (default 50). Headers re-sort; missing values stay last |
| `Chart` | `rows`, `spec` (Vega-Lite, drawing the passing rows as dataset `rows`), optional `where`, `params` (`{"cutoff": "$min"}` sets a spec param the marks read with `{"expr": "cutoff"}`) |
| `Sources` | A list of strings: each file by path and the run that wrote it |

There are no expressions: no arithmetic, functions or string templates. A
chart cannot load anything: `check.py` refuses a `url`, `data` or
`datasets` key and an image mark anywhere in its spec, and the runtime's
loader refuses every request. A widget that fails a check shows its errors
and its JSON instead of a partial view, and `check.py` reports the same
errors. Nothing in a widget sends anything back to the agent; the reader
explores, and asks in chat.

A BERIL Workbench chat widget does not paste in: its positional
`Slider("Minimum coverage", 0, 20, 0.5, $min)` becomes the named
`{"Slider": {"label": ..., "value": "$min"}}`, `$min = 5` becomes
`"state": {"min": 5}`, and `Query(...)` becomes rows embedded by `rows.py`.

## Inline in a T3 thread

When the reader should see the visual in the conversation rather than a file,
write the fragment alone (a `div.viz` figure or a `div.widget`) and wrap it:

```bash
python3 <skill-dir>/scripts/render.py fragment.html inline.html --title "Short name"
```

Preview `inline.html` with `html_preview` at width 728 in dark and 390 in
light, read its console output, then pass the same document to `html_render`
with the reported `contentHeight`. `--page` instead gives a standalone page
with its own background, margins, and the favicon of the repository the
output is written into.

## Check in a browser

`check.py` cannot run scripts. Open the page in a real browser at 320 or 390
px, about 736 px, and a desktop width, in both themes, and confirm:

1. No `.viz-error` message and no console error.
2. Every control changes the visual and its stats; the legend toggles
   series; hover shows one row per visible series; Home, arrow keys and
   Escape work on a focused chart, and step through the marks of a custom
   chart. For a widget, set each control to an edge value and read the
   Stat, Table and chart text against the rows by hand.
3. Nothing overflows or clips. `bun <skill-dir>/scripts/audit.ts <page>`
   lists errors, figures that drew nothing, clipped text and page overflow at
   390 and 1280 px in both themes, and exits 0 only when all four passes are
   clean.

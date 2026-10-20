# Components

A guide to the page components beyond prose, figures and tables. Treat it as
advice, not a rule: pick what shows the point fastest, and write a sentence
when a sentence does. Most pages need two or three of these, not all.

## Which one

| The reader wants to know | Reach for | Instead of |
|---|---|---|
| The two to four numbers that matter, and how they moved | `.tiles` with a delta, plus a sparkline when there is a real series | A paragraph of numbers |
| What changed in the code or config | Diff view from `scripts/diff.py` | Pasted snippets or a prose list of edits |
| What was planned and what became of each item | Status ledger | A checklist, a bullet list, or a status column |
| Why a claim holds, without wading through the proof | Evidence disclosure under the claim | Logs and tables inline |
| How the thing that was built works, step by step | Stepper over an inline SVG or HTML diagram | One crowded diagram, or several near-identical ones |
| When the work happened, what ran in parallel, where it waited | Duration lanes, from measured times | `.timeline`, which lists events without durations |
| A short sequence of dated events | `.timeline` | Lanes, when durations do not matter |
| What the reader must decide next | Decision form | A list of questions in prose |
| One verdict, caution, or risk | `.callout` | Bold text in a paragraph |
| How a result responds to an input | Interactive figure, per [interactive.md](interactive.md) | A table of scenarios |

A plan that is still open reads better as a table of decisions and a flow
diagram; these components lean toward pages that report finished work. The
"Work summary" shape in [writing.md](writing.md) puts them in order.

## Tile delta and sparkline

Use a delta when a tile's number has a real "before". Use a sparkline only for
a real series of five or more points; a two-point trend is a delta.

```html
<div class="tile"><div class="n">25.2</div><div class="k">minutes per run</div>
  <div class="d good">−21.9 from 47.1</div>
  <svg class="spark" data-values="47.1 46.8 47.4 31.0 25.2" aria-label="Run minutes, last five nights"></svg></div>
```

`good` or `bad` on `.d` colours the delta by meaning, not by sign. Always
write the comparison point ("from 47.1", "vs last week").

## Status ledger

Each planned item, its outcome, and a short reason. The runtime adds a count
and a proportion bar above the list. Statuses: `done`, `changed`, `dropped`,
`deferred`. Say why for every item that is not `done`.

```html
<ul class="ledger">
  <li data-status="done"><b>Diff view</b> rendered from the real diff by <code>diff.py</code>.</li>
  <li data-status="changed"><b>Checklist</b> became this ledger: a summary looks back.</li>
  <li data-status="deferred"><b>Maps</b> wait for a page with spatial data.</li>
</ul>
```

Skip it when everything planned was done as planned; say so in one sentence.

## Evidence disclosure

The claim stays on the page; the logs, findings or tables behind it open on
demand and always print expanded. The summary line states the claim and its
size ("9 findings, all fixed"), never "Details".

```html
<details class="evidence"><summary><b>All nine review findings were confirmed and fixed.</b> <span>Codex review, nine verifiers</span></summary>
  <div class="table-wrap"><table>...</table></div>
</details>
```

Keep anything the reader needs to accept the page's main claim outside the
disclosure. Code blocks, tables and figures all work inside it.

## Diff view

Render it from the real diff so the lines match the repository, and pin a
note only where a line needs a reason:

```bash
git diff BASE -- PATHS | python3 <skill-dir>/scripts/diff.py \
  --caption "<b>Changes to the checker.</b> Unified diff against main. Pins mark the two fixes." \
  --notes notes.json -o diff.html
```

`notes.json` maps `path:N` (new-side line) or `path:-N` (a deleted line's
old-side number) to the note; a note that matches no line stops the script.
Paste the output where the figure belongs. Above about 300 changed lines,
show the files that carry the point and list the rest in a table.

## Stepper

For explaining a mechanism one stage at a time. It opens on the complete
diagram, so the first view is still the whole picture, and prints every step.
The diagram must be inline SVG or HTML: mark each part with the steps it
belongs to (`data-step="2"` or `data-step="2 3"`), and give one caption per
step. An Excalidraw export is an image and cannot step; use separate figures
for its states instead.

```html
<figure class="stepper">
  <svg viewBox="0 0 640 80" role="img" aria-label="...">
    <g data-step="1">...</g><g data-step="2">...</g><g data-step="2 3">...</g>
  </svg>
  <ol class="step-captions"><li>...</li><li>...</li><li>...</li></ol>
  <figcaption><b>...</b> ...</figcaption>
</figure>
```

Three to six steps. Skip it for a sequence that a numbered list already
explains.

## Duration lanes

When durations, overlap, or waiting are the point: parallel agents, a build
pipeline, a long run. Use only measured times (timestamps from git, logs or
session records, or measured durations laid end to end), never estimates;
when you have only an order of events, use `.timeline`.

```html
<figure>
  <div class="lanes" aria-label="Review run by agent"><script type="application/json">
  {"lanes": [
    {"name": "Codex review", "spans": [{"start": "2026-10-20T20:10:05Z", "end": "2026-10-20T20:31:40Z", "label": "Find"}]},
    {"name": "Verifiers", "spans": [{"start": "2026-10-20T20:31:40Z", "end": "2026-10-20T20:34:30Z", "wait": true, "label": "Queued"}]}
  ]}
  </script></div>
  <figcaption><b>...</b> ...</figcaption>
</figure>
```

Times are ISO strings or plain numbers (then set `"unit"`). `"wait": true`
draws a hatched waiting span. Each lane takes the next chart colour; hover,
or focus the timeline and use the arrow keys, for a span's times.

## Decision form

For the decisions that wait on the reader, typically the last section. Each
question is a `fieldset` with a `legend` and radio options; mark the
recommended one with `data-rec`. The runtime adds a one-line answer and a
"Copy as prompt" button, so the reader pastes their choices back to the
agent.

```html
<form class="decide" data-prompt="Decisions on the interactive-figure work">
  <fieldset><legend>Keep the new skill version?</legend>
    <label><input type="radio" name="keep" value="keep and sync" checked data-rec>Keep and sync</label>
    <label><input type="radio" name="keep" value="revert">Revert</label>
  </fieldset>
  <textarea name="note" rows="2" aria-label="Anything else" placeholder="Anything else"></textarea>
</form>
```

One question per decision, two to four options each, the recommendation
checked by default. A decision with no real alternative is a statement, not
a question.

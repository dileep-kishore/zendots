# Story pages

Read this only when the ask is to tell one finding as a story ("walk me
through why the run got faster"). A page with several findings stays a
Results page.

## Shape

- A lead that states the finding with its one number.
- One scroll stepper of three to five chapters. Each chapter is a short
  claim headline in `<b>` and one or two sentences.
- "What to do next", then the sources.

Each chapter lights the part of one figure it talks about. Pick that figure
by the idea, as the "Which visual" rows in [visuals.md](visuals.md) say: a
dot grid for a share, two bars and a bracket for a gap, bars from zero for a
comparison. Marks start muted, and the subject of the chapter is lit.

## The story block

Copy `<style id="story-css">` and `<script id="story-js">` from
`assets/story.html` into the page, directly after `viz-js`. Plain pages
never carry it. `check.py` errors when a page uses a story feature without
the block, or carries the block with a `viz-js` older than the story hooks.
To turn an older page into a story, replace its copied `viz-css` and
`viz-js` from the template first; this is the one exception to leaving a
page's copied runtime alone.

`render.py` does not copy the block: a story is a standalone page. In a T3
inline frame, below 720 px, and in print, a scroll stepper falls back to the
button stepper, and print shows every chapter undimmed.

## Scroll stepper over a drawing

The [stepper](components.md#stepper) markup, with `scroll` added. At 720 px
and wider, in a page that scrolls itself, the chapters scroll beside the
drawing, which stays in view; the chapter crossing a band 40% down the
screen is the current step.

```html
<figure class="stepper scroll">
  <svg viewBox="0 0 640 120" role="img" aria-label="...">
    <g data-step="1">...</g><g data-step="2">...</g><g data-step="2 3">...</g>
  </svg>
  <ol class="step-captions">
    <li><b>Embedding dominates.</b> It takes 31 of the run's 47 minutes.</li>
    <li><b>Batching cuts it.</b> 64 records per call bring it to 9 minutes.</li>
    <li><b>The run halves.</b> 25 minutes end to end.</li>
  </ol>
  <figcaption><b>...</b> ...</figcaption>
</figure>
```

## Chapters that drive a chart

A stepper, scroll or button, may hold a `.vega` figure in place of SVG
parts. Each step change sets the chart's `step` signal to the step number,
0 meaning all steps. The spec declares the param and its rows carry the
steps they belong to:

```json
{"params": [{"name": "step", "value": 0}, {"name": "ref", "value": ""}],
 "data": {"values": [
   {"stage": "Embed", "min": 31, "steps": "1 2", "ref": "embed"},
   {"stage": "Other", "min": 16, "steps": "3", "ref": "other"}]},
 "mark": {"type": "bar", "tooltip": true},
 "encoding": {
   "y": {"field": "stage", "type": "nominal", "sort": null, "title": null},
   "x": {"field": "min", "type": "quantitative", "title": "Minutes"},
   "opacity": {"condition": {"test": "(step == 0 || indexof(split(datum.steps, ' '), toString(step)) >= 0) && (ref == '' || datum.ref == ref)", "value": 1}, "value": 0.25}}}
```

## Linked highlights

A phrase in the prose or a caption names the marks it is about:

```html
<p>Most of the gain comes from <mark class="ref" data-ref="embed">the embed stage</mark>.</p>
```

Hovering, focusing or tapping it lights the matching marks and dims the
rest of their figure; leaving, blur, a second tap or Escape clears it. Mark
inline SVG or HTML targets with the same `data-ref`. For a Vega chart, give
its rows a `ref` field and declare the `ref` param, as above; a chart
without the param, or without a matching row, is never touched.
`check.py` warns when a phrase names a value no figure carries.

## Check

Run `check.py` and the audit as for any page. Then open the page at a
desktop width in T3 preview, scroll through every chapter, and confirm each
one lights its part, the drawing stays in view, and the spacing reads well.

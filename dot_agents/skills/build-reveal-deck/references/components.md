# Slide frame, components and animation

The slide is 1600x900 and reveal scales it to the window. Most layouts place
elements with absolute positions inside `.stage`. The stage is 1440x588, or
1440x650 with `.stage.tall`. Copy markup from the starter slides rather than
writing it from scratch.

## Frame

```html
<!-- 4 Short name -->
<section>
  <div class="kicker">Section label</div>
  <h2>Title that states the point</h2>
  ...the slide's content: a .stage visual, .bullets, .prose or a table...
</section>
```

- `h2` stays on one line, and `check` flags a title that runs past one line.
  As a rough limit, keep it to about 55 characters in the KBase theme and
  about 48 in the default theme.
- `.takeaway` is an optional bullet list fixed 52px above the bottom of the
  slide, for the one line to remember under a visual. Use as many items as
  fit, or none.
- `.source` is a small grey line that names the source of a number. Place it
  with inline `left` and `bottom`.
- In the KBase theme, keep text clear of the logos at the bottom right.
  `check` flags any overlap.

## Text slides

- `ul.bullets` is a list placed under the title. Nested `ul` items render
  smaller and muted. Add `fragment rise` to items that should appear one
  click at a time.
- `.prose` holds paragraphs, for a slide that is plain text.
- `table.data` is a simple table. Put it inside `.stage` or a `.box`.

When a list grows past the bottom of the slide, split it across two slides or
cut words. Shrinking the font is the last resort. `check` reports content that
runs off the slide.

## Components for visuals (base.css)

- `.box` is a card. It holds an `h4`, a `p`, a `.tag` chip and an optional
  `.big` number. Give it a colour role (below), and set its position and size
  inline.
- `.box.krow` is a row with a big number on the left and text on the right.
- `.lim` is a comparison row. `.bad` sits on the left and `.good` on the
  right, joined by `svg.arrow`. `.colhead` labels the two columns.
- `.col` is a tall column. `.lane-label` is an uppercase label above a row of
  boxes.
- `.window` and `.term` mock an app window and a terminal. `.callout` is a
  labelled note.
- `.hero` is the preview area on the title slide.

The theme supplies six colour roles: `c-accent`, `c-alt`, `c-blue`,
`c-green`, `c-orange` and `c-red`. In CSS and SVG, use the matching variables,
such as `var(--accent)` or `var(--green-soft)`. Keep one meaning per colour
within a deck.

Styles that only one deck needs go in its `deck.css`. Change `base.css` only to
fix something every deck needs, and copy that fix back into the skill.

## Animation

- `.enter` with `.d1` to `.d6` staggers elements in when the slide opens.
- `.fragment.rise` and `.fragment.pop` build on click. Set
  `data-fragment-index` when several elements should appear together.
- `.fragment.draw` on an SVG `<g>` or `<svg>` draws its lines on click. Put
  `data-marker="<marker id>"` on each path, never `marker-end`. `deck.js`
  measures each line and attaches the arrowhead the moment the line finishes
  drawing.
- An arrow must not appear before the boxes at both of its ends. Give the
  arrow the same fragment index as the box it points to, or a later one.
- Place labels on arrows beside the line, not on it. Give SVG text a
  `paint-order: stroke` halo in the background colour.
- Use `data-auto-animate` only between two slides with matching `data-id`
  elements. Then go forward and come back, and confirm both slides still show
  every box. `check` tests this.
- `.flow` adds moving dashes to an arrow that is always shown. Use it
  sparingly.

## Readability

- Text is at least 18px on the 1600px slide. Body text in boxes is 19 to
  20px, box headings are 24 to 26px, and text-slide bullets are 32px.
- Leave at least 20px between boxes, and 24px between a box and the edge of
  the stage.

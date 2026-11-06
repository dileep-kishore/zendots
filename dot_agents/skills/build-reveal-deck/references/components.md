# Slide frame, components and animation

The slide is 1600x900 and reveal scales it to the window. Lay out everything
with absolute positions inside `.stage`, which is 1440x588 by default and
1440x650 with `.stage.tall`. Copy markup from the starter slides in
`index.html` rather than writing it from scratch.

## Frame

```html
<!-- 4 Short name -->
<section>
  <div class="kicker">Section label</div>
  <h2>One-line claim</h2>
  <div class="stage"> ...one visual... </div>
  <ul class="takeaway fragment rise"><li>One sentence to remember.</li></ul>
</section>
```

- `h2` never wraps. It stays on one line, and `check` flags one that runs
  past the slide. Shorten it to about 55 characters in the KBase theme and
  about 48 in the default.
- `.takeaway` sits 52px above the bottom. In the KBase theme, keep its text
  clear of the logos at the bottom right; `check` flags a collision.
- `.source` is a small grey line for the source of a number; place it with
  inline `left` and `bottom`.

## Components (base.css)

- `.box` is a card. Add `h4`, `p`, a `.tag` chip and an optional `.big`
  number. Give it a colour role (below), and position and size it inline.
- `.box.krow` is a row with a big number on the left and text on the right.
- `.lim` is a gaps-to-plan row. `.bad` sits on the left, `.good` on the
  right, and `svg.arrow` joins them. `.colhead` labels the columns.
- `.col` is a tall summary column. `.lane-label` is an uppercase label above
  a row of boxes.
- `.window` and `.term` mock an app window and a terminal for product
  previews. `.callout` is a labelled note.
- `.hero` is the preview area on the title slide.

Colour roles come from the theme. They are `c-accent`, `c-alt`, `c-blue`,
`c-green`, `c-orange` and `c-red`. In CSS and SVG, use the matching
variables: `var(--accent)`, `var(--green-soft)` and so on. Keep one meaning
per colour within a deck. For example, red means a gap, green means the fix,
and the accent means the proposal.

Styles that only this deck needs go in `deck.css`. Change `base.css` only to
fix something every deck needs, and copy that fix back into the skill.

## Animation

- `.enter` with `.d1` to `.d6` staggers elements in when the slide opens.
- `.fragment.rise` and `.fragment.pop` build on click. Set
  `data-fragment-index` whenever several elements should appear together.
- `.fragment.draw` on an SVG `<g>` or `<svg>` draws its lines on click. Put
  `data-marker="<marker id>"` on each path, never `marker-end`. `deck.js`
  measures each line and attaches the arrowhead the moment the line finishes
  drawing.
- An arrow must not appear before the boxes at both of its ends. Give the
  arrow the same fragment index as the box it points to, or a later one. When
  a box and an arrow appear together, the box pops while the line draws.
- Put labels on arrows beside the line, not on it. Give SVG text a
  `paint-order: stroke` halo in the background colour.
- Use `data-auto-animate` only between two slides with matching `data-id`
  elements. Then check that both slides still show every box after you go
  forward and come back; `check` tests this.
- `.flow` adds moving dashes to an always-visible arrow. Use it sparingly.

## Size limits

- Text at least 18px. Box text 19 to 20px, headings 24 to 26px.
- At most about 25 words in a box. When text overflows, shorten it before
  shrinking the font.
- Leave at least 20px between boxes and 24px between a box and the stage edge.

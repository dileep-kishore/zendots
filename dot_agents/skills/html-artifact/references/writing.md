# Writing

## Length

The page answers the ask and stops. A plan review fits on two screens, a
results report on three, a "one screen" request on one; a screen is
1400x900 with no scrolling. Every paragraph earns its place by saying
something the visual beside it cannot.

## Sentences

- One idea per sentence, about 20 words, active voice, plain words.
- Headings name the claim ("Windows cap the input length"), not the topic
  ("Windows"). No "Overview" or "Introduction". The fixed parts "Not doing"
  and "Next" keep those names. Give a long claim a short TOC label with
  `data-toc="..."` on the heading.
- The meta line is `date · sources (files, datasets, or people) · author or
  purpose`.
- No bold-label lists, no emoji, no headings that are questions.
- Numbers in tiles or tables, not in running prose, unless one number is the
  point of the sentence.

## Captions read like a manuscript's

The template numbers every figure and table and prints the "Figure 1." or
"Table 1." label; never type the number yourself. Figure captions sit below
the figure, table captions above the table. A caption has three parts, in
this order, as one paragraph:

1. **Title sentence**, in `<b>`: what is shown, as a noun phrase ending in a
   full stop ("Minutes per stage, median and 95th percentile.").
2. **Legend**: what the marks, colours, axes, boxes, or columns encode, the
   units, and the data: sample size, source, date range, statistic
   ("Bars show p50 (blue) and p95 (orange) minutes over 30 nightly runs,
   2026-08-07 to 2026-09-05.").
3. **Takeaway**: the one thing the reader should notice.

Never invent a number, date, source, or sample size to complete a caption.
When it is not in the material, write a visible placeholder such as
`[n = ?]` or `[source?]` and say so in the reply; the reader can fill it,
but cannot detect a plausible fabrication.

Tables add footnotes for abbreviations or caveats: a superscript letter in
the cell and a `<p class="fn">` line inside the figure. Cite figures in prose
by their number ("Figure 2 shows ...") since the numbers are stable.

## Opinions end with a recommendation

A comparison closes with the choice and one reason. A plan carries a
`.not-doing` list of what was ruled out.

## Section shapes

- **Plan:** lead, decisions table, flow diagram, timeline, not doing.
- **Workflow:** lead, flowchart, per-stage table, failure modes.
- **Results:** lead, tiles, one chart per question, full table,
  findings, next.
- **Comparison:** lead, criteria table, one chart if the criteria are numeric,
  recommendation.

Drop any part the ask does not need.

## Voice check

Apply the `unslop` rules while drafting. Run the `humanizer` skill over the
finished prose before the checker.

## Publishing from Claude Code, on request only

The Artifact tool wraps a page in its own document skeleton. Give it a copy
with everything from `<!doctype html>` through `<body>` removed and the
closing `</body></html>` removed, keeping `<title>`, `<style>` (the
`@font-face` rules included), the markup, and the `<script>`. Leave the
file in the project unchanged. Report the path and the link. The Artifact
host allows fonts only from 'self', data: and gstatic, so a published copy
drops the jsDelivr faces and falls back to the system stack. The local file
keeps SN Pro and iA Writer Duo, from an installed copy when the machine has
one and from jsDelivr otherwise.

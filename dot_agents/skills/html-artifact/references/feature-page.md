# Feature page

The one page the user reads for a feature, instead of its spec and plan. Write
it once the spec has passed design review, before planning, and update the
same page in place after the build. Its job is the design and architecture
at a glance: what the feature is, how it works, what was decided and by whom,
and how anyone will know it is done.

Put it at `docs/superpowers/<feature>/<feature>.html`, git-ignored, or in the
project's established ignored artifact folder, with its diagram specs beside
it. Link the spec and plan by path in the meta line; never copy them in.

## Core sections, always in this order

The `id`s and short TOC labels are fixed, so every feature page reads the same
way. Headings stay claims about this feature, per [writing.md](writing.md).

| # | `id` and `data-toc` | Content | Visual |
|---|---|---|---|
| 0 | header | Title is the feature's name. Meta line: `date · Design \| In build \| Built · spec path`. Lead: what it does, for whom, and why now, in three sentences | `.tiles`: stage, done checks passing (`n of m`), open decisions, spec changes since approval |
| 1 | `how` "How it works" | The architecture, or for science and algorithm work the data and algorithm flow. Two or three sentences only | A graph-spec diagram ([diagrams.md](diagrams.md)), required, the first figure on the page |
| 2 | `decisions` "Key decisions" | The choices that shape the build: decision, chosen option, the alternative rejected, why, and who chose it | Table; `who` is a tag: `you` (blue), `agent default` (peach), `review` (mauve). Undiscussed agent defaults come first. At most 8 rows; the rest go in an evidence disclosure |
| 3 | `done` "Done checks" | The spec's done checks: check, kind (known answer, reference, property, real-data run, degenerate input, or app run from empty state), the command, status, evidence | Table with `.status` dots: `planned`, `pass` (good), `fail` (bad); evidence names the revision checked |
| 4 | `risks` "Risks and review" | The design review's verdict in one line, then the two or three risks that matter, each with its mitigation | One `.callout`; full review findings in an evidence disclosure |
| 5 | `not-doing` "Not doing" | What is out of scope, and why when it is not obvious | `.not-doing` list |
| 6 | `decide` "Waiting on you" | Only what needs the user's call | Decision form ([components.md](components.md)), or one sentence: "Nothing waits on you." |

After the build, add section 7. It sits between Done checks and Risks and
review, beside the results it explains, so the decision form stays last:

| # | `id` and `data-toc` | Content | Visual |
|---|---|---|---|
| 7 | `changes` "What changed from the design" | Each spec amendment made during planning and the build, with its reason; corrections to a done check or to the user's requests first | Status ledger (`done`, `changed`, `dropped`, `deferred`) |

## Optional sections

Add one only when the feature needs it, placed after the core section it
supports: a UI mockup after How it works; one results chart per question for
science work after Done checks; interfaces or data shapes as a code block in
an evidence disclosure under Decisions; duration lanes after What changed when
measured times exist.

## Detail

The core fits about three screens at 1400x900. Everything that supports a
claim without being the claim (interfaces, file lists, full review findings,
raw check output) goes in `details.evidence` blocks. Numbers go in tiles and
tables, not prose. A section with nothing to say keeps its heading and one
sentence saying so; it is never padded.

## Updating after the build

Edit `<main>` in place. Change the stage in the meta line and the tiles, fill
each done check's status and evidence with the revision checked, add What
changed, and refresh Risks and Waiting on you. Do this after the last review
fixes and before any workspace cleanup deletes the ledger the amendments came
from.

[`assets/feature-example.html`](../assets/feature-example.html) is a complete
page at the Built stage.

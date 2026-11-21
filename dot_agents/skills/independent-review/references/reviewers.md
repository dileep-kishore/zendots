# Reviewers, tiers, and launch routes

## Roster

Ranked. A seat goes to the highest-ranked reviewer whose model family did not
write the change. Model IDs age: take the newest flagship of each family from
`orchestrator_capabilities` or the CLI's model list, and update this table
when one is replaced. Gemini 4 Neon replaced Carbon in the council seat on
19 November 2026, after the PR #97 replay below, and Carbon left the roster.
On 20 November 2026 the user moved Neon ahead of Argon into the tier 2 seat.
Neon reviews about as well as Claude Opus, and sometimes better. Its
Antigravity allocation is smaller than the Claude and OpenAI allocations, so
it ranks below them. Argon stays only as Neon's tier 3 fallback. Use Neon at
high: the LBL enterprise Gemini project rejects `xhigh` with HTTP 400 through
`agy`, though T3 lists it.

| Rank | Reviewer | Family | Seats |
|---|---|---|---|
| 1 | GPT-6.2 Sol, high effort | OpenAI | tiers 1-3 when Codex did not write the change; verifier |
| 1 | Claude Opus 5.5, high effort | Anthropic | tiers 1-3 when Codex wrote the change; verifier |
| 2 | Gemini 4 Neon, high thinking, through Antigravity | Google | tiers 2-3 |
| 3 | Grok 4.7, high effort, through Cursor | xAI | tier 3; Neon's fallback in tier 2 |
| - | Gemini 4 Argon, high thinking, through Antigravity | Google | Neon's fallback in tier 3 |
| - | Claude Sonnet 5.5, high effort | Anthropic | extra tier 2 seat when Claude wrote the change |

Rank 1 goes to the frontier model from the other family than the one that
wrote the change: Sol when Claude wrote it, Claude Opus when Codex wrote it.
When neither wrote it, Sol takes rank 1 and Claude Opus serves only as a
verifier.

Sonnet shares the author's family when Claude wrote the change, so it adds a
seat and never fills a cross-family one. The user chose it for tier 2 on 12
November 2026 after it found 3 of 5 real bugs in 10 minutes with no false
findings; its calibration rows decide whether it keeps the seat.

## Tiers

- **Tier 1:** the first eligible reviewer.
- **Tier 2:** the first two eligible reviewers, plus Claude Sonnet when
  Claude wrote the change.
- **Tier 3 (council):** the first three eligible reviewers.

A seat whose reviewer is unavailable goes to the next eligible reviewer.
Grok fills a tier 2 seat only as Neon's fallback, and Argon fills a tier 3
seat only as Neon's fallback, under Gemini finders below. With no eligible substitute, leave the seat empty and label the
review partial. Say which seat moved or stayed empty, and why.

## Verifiers

Verifiers settle findings, so they are Claude Opus or Sol only: whichever of
the two is not the finding reviewer's family, as a fresh native subagent
when it is the coordinator's own family. A Sonnet finding goes to Sol. When
Sol and Sonnet both raise one failure, no verifier is outside both families:
verify the two write-ups separately before merging, Sol's with Opus and
Sonnet's with Sol, and give the merged finding the stronger verdict
(CONFIRMED, then PLAUSIBLE, then UNVERIFIED, then REFUTED). When one write-up
is CONFIRMED and the other REFUTED, the merged finding is PLAUSIBLE: report
both verdicts, and settle it at triage only with code evidence. Never use Neon, Argon, or Grok as
verifiers until the calibration log shows they settle findings reliably.

## Gemini finders

Inside T3, launch Gemini finders with `delegate_task` like the other
finders. Use the `agy` CLI outside T3, or when `orchestrator_capabilities`
marks Antigravity unable to run child tasks or lacks the model. The default
listing shows at most eight models per provider, so call it with
`search: "gemini-4"` before deciding a model is missing. When T3 lacks a
model that `agy models` lists, launch it through `agy` and tell the user
that **Refresh provider status** in T3's provider settings would add it.

T3's bundled Antigravity server was 1.4.5 until 20 November 2026, and that
route failed often: 12 of 76 T3 Gemini runs hit `502 "The model is currently
unreachable"`, each costing 5.1 minutes, while no direct `agy` run hit it.
T3 then installed runtime 1.5.13
(`~/.t3/tools/antigravity-acp/*/versions/*/.install-complete.json`). The
same day, Neon high ran the PR #97 replay brief through T3 on both hosts
with no 502: 11.1 minutes and 13 findings on the macbook, 9.0 minutes and 11
findings on the macmini. The same brief through `agy` took 10.7 minutes on
the macbook and 9.0 on the macmini. Two clean runs are thin against a 16%
failure rate: when a T3 Gemini
run hits a 502, say so in the report's coverage with the run's elapsed time,
and propose moving Gemini back to `agy` for the user's approval.

Every Gemini finder gets the bundle and rules in the
[reading budget](reading-budget.md), and a deadline from launch: 20 minutes
for Argon and Neon. Most of their time is a few long thinking turns
that print nothing, so through `agy` judge progress by the event stream, not
by silence. Fall back at once when a T3 task fails or its report lacks the
completion token, or, through `agy`, when the stream shows an `ERROR` step
or "unreachable", when the result's `response` is empty, or when it lists
`denied_actions`.

Only `agy` enforces the deadline, through `--print-timeout`. An async T3
task wakes the coordinator only when it ends, and T3 ends an Antigravity
task after 15 minutes without activity, not at a wall-clock limit. Through
T3, treat a Gemini task that ends without a report as having missed its
deadline. When another finder's completion wakes the coordinator after a
Gemini task's 20 minutes have passed, cancel that task with `task_cancel` and
fall back as below.

In tier 2, at Neon's deadline, stop it and
launch Grok 4.7 high fast with the same brief, minus the reading budget, into
that seat. Do the same at once when Neon is unavailable or its launch fails.
Grok gets its own 20-minute deadline; if it misses that too, label the seat
partial.

In tier 3, at Neon's deadline, stop it and launch Argon with the same
brief and a reading budget rendered for Argon's own deadline, into that seat. Do the same at once when
Neon is unavailable or its launch fails. Argon gets its own 20-minute
deadline; Grok already holds a seat, so if Argon misses too, that seat stays
empty and the review is partial.

Report a seat as fallen back with the first reviewer's elapsed time, and keep
that reviewer's calibration row with `findings` empty.

A report quarantined on the grounding trigger
([grounding.md](grounding.md)) starts the same fallback at once, with the
same brief and reading-budget rules as above. It differs from a missed
deadline in two ways: the first report's findings are kept and verified,
and its calibration row keeps its findings and verdict counts, with `score`
set to `withheld`. Any finder's seat can be quarantined. A seat with no
fallback named here (Sol, Grok, or Claude Opus in its own seat) stays
partial.

A November 2026 bake-off on one 46-line diff with five known defects set
the first order: Sol found 5 of 5 in 38 seconds, Argon 5 of 5 in about 2
minutes, and Grok high fast 4 of 5 in about 3 minutes, with severity
inflated to P0. One small diff cannot separate Sol from Argon; the
calibration log decides from here.

The first log review, on 12 November 2026 (161 rows, grouped by the `model`
column so fallback runs count for the model that ran), found:

| Model | Runs | No report | Refuted | Unique confirmed per run | Median minutes |
|---|---|---|---|---|---|
| Sol | 77 | 0 | 1% | 2.16 | 10 |
| Argon | 52 | 6 | 21% | 1.33 | 13 |
| Grok | 22 | 0 | 11% | 1.73 | 18 |
| Carbon | 8 | 5 | 7% | 1.38 | 15 |

Argon's refutations include cited files and spec text that do not exist,
which led to the grounding gate. Grok's rows come mostly from tier 3 and
Argon's from tier 2 deep reviews, so the comparison is confounded.

A benchmark the same night replayed PR #97 of beril-workbench (4,500 lines)
at the commit before five real bugs were fixed, one run per reviewer, Gemini
through `agy` with the bundle:

| Reviewer | Minutes | Real bugs found | Extra valid | False |
|---|---|---|---|---|
| Sol | 16.4 | 4 of 5 | 5 | 0 |
| Sonnet | 10.0 | 3 of 5 | 8 | 0 |
| Argon | 14.0 | 3 of 5, one no one else found | 5 | 1 |
| Carbon | 19.3 | 2 of 5 | 7 | 2 |

Codex had found three of the bugs originally, which favours Sol. Carbon was
the slowest and found the fewest, so Argon kept the tier 2 seat and Carbon
the council seat.

On 19 November 2026 the same replay ran Carbon high and Neon high side by
side through `agy`, at `6f6735d8` against the fixes in `f0e48847`,
`1feb6671` and `01357e21`, with one bundle and brief for both. Carbon read the
bundle, then hit four empty model calls with errors and returned nothing at
its 30-minute deadline. Five of the 8 Carbon runs in the first log review
also returned no report.
Neon high finished in 14.3 minutes and found 3 of 5 exactly (per-project fix
dedupe, per-revision streak, the pass's clock), one partly (baseline replay
arms), and missed the zero-row source case. All of its file and line
citations existed; its 10 other findings were not verified.

## Launch routes

Use T3's `delegate_task` inside T3 Code, and the CLI otherwise. Gemini
finders fall back to `agy` inside T3 as [Gemini finders](#gemini-finders)
says. Call `orchestrator_capabilities` once before the first
`delegate_task`, with `search: "gemini-4"` when a Gemini seat is in the
tier. Start one
`delegate_task` per finder or verifier with `role: "review"`,
`mode: "async"`, and the brief as `task`; keep each `taskId`. Completion
wakes the coordinator, so do not poll. The child's final message is its
report: save it unchanged to the report path.

| Reviewer | T3 `target` | CLI |
|---|---|---|
| Sol | `providerInstanceId: "codex"`, `model: "gpt-6.2-sol"`, `options: {reasoningEffort: "high"}` | `codex exec -C <checkout> -s read-only -m gpt-6.2-sol -c model_reasoning_effort=high --ephemeral -o <report> "<prompt>"` |
| Argon | `providerInstanceId: "antigravity"`, `model: "gemini-4-argon"`, `options: {thought_level: "high"}` | `agy --mode plan --model gemini-4-argon-high --add-dir <private dir> --output-format stream-json --print-timeout 20m -p "<prompt>" > <events.jsonl>`, run from the checkout in the background |
| Neon | `providerInstanceId: "antigravity"`, `model: "gemini-4-neon"`, `options: {thought_level: "high"}` | `agy --mode plan --model gemini-4-neon-high --add-dir <private dir> --output-format stream-json --print-timeout 20m -p "<prompt>" > <events.jsonl>`, run from the checkout in the background |
| Claude Sonnet | `providerInstanceId: "claudeAgent"`, `model: "claude-sonnet-5-5"`, `options: {effort: "high"}` | `env -u ANTHROPIC_API_KEY claude -p --model claude-sonnet-5-5 --effort high --permission-mode plan "<prompt>" > <report>` |
| Grok | `providerInstanceId: "cursor"`, `model: "grok-4.7"`, `options: {reasoning_effort: "high", fastMode: false}`; as Neon's tier 2 fallback, `fastMode: true` | `cursor-agent -p --trust --mode plan --model grok-4.7-high --output-format text "<prompt>" > <report>`, run from the checkout; as Neon's tier 2 fallback, `--model grok-4.7-high-fast` |
| Claude Opus | `providerInstanceId: "claudeAgent"`, `model: "claude-opus-5-5"`, `options: {effort: "high"}` | `env -u ANTHROPIC_API_KEY claude -p --model claude-opus-5-5 --effort high --permission-mode plan "<prompt>" > <report>` |

`<prompt>` is one short line: read the brief at its absolute path and follow
it. T3 offers no read-only runtime mode, so read-only rests on the brief and
the pinned-state comparison before triage.

`agy` and `cursor-agent` plan modes are read-only and cannot run shell
commands: headless `agy` denies the call and can end with an empty report.
`agy` reads outside the checkout only through `--add-dir`. Before launching
either, save the log, the diff, `git status --short --untracked-files=all`,
and the list of changed and untracked files into the private directory, and
fill the brief's `{SAVED_INPUTS}` with those paths. Both CLIs can exit 0
without a report; the completion token decides. For `agy`, the report is the
`response` of the last `result` event in `<events.jsonl>`, and
`--print-timeout` is the Gemini deadline.

T3 lists a new Antigravity model only after a session starts or the user
presses **Refresh provider status** in its provider settings. Until then,
the model goes through `agy`, as [Gemini finders](#gemini-finders) says.

## Score line

Every finder ends its verdict with a score out of 10. The final report and
the PR's Verification section carry one line per review:

```text
Independent review, tier 2 deep: GPT-6.2 Sol 7/10, Gemini 4 Neon 8/10; 2 confirmed and fixed, 1 refuted.
```

A repeat review appends its scores (`Sol 7 -> 9/10`). A reviewer that gave
none gets `no score`. A quarantined report gets `withheld (ungrounded)` or
`withheld (refuted)` in place of its score. Never invent one.

## Calibration log

After triage, append one row per finder to
`~/.local/state/independent-review/reviewers.tsv` (create it with this header
when missing):

```text
ts	repo	target	tier	shape	reviewer	model	route	minutes	findings	confirmed	plausible	refuted	unique_confirmed	score	ungrounded
```

If the existing header ends at `score`, append an empty `ungrounded` cell to
every row and the name to the header before adding rows. An empty cell
means unknown; never fill old rows with `0`.

`minutes` is the finder's wall time to its report, or to the deadline.
`unique_confirmed` counts CONFIRMED findings no other finder raised.
`ungrounded` counts the report's ungrounded citations by the definition in
[grounding.md](grounding.md); leave it empty for a seat with no report.
`model` names the model that ran, not the seat it filled. Strip tabs and
newlines from cells. When a reviewer has about ten rows, report its
confirmed and unique rates and its median minutes, and propose a roster change
if they support one; the user approves changes to this file.

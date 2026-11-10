# Reviewers, tiers, and launch routes

## Roster

Ranked. A seat goes to the highest-ranked reviewer whose model family did not
write the change. Model IDs age: take the newest flagship of each family from
`orchestrator_capabilities` or the CLI's model list, and update this table
when one is replaced. Gemini 4 Carbon is a tier above Argon, not its
successor: Google keeps Argon as its default for most engineering work, so
Carbon holds only the council seat until the calibration log says otherwise.

| Rank | Reviewer | Family | Seats |
|---|---|---|---|
| 1 | GPT-6.1 Sol, high effort | OpenAI | tiers 1-3, verifier |
| 2 | Gemini 4 Argon, high thinking, through Antigravity | Google | tier 2; Carbon's fallback in tier 3 |
| 2 | Gemini 4 Carbon, high thinking, through Antigravity | Google | tier 3 |
| 3 | Grok 4.7, high effort, through Cursor | xAI | tier 3; Argon's fallback in tier 2 |
| - | Claude Opus 5.5, high effort | Anthropic | rank 1 when Claude did not write the change; verifier |

When Codex wrote the change, Claude Opus takes rank 1 and Sol drops out.

## Tiers

- **Tier 1:** the first eligible reviewer.
- **Tier 2:** the first two eligible reviewers.
- **Tier 3 (council):** the first three eligible reviewers, with Carbon in
  the Gemini seat and Grok included.

A seat whose reviewer is unavailable goes to the next eligible reviewer.
Grok fills a tier 2 seat only as Argon's fallback, and Argon fills a tier 3
seat only as Carbon's fallback, under Gemini finders below. With no eligible substitute, leave the seat empty and label the
review partial. Say which seat moved or stayed empty, and why.

## Verifiers

Verifiers settle findings, so they are Claude Opus or Sol only: whichever of
the two is not the finding reviewer's family, as a fresh native subagent
when it is the coordinator's own family. Never use Carbon, Argon, or Grok as
verifiers until the calibration log shows they settle findings reliably.

## Gemini finders

Antigravity's Gemini models tend to read files in small slices, re-read what
they already have, and open files they guess at, which can burn quota for
tens of minutes. Every Gemini finder's brief gets the
[reading budget](reading-budget.md) inserted before its Intent section, and
a deadline from launch: 20 minutes for Argon, 30 for Carbon, which Google
says spends more tokens per task.

In tier 2, at Argon's deadline, cancel the task (`task_cancel` in T3) and
launch Grok 4.7 high fast with the same brief, minus the reading budget, into
that seat. Do the same at once when Argon is unavailable or its launch fails.
Grok gets its own 20-minute deadline; if it misses that too, label the seat
partial.

In tier 3, at Carbon's deadline, cancel it and launch Argon with the same
brief, reading budget included, into that seat. Do the same at once when
Carbon is unavailable or its launch fails. Argon gets its own 20-minute
deadline; Grok already holds a seat, so if Argon misses too, that seat stays
empty and the review is partial.

Report a seat as fallen back with the first reviewer's elapsed time, and keep
that reviewer's calibration row with `findings` empty.

A November 2026 bake-off on one 46-line diff with five known defects set
this order: Sol found 5 of 5 in 38 seconds, Argon 5 of 5 in about 2
minutes, and Grok high fast 4 of 5 in about 3 minutes, with severity
inflated to P0. One small diff cannot separate Sol from Argon; the
calibration log decides from here.

## Launch routes

Use T3's `delegate_task` inside T3 Code; otherwise the CLI. Call
`orchestrator_capabilities` once before the first `delegate_task`. Start one
`delegate_task` per finder or verifier with `role: "review"`,
`mode: "async"`, and the brief as `task`; keep each `taskId`. Completion
wakes the coordinator, so do not poll. The child's final message is its
report: save it unchanged to the report path.

| Reviewer | T3 `target` | CLI |
|---|---|---|
| Sol | `providerInstanceId: "codex"`, `model: "gpt-6.1-sol"`, `options: {reasoningEffort: "high"}` | `codex exec -C <checkout> -s read-only -m gpt-6.1-sol -c model_reasoning_effort=high --ephemeral -o <report> "<prompt>"` |
| Argon | `providerInstanceId: "antigravity"`, `model: "gemini-4-argon"`, `options: {thinking_level: "high"}` | `agy --mode plan --model gemini-4-argon-high --add-dir <private dir> --print-timeout 20m -p "<prompt>" > <report>`, run from the checkout |
| Carbon | `providerInstanceId: "antigravity"`, `model: "gemini-4-carbon"`, `options: {thinking_level: "high"}` | `agy --mode plan --model gemini-4-carbon-high --add-dir <private dir> --print-timeout 30m -p "<prompt>" > <report>`, run from the checkout |
| Grok | `providerInstanceId: "cursor"`, `model: "grok-4.7"`, `options: {reasoning_effort: "high", fastMode: false}`; as Argon's fallback, `fastMode: true` | `cursor-agent -p --trust --mode plan --model grok-4.7-high --output-format text "<prompt>" > <report>`, run from the checkout; as Argon's fallback, `--model grok-4.7-high-fast` |
| Claude Opus | `providerInstanceId: "claudeAgent"`, `model: "claude-opus-5-5"`, `options: {effort: "high"}` | `env -u ANTHROPIC_API_KEY claude -p --model claude-opus-5-5 --effort high --permission-mode plan "<prompt>" > <report>` |

`<prompt>` is one short line: read the brief at its absolute path and follow
it. T3 offers no read-only runtime mode, so read-only rests on the brief and
the pinned-state comparison before triage.

`agy` and `cursor-agent` plan modes are read-only and cannot run shell
commands, and `agy` reads outside the checkout only through `--add-dir`.
Before launching either, or any Gemini finder, save the log, the diff,
`git status --short --untracked-files=all`, and the list of changed and
untracked files into the private directory, and fill the brief's
`{SAVED_INPUTS}` with those paths. Both CLIs can exit 0 without a report; the
completion token decides. For `agy`, `--print-timeout` is the Gemini
deadline.

T3 lists a new Antigravity model only after a session starts or the user
presses **Refresh provider status** in its provider settings. When
`orchestrator_capabilities` lacks Carbon but `agy models` lists it, ask the
user to refresh, or launch it through the CLI.

## Score line

Every finder ends its verdict with a score out of 10. The final report and
the PR's Verification section carry one line per review:

```text
Independent review, tier 2 deep: GPT-6.1 Sol 7/10, Gemini 4 Argon 8/10; 2 confirmed and fixed, 1 refuted.
```

A repeat review appends its scores (`Sol 7 -> 9/10`). A reviewer that gave
none gets `no score`. Never invent one.

## Calibration log

After triage, append one row per finder to
`~/.local/state/independent-review/reviewers.tsv` (create it with this header
when missing):

```text
ts	repo	target	tier	shape	reviewer	model	route	minutes	findings	confirmed	plausible	refuted	unique_confirmed	score
```

`minutes` is the finder's wall time to its report, or to the deadline.
`unique_confirmed` counts CONFIRMED findings no other finder raised. Strip
tabs and newlines from cells. When a reviewer has about ten rows, report its
confirmed and unique rates and its median minutes, and propose a roster change
if they support one. Carbon is the exception: after about five council rows,
compare it with Argon's rows and propose whether it should take the tier 2
seat;
the user approves changes to this file.

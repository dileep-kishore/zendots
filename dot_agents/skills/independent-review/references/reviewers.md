# Reviewers, tiers, and launch routes

## Roster

Ranked. A seat goes to the highest-ranked reviewer whose model family did not
write the change. Model IDs age: take the newest flagship of each family from
`orchestrator_capabilities` or the CLI's model list, and update this table
when one is replaced.

| Rank | Reviewer | Family | Seats |
|---|---|---|---|
| 1 | GPT-6.1 Sol, high effort | OpenAI | tiers 1-3, verifier |
| 2 | Gemini 4 Argon, high thinking, through Antigravity | Google | tiers 2-3 |
| 3 | Grok 4.7, high effort, through Cursor | xAI | tier 3 only |
| - | Claude Opus 5.5, high effort | Anthropic | rank 1 when Claude did not write the change; verifier |

When Codex wrote the change, Claude Opus takes rank 1 and Sol drops out.

## Tiers

- **Tier 1:** the first eligible reviewer.
- **Tier 2:** the first two eligible reviewers.
- **Tier 3 (council):** the first three eligible reviewers, Grok included.

A seat whose reviewer is unavailable goes to the next eligible reviewer,
except that Grok fills tier 3 seats only. With no eligible substitute, leave
the seat empty and label the review partial. Say which seat moved or stayed
empty, and why.

## Verifiers

Verifiers settle findings, so they are Claude Opus or Sol only: whichever of
the two is not the finding reviewer's family, as a fresh native subagent
when it is the coordinator's own family. Never use Argon or Grok as
verifiers until the calibration log shows they settle findings reliably.

## Gemini finders

Antigravity's Gemini models tend to read files in small slices, re-read what
they already have, and open files they guess at, which can burn quota for
tens of minutes. Every Gemini finder's brief gets the
[reading budget](reading-budget.md) inserted before its Intent section, and
a 25-minute deadline: at the deadline, cancel the task (`task_cancel` in T3)
and label that seat partial.

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
| Argon | `providerInstanceId: "antigravity"`, `model: "gemini-4-argon"`, `options: {thinking_level: "high"}` | `agy --mode plan --model gemini-4-argon-high --add-dir <private dir> --print-timeout 25m -p "<prompt>" > <report>`, run from the checkout |
| Grok | `providerInstanceId: "cursor"`, `model: "grok-4.7"`, `options: {reasoning_effort: "high", fastMode: false}` | `cursor-agent -p --trust --mode plan --model grok-4.7-high --output-format text "<prompt>" > <report>`, run from the checkout |
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
completion token decides. For `agy`, use `--print-timeout 25m` as the Gemini
deadline.

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
if they support one;
the user approves changes to this file.

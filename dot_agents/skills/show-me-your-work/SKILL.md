---
name: show-me-your-work
description: Use for long-running, unattended, or multi-phase work that a human reviews after stepping away, or when the user asks for a decision trail or audit log. Keeps one append-only TSV with a row per decision (what, why, evidence, result).
---

# Show me your work

For work a human reviews after the fact, a decision trail lets them
reconstruct what was decided, why, and on what evidence without rerunning the
work or reading the transcript. Keep one log per effort so a future agent can
find it.

## Format

One TSV file, one row per decision. TSV renders as a table on GitHub, reads
in spreadsheets and `column -s$'\t' -t`, and appends with one command. Cells
stay single-line; evidence is a pointer, not prose.

```
ts	phase	decision	why	evidence	result
```

- **ts**: ISO 8601 UTC timestamp.
- **phase**: the phase or workstream.
- **decision**: what was chosen or done, one line.
- **why**: the reason in plain words a teammate would use.
- **evidence**: a commit SHA, PR number, `file:line`, or artifact path.
- **result**: the outcome or state: `tests green`, `reverted`, `open`,
  `INCONCLUSIVE`.

Append with the helper, which stamps `ts`, writes the header on first use,
strips tabs and newlines, and prefixes a cell that starts with `=`, `+`, `-`,
or `@` with a single quote so a spreadsheet never treats it as a formula:

```bash
~/.agents/skills/show-me-your-work/scripts/log.sh <log> <phase> <decision> <why> <evidence> <result>
```

## Runs

A run is one agent session, including its later turns and any summary that
continues it. A handoff, a replacement agent, or a new chat starts a new
run. When a run adds to a log that already has rows, its first row has phase
`start`, with the `ts` range of earlier rows it did not write in `decision`
and the session or agent id in `evidence`. A run that returns to a log in a
later turn reads the last rows first, and writes another `start` row if a
different run wrote since. Use phase `start` for nothing else.

## What to log

Decision points and checkpoints, not every action: a fork chosen, a unit
finished with its verification result, a pivot or revert with its trigger, a
blocker surfaced, a gate fixed. One row per iteration for loop runs. Skip the
trivial and self-evident.

## Where it lives

A working artifact by default: `decisions.tsv` in the work directory, or
`.audit/<task-slug>.tsv` when several efforts run at once, kept out of git.
Commit it only when the work is large enough that a reviewer needs the trail
to trust the result; then it renders as a table in the PR.

## Rules

- One row is one decision. If it does not fit on a line, it is not crisp yet.
- Append-only. A wrong call gets a new row that supersedes it; never edit or
  delete history.
- Prefer evidence a reviewer can re-run (a committed script) over a one-off.

## Before handing back

Audit this run's rows, from its `start` row or the top of a log it created
up to the next run's `start` row, against tool evidence: the commands you
ran and their output, commits, and files written, not your memory of the
session. Every row maps to a real action; every evidence pointer resolves
and shows what the row claims; a fork, pivot, or abandoned approach that
shaped the work is logged. Correct the log, not the story: the log stays
append-only, so a wrong or invented row gets a new row that supersedes it
with what happened and a pointer that resolves. If the user wants the trail reviewed by a
fresh context, use the `independent-review` skill on the log and the diff.

Other skills that need an audit trail point here instead of inventing one.

Locally maintained. Adapted from Cursor pstack's
[show-me-your-work](https://github.com/cursor/plugins/blob/main/pstack/skills/show-me-your-work/SKILL.md);
`scripts/log.sh` is copied from it under its MIT license.

---
name: orca-independent-review
description: Use when the user asks for an independent, second-opinion, or fresh-context review of a PR, a branch, or the current worktree changes, run by a separate codex, claude, or pi session that Orca starts in the same checkout.
disable-model-invocation: true
---

# Orca Independent Review

Start a fresh agent in the current worktree through Orca, hand it a written
brief, and let it review the change with none of this session's context. The
reviewer is read-only and adversarial. You stay the coordinator: you do not
review the diff yourself.

Resolve the Orca executable first, as the `orca-cli` skill describes: use
`$ORCA_CLI_COMMAND` if set, `orca-dev` when `ORCA_DEV_REPO_ROOT` is set,
`orca-ide` on Linux outside an Orca terminal, otherwise `orca`. `ORCA` below
stands for that executable.

## 1. Collect inputs

Take what the user gave. Ask for the rest in one message, offering an inferred
default for each:

| Input | Values | Default to offer |
|---|---|---|
| target | `pr <number>`, `branch <base-ref>`, `worktree` | open PR for this branch, else `branch origin/main`, else `worktree` if dirty |
| reviewer | `codex`, `claude`, `pi` | none, ask |
| intent | a paragraph, or a path to the spec, plan, or issue | derived from commit messages and PR body; state it and let the user correct it |
| wait | `no` (hand off) or `yes` (wait and triage) | `no` |

The reviewer challenges execution against the intent, never the intent itself,
so a wrong intent wastes the whole review. Confirm it.

## 2. Resolve the diff

```bash
# pr: review the PR's actual commits, not whatever the local branch holds
gh pr view <n> --json baseRefName,headRefOid,title,body,url
[ "$(git rev-parse HEAD)" = "<headRefOid>" ] || stop and ask before `gh pr checkout <n>`
git fetch origin <baseRefName>
BASE=$(git merge-base FETCH_HEAD HEAD)
# branch:
BASE=$(git merge-base <base-ref> HEAD)
# both:  DIFF="git diff $BASE..HEAD"   LOG="git log --oneline $BASE..HEAD"
# worktree:
DIFF="git diff HEAD"; git status --porcelain   # list untracked files in the brief
```

Run the diff with `--stat`. An empty diff means stop and tell the user; do not
spawn a reviewer for nothing.

Collect project standards the reviewer should hold the change to: whichever of
`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md` exist at the
repo root.

## 3. Write the brief

Copy [references/review-brief.md](references/review-brief.md), fill every
`{PLACEHOLDER}`, and save it outside the repo:

```bash
DIR="${TMPDIR:-/tmp}/orca-review/$(basename "$(git rev-parse --show-toplevel)")-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DIR"   # brief.md and report.md live here
```

Paste the intent and the standards files' relevant sections into the brief
rather than pointing at them; the reviewer should not have to hunt.

## 4. Spawn the reviewer

```bash
ORCA status --json
ORCA terminal create --worktree active --title "review: <target>" --command "<reviewer>" --json
ORCA terminal wait --terminal <handle> --for tui-idle --timeout-ms 120000 --json
ORCA terminal read --terminal <handle> --json
```

If the read shows a startup prompt (workspace trust, theme, login), answer it
with `terminal send`, then wait for `tui-idle` again. Then send one line:

```bash
ORCA terminal send --terminal <handle> --text "Read $DIR/brief.md and follow it exactly. Write the report to $DIR/report.md." --enter --json
```

Long prompts through `terminal send` get mangled by TUIs, which is why the
brief is a file.

## 5. Hand off or triage

**wait = no**: report the terminal handle, `$DIR`, and how to read the result
(`ORCA terminal read --terminal <handle>`, or `cat $DIR/report.md`). Stop.

**wait = yes**: poll for `$DIR/report.md` with a bounded sleep loop
(`until [ -s "$DIR/report.md" ]; do sleep 5; done`, capped at about an hour).
`terminal wait --for tui-idle` reports idle while the agent is still thinking,
so it cannot signal completion. Read the report and triage it:

- **Act on**: real defects with evidence. Five or fewer; more means you are not filtering.
- **Consider**: judgement calls worth a human look.
- **Dismissed**: style preferences, unreachable hypotheticals, anything the reviewer misread. Say why in one line each.

Never apply fixes from the report on your own. Present the triage and let the
user decide.

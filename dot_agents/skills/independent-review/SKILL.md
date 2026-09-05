---
name: independent-review
description: Run a fresh-context second opinion on a PR, branch, or working changes using available subagents or external reviewer processes. Use when the user requests independent review, or total review with both Claude and Codex.
---

# Independent review

Coordinate a fresh, read-only review without passing along this conversation or
your conclusions. This skill owns scope, briefing, completion, and triage;
launchers such as `orca-independent-review` supply only session mechanics.

## Choose the review

Use the user's target, reviewer, and intent. Infer routine missing details from
the checkout, PR, or spec and state the assumptions. Ask only when ambiguity
would materially change the review.

- **Single**, the default: one fresh reviewer. Honor a named provider/model;
  otherwise use an available reviewer with a separate context.
- **Dual / total review**, when requested: Claude and Codex independently review
  the same scope, preferably in parallel. Honor another requested pair. Use
  configured model defaults unless the user specifies models or effort.
- Wait and triage by default. If the user requests a background handoff, return
  the run handles, brief/report paths, and how to retrieve results, then stop.

Do not silently substitute a named reviewer. If one is unavailable, explain the
limitation and ask whether the available alternative is acceptable. Two agents
using the same model are independent contexts, not a cross-model review.

## Pin the scope

Record the absolute checkout path, HEAD, target, and relevant project standards.
Respect explicit file or staged-only scopes rather than widening them.

- **Working changes:** inspect staged and unstaged changes with `git diff HEAD`
  and untracked files with `git status --short --untracked-files=all`. Untracked
  files count even when the tracked diff is empty. For an unborn HEAD, inspect
  the index and working files directly.
- **Branch:** resolve the requested base and HEAD to commit IDs, compute their
  merge base, and review the diff from that merge base to the pinned head.
  Infer the base from PR/default-branch metadata, not a hard-coded branch name.
- **PR:** read its base, head SHA, and intent. Confirm the checkout matches that
  head before reviewing. If it does not, prepare an isolated checkout when
  authorized or ask; never switch the user's checkout without authorization.
  Resolve the PR base from its repository, accounting for forked PRs.

For committed branch/PR reviews, check for pre-existing dirty files even when
HEAD matches. Use a clean isolated checkout or read all surrounding context
from the pinned commits; do not mix local edits into a committed review.

For unspecified "current work", use dirty changes if present, otherwise the
current PR or branch comparison. Stop for an empty scope only after checking
untracked files where applicable.

Keep the reviewed state stable until reviewers finish. Record the diff and
untracked file contents or hashes outside the checkout, then compare them and
HEAD before triage. If they changed, identify the stale coverage and rerun the
affected review or report it as incomplete. A clean status alone cannot detect
commits made during review. Do not copy secrets into briefs or artifacts.

## Brief and launch

Create a private temporary directory outside the checkout with `mktemp -d`.
Read [references/review-brief.md](references/review-brief.md) and fill its fields
with the intent, pinned scope, relevant standards, and reviewer-specific output
path and completion token. Give dual reviewers identical substantive briefs.
Do not include your suspected findings, preferred solution, implementation
chat, or the other reviewer's report. Include a user-requested focus verbatim.

Choose a supported launcher in the current environment:

- **Native subagents:** start with no inherited conversation, supplying only
  the brief and checkout. Use read-only permissions when supported. Reviewers
  should perform their own review without recursively launching reviewers.
- **External processes:** inspect the installed CLI's help and available
  provider instructions. Use a fresh noninteractive invocation, explicit cwd,
  and read-only controls where available. Pass the brief through a file/stdin,
  not shell-interpolated user text. Do not resume an implementation session or
  disable permission checks to get a review running.
- **Installed provider helpers:** use their documented public entrypoints only
  when their scope, context isolation, and output contract fit this request.
  In Claude Code, the Codex plugin's review commands are possible single-review
  routes, but have verbatim-output rules and limited scope controls. Read those
  instructions first. Do not call its private rescue runtime from another
  context. Choose a fresh process/subagent when custom briefs or merged triage
  cannot be supported by the helper's contract.
- **Orca:** when requested, use `orca-independent-review` for launch and terminal
  monitoring, retaining this shared workflow. When that wrapper is already
  executing, continue there instead of invoking it recursively.

Outside Orca, including T3 Code, use whichever native tools or installed CLIs
are actually available. Do not assume the host exposes subagents or a particular
provider. If no independent launcher is available, report that blocker rather
than presenting your own review as independent.

## Completion and triage

Keep a handle and separate raw output for each reviewer. Use native task/process
completion plus its final report when available. For interactive sessions, require
the brief's unique completion token as the report's last line; terminal idle or
a nonempty file alone does not mean the review finished.

Use bounded waits with progress updates and a deadline appropriate to the review
size, normally up to an hour. At the deadline, report incomplete work and its
handles. Do not silently abandon owned processes; stop them when cancellation
is authorized, or explicitly hand them off. Preserve reports for inspection.

For dual review, wait for both before combined triage. If one fails, label any
available findings as a partial review; do not imply both completed.

Read the reports in full, verify actionable claims against the scoped code, and
deduplicate by underlying issue. Agreement is not proof; a finding from only one
reviewer may be the most serious. Retain uncertainty when evidence is missing.

Present a concise verdict and prioritized findings with location, evidence,
smallest fix, and reviewer attribution. Briefly explain dismissed findings and
list coverage limits. Link the unchanged raw reports; show them verbatim if
requested. Do not impose a finding quota or manufacture findings for balance.

A review request does not authorize fixes, commits, or pushes. If fixes were
already requested, follow that scope; otherwise present the findings for decision.

Locally maintained. Inspired by the neutral reviewer briefs in
[gpt-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/gpt-review/SKILL.md)
and [fable-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/fable-review/SKILL.md),
and the dual-review workflow in
[total-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/total-review/SKILL.md).

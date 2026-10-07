---
name: independent-review
description: Fresh-context review of a PR, branch, or working changes by one reviewer or a Claude/Codex pair. Use when the user asks for independent, total, or deep review, or instructions require one after substantial work.
---

# Independent review

Coordinate a fresh, read-only review without passing along this conversation or
your conclusions. Finders hunt for bugs, a fresh verifier tries to refute each
finding against the code, and you triage what survives. You own scope,
briefing, completion, and triage; launchers such as `orca-independent-review`
supply only session mechanics.

## Choose the review

Use the user's target, reviewer, and intent. Infer routine missing details from
the checkout, PR, or spec and state the assumptions. Ask only when ambiguity
would materially change the review.

- **Single**, the default: one fresh finder. Honor a named provider/model;
  otherwise prefer the other vendor: Codex when Claude wrote the change,
  Claude when GPT did. Another tier from the same vendor (Opus and Sonnet)
  does not count. Fall back to any reviewer with a separate context.
- **Dual / total review**, when requested: Claude and Codex independently review
  the same scope, preferably in parallel. Honor another requested pair. Use
  configured model defaults unless the user specifies models or effort.
- **Deep**, when requested, or when the change is large (roughly 1,000+
  changed lines) or touches authentication, authorization, persistent data or
  migrations, money, or concurrency: several finders, each with one lens from
  [references/lenses.md](references/lenses.md), split across both vendors.
  State that you chose deep and why.
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

Collect standards and review rules as
[references/review-rules.md](references/review-rules.md) describes, including
any `REVIEW.md`, from the revision the change starts from.

Keep the reviewed state stable until finders and verifiers finish. Record the
diff and untracked file contents or hashes outside the checkout, then compare
them and HEAD before triage. If they changed, identify the stale coverage and
rerun the affected review or report it as incomplete. A clean status alone
cannot detect commits made during review. Do not copy secrets into briefs or
artifacts; record hashes, or redact, for files that hold credentials.

## Brief and launch finders

Create a private temporary directory outside the checkout with `mktemp -d`.
Fill [references/review-brief.md](references/review-brief.md) with the intent,
pinned scope, standards, and a per-finder report path and completion token.
`{LENS}` is the finder's lens for deep review; otherwise "Full review: cover
every step of the process." Append a user-requested focus verbatim. Every
finder gets the same substantive brief apart from its lens. Do not include
your suspected findings, preferred solution, implementation chat, or another
reviewer's report.

Choose a supported launcher in the current environment:

- **Native subagents:** start with no inherited conversation, supplying only
  the brief and checkout. Use read-only permissions when supported. Reviewers
  should perform their own review without recursively launching reviewers.
- **External processes:** inspect the installed CLI's help and available
  provider instructions. Use a fresh noninteractive invocation, explicit cwd,
  and read-only controls where available. Pass the brief through a file/stdin,
  not shell-interpolated user text. Do not resume an implementation session or
  disable permission checks to get a review running. Launch Claude as
  `env -u ANTHROPIC_API_KEY claude -p ...`: with that variable set, the CLI
  bills the API key instead of the claude.ai subscription.
- **Installed provider helpers:** use their documented public entrypoints only
  when their scope, context isolation, and output contract fit this request.
  The Codex plugin's review commands and built-in `/code-review` skills use
  their own briefs and output rules, so they cannot replace the finder brief
  here. Do not call the Codex plugin's private rescue runtime from another
  context.
- **Orca:** when requested, use `orca-independent-review` for launch and terminal
  monitoring, retaining this shared workflow. When that wrapper is already
  executing, continue there instead of invoking it recursively.

Use whichever native tools or installed CLIs are actually available. If no
independent launcher is available, report that blocker rather than presenting
your own review as independent.

## Wait for completion

Keep a handle and separate raw output for each finder and verifier. Use native
task/process completion plus its final report when available. For interactive
sessions, require the brief's unique completion token as the report's last
line; terminal idle or a nonempty file alone does not mean the review finished.

Set a deadline appropriate to the review size, normally up to an hour. Native
subagents and harness-tracked background tasks notify on completion; do not poll
them. Start external CLIs in the background or with a timeout well under the
shell tool's cap, since a killed shell call kills the reviewer mid-run. Then
poll: wait a bounded interval, check the report for the token, repeat until it
appears or the deadline passes. At the deadline, report incomplete work and its
handles. Do not silently abandon owned processes; stop them when cancellation
is authorized, or explicitly hand them off. Preserve reports for inspection.

Wait for every finder before verification. If one fails, label the review
partial and name the lens or reviewer whose coverage is missing.

## Verify findings

You wrote or own the change, so do not judge findings yourself. First merge
duplicates by underlying failure: two findings on one line with different
failures stay separate, and one failure reported from two places is one
finding that keeps both attributions. Then verify each finding in a fresh
context with [references/verify-brief.md](references/verify-brief.md):

- One verifier per P0–P2 finding, in parallel; P3 findings share one verifier,
  which receives that batch and no other findings.
- Launch verifiers like finders, with no inherited conversation. Prefer a model
  family other than the finding's reviewer; your own fresh subagents usually
  qualify for single review.
- Give each verifier its finding verbatim with the scope, intent, rules, a
  report path and completion token, and its own scratch directory inside the
  private temporary directory, not other findings, other reports, or your
  opinion.
- A verifier that fails or misses the deadline leaves its finding UNVERIFIED,
  never refuted.

## Triage and report

Read every report and verdict in full. Overrule a verdict only with code
evidence and say so. Agreement between finders raises rank, not certainty; a
finding from one finder may be the most serious.

Present a one-line verdict, then CONFIRMED findings, then PLAUSIBLE and
UNVERIFIED ones labeled with the step left unproven, most severe first. Give
each its location, trigger, evidence, repro, smallest fix, and finder and
verifier attribution. List REFUTED findings one line each with the refuting
file:line. Then coverage: the concern map, lenses run or skipped, and what no
one could verify. Link the unchanged raw reports; show them verbatim if
requested. Do not impose a finding quota or manufacture findings for balance.

When a refuted or user-dismissed finding would recur in this repository,
propose a precedent as [references/review-rules.md](references/review-rules.md)
describes. Write it only after the user approves.

A review request does not authorize fixes, commits, or pushes. If fixes were
already requested, fix CONFIRMED findings and settle each PLAUSIBLE one by
fixing it or recording why not; otherwise present the findings for decision.

Locally maintained. Inspired by the neutral reviewer briefs in
[gpt-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/gpt-review/SKILL.md)
and [fable-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/fable-review/SKILL.md),
and the dual-review workflow in
[total-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/total-review/SKILL.md).
The bug bar follows the OpenAI Codex review rubric; find-then-refute follows
Anthropic's code-review plugin, Juror, and Trail of Bits' fp-check.

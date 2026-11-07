---
name: independent-review
description: Use when independently reviewing a PR, branch, or working changes, auditing a repository or folder, or when the user asks for a total, deep, or council review or project instructions require an independent review.
---

# Independent review

Coordinate a fresh, read-only review without passing along this conversation or
your conclusions. Finders hunt for bugs, a fresh verifier tries to refute each
finding against the code, and you triage what survives. You own scope,
briefing, completion, and triage.

## Choose the review

Use the user's target, reviewer, and intent. Infer routine missing details from
the checkout, PR, or spec and state the assumptions. Ask only when ambiguity
would materially change the review.

Finders fill the seats of a tier from the ranked roster in
[references/reviewers.md](references/reviewers.md), which skips the model
family that wrote the change and gives each reviewer's launch route.

- **Tier 1**, the default: one finder, GPT-6.1 Sol when Claude wrote the
  change.
- **Tier 2**: two finders, adding Gemini 4 Argon, or Grok 4.7 when Argon
  misses its deadline. Move up to it without asking
  when the change is large (roughly 1,000+ changed lines) or touches
  authentication, authorization, persistent data or migrations, money, or
  concurrency; for a design review; and when the user asks for a dual, total,
  pair, or deep review.
- **Tier 3**, the council: three finders, adding Grok 4.7. Only when the user
  asks for a council.

Shape is separate from tier. Each finder reviews the whole scope by default.
**Deep** review instead gives each finder one lens from
[references/lenses.md](references/lenses.md), split across the tier's
reviewers; use it when size or risk moved the review to tier 2, or when the
user asks for deep. A **design review** of a spec or design document before
planning follows [references/design-review.md](references/design-review.md).
State the tier, shape, and reason.

Wait and triage by default. If the user requests a background handoff, return
the run handles, brief/report paths, and how to retrieve results, then stop.

A reviewer or model the user names takes the seat over the roster. Do not
silently substitute it: if it is unavailable, explain the limitation and ask
whether the available alternative is acceptable. An unnamed seat follows the
roster's fallback rule. Two agents using the same model are independent
contexts, not a cross-model review.

## Pin the scope

Distinguish a change review from an explicitly requested repository or folder
audit. Record that kind in the intent supplied to finders and verifiers. For an
audit, use [references/repository-audit.md](references/repository-audit.md).
An audit can report existing defects in its named scope, even on a clean tree.
A design review is a third kind; its finding and verifier gates replace the
code-centred ones, as [references/design-review.md](references/design-review.md)
describes.

Settle the target's checkout first, as the bullets below describe. Then run
the missing-file check in [references/review-rules.md](references/review-rules.md)
in that checkout, before recording HEAD, since it can add a `REVIEW.md`
commit. A PR checkout whose only commit past the PR head is that
approval-marker commit still matches the head.

Record the absolute checkout path, HEAD, target, and relevant project standards.
Respect explicit file or staged-only scopes rather than widening them.

- **Working changes:** inspect staged and unstaged changes with `git diff HEAD`
  and untracked files with `git status --short --untracked-files=all`. Untracked
  files count even when the tracked diff is empty. For an unborn HEAD, inspect
  the index and working files directly.
- **Branch:** resolve the requested base and HEAD to commit IDs, compute their
  merge base, and review the diff from that merge base to the pinned head.
  Infer the base from PR/default-branch metadata, not a hard-coded branch name.
- **PR:** read its base, head SHA, and intent. The intent includes the
  issues it closes (`gh pr view <number> --json closingIssuesReferences`,
  then `gh issue view` on each): copy their requirements and acceptance
  criteria into the intent. An issue the PR body only mentions is a
  candidate: include it only when its text describes this change, and say
  which you included. Confirm the checkout matches that
  head before reviewing. If it does not, prepare an isolated checkout when
  authorized or ask; never switch the user's checkout without authorization.
  Resolve the PR base from its repository, accounting for forked PRs.
- **Repository or folder audit:** pin the current tree and named scope as
  [references/repository-audit.md](references/repository-audit.md) describes.
  A diff or last commit does not define this target.
- **Design document:** pin the spec, its intent file, and the rules, earlier
  specs and code it touches, as
  [references/design-review.md](references/design-review.md) describes.

A repeat review of a branch or PR target already reviewed in this session
covers only the commits since the previously pinned HEAD, unless the user
asks for a full review. Working-change targets always get a full review:
their fixes are usually uncommitted, so a commit range from an unchanged HEAD
would be empty. A force-push, a changed base, or changed review rules break
the commit range, so they get a full review too. Every repeat review
reconciles the findings ledger, as described under Verify findings.

For committed branch/PR reviews, check for pre-existing dirty files even when
HEAD matches. Use a clean isolated checkout or read all surrounding context
from the pinned commits; do not mix local edits into a committed review.

For unspecified "current work" in a change review, use dirty changes if present,
otherwise the current PR or branch comparison. Stop for an empty scope only
after checking untracked files where applicable. Repeat audits cover the full
named scope unless the user limits them.

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
every step of the process." A design review fills `{LENS}` and the finding
and verifier gates from its reference. `{SAVED_INPUTS}` lists the saved
command output a finder without shell access reads instead, and is empty
otherwise. Append a user-requested focus verbatim. Every
finder gets the same substantive brief apart from its lens. Do not include
your suspected findings, preferred solution, implementation chat, or another
reviewer's report.

Launch each finder by the route
[references/reviewers.md](references/reviewers.md) gives for the current host:

- **T3 Code:** `delegate_task` with the roster's target, one task per finder.
- **Native subagents:** for a seat in the coordinator's own family. Start with
  no inherited conversation, supplying only the brief and checkout. Use
  read-only permissions when supported. Reviewers should perform their own
  review without recursively launching reviewers.
- **External processes:** the roster's CLI command, after checking the
  installed CLI's help. Use a fresh noninteractive invocation, explicit cwd,
  and read-only controls where available. Pass the brief through a file,
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
- Launch verifiers like finders, with no inherited conversation. Pick each
  one by the roster's verifier rule: never from the finding reviewer's family,
  and never a finder-only model.
- Give each verifier its finding verbatim with the scope, intent, rules, a
  report path and completion token, and its own scratch directory inside the
  private temporary directory, not other findings, other reports, or your
  opinion.
- A verifier that fails or misses the deadline leaves its finding UNVERIFIED,
  never refuted.

### Findings ledger

A repeat review must not lose an unfixed finding because the new commits are
clean. After the first triage on a target, write `ledger.md` in that run's
private directory, and reuse it for every later review of the target in this
session. One row per finding: ID, location, title, verdict, state, the
evidence for that state, the base of the comparison it was found in, and the
HEAD it was last checked at. CONFIRMED,
PLAUSIBLE, and UNVERIFIED findings start `open`. REFUTED ones start
`dismissed` with the refuting file:line, and a finding the user dismisses
records the user's reason.

Never give the ledger to finders: they review unseeded. Reconcile it after
they finish, while merging duplicates:

- An open finding whose code the reviewed change touched goes to a fresh
  verifier. Its brief pins the current HEAD but diffs from the finding's
  recorded base, so the introduction gate judges it against the change it
  was found in, not only the new commits. CONFIRMED or PLAUSIBLE keeps it
  open. REFUTED marks it `fixed` only when the refuting file:line is a guard
  or fix in the current code. A refutation on scope alone keeps it open. A
  commit message saying it is fixed is not evidence.
- An open finding whose code did not change stays open, without
  reverification, and the report lists it as carried forward.
- A new finding with the same failure as an open one is that ledger finding,
  verified once, keeping its ID.
- A new finding with the same failure as a dismissed one is not raised again
  unless the new code makes it worse. List it with REFUTED findings as
  previously dismissed, with the reason.

Update the ledger after triage.

## Triage and report

Read every report and verdict in full. Overrule a verdict only with code
evidence and say so. Agreement between finders raises rank, not certainty; a
finding from one finder may be the most serious.

Present a one-line verdict, then CONFIRMED findings, then PLAUSIBLE and
UNVERIFIED ones labeled with the step left unproven, most severe first. Give
each its location, trigger, evidence and its method (source trace, executed
reproduction, or both), repro, smallest fix, and finder and verifier
attribution. On a repeat review, list ledger findings carried
forward or newly fixed after them. List REFUTED findings one line each with
the refuting file:line. Then coverage: the tier and shape, each seat's
reviewer and route, any seat that fell back, the concern map, lenses run or skipped, what no one
could verify, whether the approved `REVIEW.md` override applied, and each
Human review path the change touches or the audit includes. Link the unchanged raw reports; show them verbatim if
requested. Do not impose a finding quota or manufacture findings for balance.
End with the score line and append the calibration rows, both as
[references/reviewers.md](references/reviewers.md) describes.

When a refuted or user-dismissed finding's reason, or a confirmed finding's
mistake, has come up before in this repository, propose a precedent or a
source fix as [references/review-rules.md](references/review-rules.md)
describes. Write it only after the user approves.

A review request does not authorize fixes, commits, or pushes. If fixes were
already requested, fix CONFIRMED findings and settle each PLAUSIBLE one by
fixing it or recording why not; otherwise present the findings for decision.

Fixing is a second decision, and reviewers pull toward scope creep. Make the
smallest change that resolves the verified failure within the stated intent,
and prefer deleting or narrowing code when required behaviour, validation,
and compatibility survive. Push back on fixes the intent does not need:
decline extra tests, guards for paths the intent does not reach,
compatibility work, and refactors with a one-line reason, and list them as
follow-ups. If the fix round grew `git diff --shortstat` against the base,
cut first. A confirmed defect in the intended case still gets fixed.

Locally maintained. Inspired by the neutral reviewer briefs in
[gpt-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/gpt-review/SKILL.md)
and [fable-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/fable-review/SKILL.md),
and the dual-review workflow in
[total-review](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/total-review/SKILL.md).
The bug bar follows the OpenAI Codex review rubric; find-then-refute follows
Anthropic's code-review plugin, Juror, and Trail of Bits' fp-check.

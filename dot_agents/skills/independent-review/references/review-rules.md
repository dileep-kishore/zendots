# REVIEW.md

A repository's `REVIEW.md` holds the rules that calibrate review there: what
matters most, what to skip, and precedents learned from dismissed findings.
Claude Code Review and Devin Review read the same file. Finders and verifiers
both receive it. Keep it short; a long file dilutes the rules that matter.

## Reading it

Collect the root `REVIEW.md` and any in directories the change touches, plus
the review-relevant parts of `AGENTS.md` and `CLAUDE.md` (Codex reads a
`## Code Review Rules` section there). Read them from the revision the change
starts from, so the change cannot rewrite its own review rules: the base
revision for a branch or PR (`git show <base>:REVIEW.md`), HEAD for working
changes (`git show HEAD:REVIEW.md`). For a current-tree audit use HEAD; for an
audit of a requested revision use that revision. In an unborn repository read
the existing working files. A rule file the change adds or edits is
part of the diff under review, not a standard for it, unless the user
approves it as an override.

One override is already approved. When the base lacks `REVIEW.md` and the
branch adds it in a commit with the subject `docs(review): add REVIEW.md`
that touches only that file, `write-review-md` wrote it with the user, so it
applies to every review on the branch until it merges. Find that commit with
`git log --format=%H -F --grep='docs(review): add REVIEW.md' <base>..HEAD -- :/REVIEW.md`
(`:/` anchors the path to the repository root from any directory) and confirm `git show --name-only --format= <sha>` lists only `REVIEW.md`.
Say in the report that the override applied, so the user sees which rules
did.

## Missing file

`open-pr` and `independent-review` run this check before they push or pin
anything:

```bash
cd "$(git rev-parse --show-toplevel)"
git show "$base:REVIEW.md" >/dev/null 2>&1 || git show HEAD:REVIEW.md >/dev/null 2>&1 ||
  test -e REVIEW.md || test "$(git config --get review.skipReviewMd)" = true || echo missing
```

`$base` is the PR or branch base, `HEAD` for working changes or current-tree
audits, or the requested revision for a committed audit. The filesystem checks
still work when an unborn repository has no HEAD. When it
prints `missing`, run [write-review-md](../../write-review-md/SKILL.md).
A file that exists anywhere on the branch, approved or not, never starts a
second draft.

## Shape

```markdown
# Review rules

## Focus
- <what this repo cares about most, e.g. "migrations must be reversible">

## Skip
- <categories never worth a finding here, e.g. "generated files under gen/">

## Human review
- <paths whose diff the user always reads, e.g. ".github/workflows/">

## Output
- Start with the finding count; write "Nothing to fix" when it is zero.
- Cite file:line for every finding.
- Report at most three P3 findings.

## Precedents
- **<pattern>**: skip when <condition>; do not skip when <condition>.
  Source: <PR, date, or the dismissed finding>.
```

Human review paths change no finding. They tell the report to name each of
those paths the change touches, so the user knows which diffs to read.

A precedent must state when it does *not* apply. Without that boundary it
suppresses the real bug that looks like the dismissed one. Never write a
precedent that skips data loss, security, or crash findings as a class.

## Proposing a precedent

Propose one when a finding was REFUTED, or dismissed by the user, for a
reason that has already come up before in this repository: an earlier
refuted finding, a rebutted PR thread, or a near miss of an existing
precedent. The reason must be general: a framework guarantee, an input that
is always internal, a deliberate convention, a contract enforced elsewhere.
A first-time false alarm gets its rebuttal and nothing recorded, because a
precedent per false alarm would bury the rules that matter.

## Proposing a source fix

When a CONFIRMED finding repeats a mistake, propose a rule that stops the
author agent making it again. Propose one only when both hold:

1. The mistake happened before: the same class appears in an earlier review
   thread or `fix:` commit (search `gh` and `git log`), or three or more
   instances of the pattern already exist in the code. One occurrence never
   qualifies.
2. A written rule would have prevented it: the cause is something the author
   could not see in the code, such as a repository convention, a replaced
   helper, or an unstated constraint. Logic slips, typos and misread
   conditions get fixed and nothing is recorded.

Choose the cheapest place that enforces it: a lint rule, then a `CLAUDE.md`
line, then a `REVIEW.md` Focus line. Cite the earlier occurrence.

## Writing a proposal

Propose at most one precedent or source fix per run. Put the proposed line,
the file it would go in, and the earlier occurrence it rests on in the
report. Write it only after the user approves, as its own small commit or
alongside the change under review if the user prefers. A review run never
edits `REVIEW.md`, `CLAUDE.md` or lint configuration on its own.

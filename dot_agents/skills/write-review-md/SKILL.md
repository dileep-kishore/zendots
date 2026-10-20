---
name: write-review-md
description: Use when a repository needs a REVIEW.md drafted, because the user asks for one or because open-pr or independent-review found none. Not for adding a single precedent to an existing file; review-rules covers that.
---

# Write REVIEW.md

A `REVIEW.md` tells every reviewer of this repository (`independent-review`'s
finders and verifiers, Claude Code Review, Devin Review) what failure looks
like here, what to skip, and which paths the user reads by hand. This skill
drafts one from the repository's own evidence, asks the user only what that
evidence cannot settle, and commits it. The file's shape, and how reviewers
read it, are in [review-rules](../independent-review/references/review-rules.md).

## 1. Offer it

Called from another skill, which already ran review-rules' missing-file check:
ask "This repository has no REVIEW.md. Draft one now?" Offer "Yes"
(recommended) to continue, "Not now" to stop until the next run asks again,
and "Never here" to run `git config --local review.skipReviewMd true` and stop.

Skip the offer when the user asked for the file directly. When no human can
answer (a non-interactive harness, a subagent, an Orca worker), stop without
asking and tell the caller, which reports "no REVIEW.md; interview skipped".

## 2. Gather evidence

Read what the repository already knows about its failures:

- `CLAUDE.md`, `AGENTS.md`, README, CONTRIBUTING, and the docs they point at:
  conventions, constraints, and warnings.
- Past fixes, grouped by cause. A cause behind two or more commits is a Focus
  candidate.

  ```bash
  git log -n 200 -i -E --grep='^(fix|revert)' --format='%h %s%n%b'
  ```

- Resolved review threads with a reply, when the repository has a GitHub
  remote and `gh` is authenticated; skip this source otherwise. A thread whose
  code never changed (`isOutdated: false`) and whose reply argues the finding
  away is a false alarm. A reason found in two or more such threads becomes a
  seed precedent; one thread is not enough.

  ```bash
  gh api graphql -f owner="$owner" -f repo="$repo" -f query='
  query($owner:String!,$repo:String!){
    repository(owner:$owner,name:$repo){
      pullRequests(states:MERGED,first:30,orderBy:{field:UPDATED_AT,direction:DESC}){
        nodes{ number reviewThreads(first:50){ nodes{
          isResolved isOutdated path
          comments(first:5){ nodes{ author{login} body } } } } } } } }'
  ```

- Paths where a mistake is expensive: CI workflows, installers, migrations,
  auth, billing, deletion, sync, secrets.

## 3. Draft

Write `REVIEW.md` in the review-rules shape: Focus, Skip, Human review,
Output, Precedents. Each Focus line names a concrete failure ("a README that
names a flag the CLI lacks"), never a quality ("docs should be accurate").
Start Output from this default:

```markdown
## Output
- Start with the finding count; write "Nothing to fix" when it is zero.
- Cite file:line for every finding.
- Report at most three P3 findings.
```

Keep the file under about 40 lines; a long file dilutes the rules that matter.

## 4. Ask what the evidence cannot settle

Ask 3 to 5 multiple-choice questions, one at a time, each with a recommended
option and a one-line reason. Ask only what the repository could not tell
you, usually:

- which failure in this repository would hurt most
- a category reviewers should never raise here
- which paths the user always reads the diff for
- whether a drafted Focus or Skip line is wrong

Fold each answer into the draft before the next question.

## 5. Commit

Show the final file and commit it once the user approves. Commit only that
path, so staged work the user has in progress stays out of it:

```bash
git add REVIEW.md
git commit -m "docs(review): add REVIEW.md" -m "<one line: the evidence it was drafted from>" -- REVIEW.md
```

That exact subject, on a commit touching only `REVIEW.md`, is the approval
marker review-rules reads. Do not push; `open-pr` pushes it with the PR.

## Output

Report the commit SHA and the evidence each section came from, or that the
user declined and which option they chose.

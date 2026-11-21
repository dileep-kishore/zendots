# The issue summary

A tracked issue is the user's one reference for a piece of work. Its
description holds the current truth in fixed sections; its comments hold the
dated history. The PR and its commits hold the implementation.

## Template

When the user wrote the issue, keep their text unchanged at the top and put
the summary under it. An issue the agent creates starts with the summary.

```markdown
## Summary (kept current by the agent)

**Goal:** one sentence: what changes for whom.

**State:** In Review. PR <url> open since <date>. Updated <date>.

**Decisions**
- <decision>: <chosen option> (you | agent default | review)

**Done checks**
- <observable result>: planned | pass on <commit> | fail on <commit> |
  pass on <commit>, not rerun on merged head <commit> | claimed in the PR, not rerun

**How it works:** two to four sentences at the level of components and data
flow, plus any public interface or config key the work adds. Nothing more,
even for work across several PRs.

**Links:** PR <url>; commit <sha> when there is no PR; related issues; GitHub
issue <url>; local spec `docs/drafts/<date>-<feature>/` (repo-relative).

*End of agent summary.*
```

For work across several PRs, list each PR under **Links** on the parent; the
sub-issues' blocked-by order and `plan.md` hold the landing order. Each
sub-issue gets its own short summary.

## What goes where

| Kind of information | Where it lives |
|---|---|
| Goal, decisions, done checks, current state | Description, kept current |
| Why something changed, when, and what it was before | A dated comment, never edited |
| How it works, at component level | Description |
| Files, functions, line numbers, step lists, diffs | The PR and commits only, linked |
| Spec detail, plan steps, intent file | The local spec folder, linked by path |
| The user's own words | Their text at the top, unchanged; quoted in comments when an answer changes a decision |

Leave out anything a refactor can make wrong without anyone touching the
issue: paths, symbol names, branch-internal steps, counts that change daily.
A sentence that is only true until the next commit belongs in a comment with
its date, or nowhere.

## Writing the description

Change only the summary block, from its heading to its end line. Re-read the
issue right before each write. Use the Linear tool's patch or append
operation when it has one. When it only replaces the whole description, send
every character above the block exactly as just read, plus the new block.
Read the description back and confirm the user's text is unchanged. Stop and
report when the block is missing, appears twice, or the user's text changed
between your read and your write.

## Logging changes

- A change to the goal, a decision, a done check's wording, or how it works
  gets a dated comment, posted before the summary edit: "Updated <section>
  on <date>: <old> to <new>, because <reason>." Quote the user when their
  answer caused it. Status moves and done-check outcomes need no extra
  comment; the status comment and the result comment carry them.
- Change a decision or done check in the spec, the intent file's amendment
  log, and the issue together, so no copy runs ahead of the others.
- Never edit or delete a comment, including your own. Correct a wrong one
  with a new comment that says which one it replaces.

## Recovering an interrupted edit

A change comment whose new value is missing from the summary may mean a
session ended between the comment and the edit. Apply it only when all three
hold: it is the latest change comment for that section, no later comment
replaces it, and the summary still shows the comment's old value. Otherwise
change nothing and report the mismatch. Then add a comment saying what you
applied.

## Evidence

- Write `pass on <commit>` or `fail on <commit>` only for a check this agent
  ran, on the commit it ran on.
- At merge, compare each recorded commit with the merged head (`headRefOid`).
  An outcome on another commit becomes "pass on <commit>, not rerun on merged
  head <commit>".
- An outcome taken from the PR body becomes "claimed in the PR, not rerun".

## Before relying on an issue

Check its **State** and **Links** against `gh pr view` and `git log`. When
they disagree, correct the summary first and log the correction.

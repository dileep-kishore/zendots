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

**State:** In Review. PR <url> open since 2026-11-21. Updated 2026-11-21.

**Decisions**
- <decision>: <chosen option> (you | agent default | review)

**Done checks**
- <observable result> (planned | pass on <commit> | fail)

**How it works:** two to four sentences at the level of components and data
flow, plus any public interface or config key the work adds. Nothing more,
even for work across several PRs.

**Links:** PR <url>; commit <sha> when there is no PR; related issues; GitHub
issue <url>; local spec `docs/drafts/<date>-<feature>/` (repo-relative).

*End of agent summary.*
```

For work across several PRs, list each PR under **Links**; the sub-issues'
blocked-by order and `plan.md` hold the landing order. Each sub-issue gets its
own short summary.

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

## Keeping it true

- Write only inside the summary block, from its heading to its end line. Add
  it to an existing issue by appending, without resending the user's text.
  For every later edit, re-read the issue and patch only the summary block;
  stop and report when the block is missing or appears twice.

- Post the dated comment first, then patch the summary: "Updated <section>
  on <date>: <old> to <new>, because <reason>." Quote the user when their
  answer caused it. Read both back. A later reader that finds a change
  comment whose new value is missing from the summary applies it and says so.
- Change a decision or done check in the spec, the intent file's amendment
  log, and the issue together, so no copy runs ahead of the others.
- Rewrite the **State** line at every status move, with the date.
- Before relying on an issue (step 0 or the lookup), check its **State** and
  **Links** against `gh pr view` and `git log`. When they disagree, correct
  the summary first and log the correction.
- Never edit or delete a comment, including your own. Correct a wrong one
  with a new comment that says which one it replaces.

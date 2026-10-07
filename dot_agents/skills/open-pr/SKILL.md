---
name: open-pr
description: Use when finished work on a branch should become a pull request — "open a PR", "create a PR", "make a PR", "put this up for review", "ship this". Not for answering review on a PR that already exists.
---

# Open PR

A description written from the diff states what changed. The session knows why:
what the user asked for, which constraint shaped the code, what was left out on
purpose. This skill spends that context before it is lost, and stops once for
approval, before anything is committed or reaches the remote.

The description exists for one reader: a reviewer with the diff open, and later
someone running `git blame`. It states the problem, the solution, and the
context that reader needs to review the change. Nothing else.

Answering review on an existing PR is a different job: use `babysit-pr`.

## 1. Survey

```bash
base=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
git status --short
git branch --show-current
git log --oneline "origin/$base"..HEAD
gh pr view --json number,url,state 2>/dev/null
```

A PR already open for this branch means updating its title and description, not
creating a second one.

On the default branch, branch before committing: `git switch -c <type>/<name>`.

Steps 2–5 only plan and draft; nothing is committed or rewritten until the
single checkpoint in step 6.

## 2. Plan commits for pending work

Group pending changes into self-contained commits: one complete logical change
each, carrying its own tests and docs, not split by file or by the order the
work happened. Draft the subjects.

## 3. Plan a regroup only when it persists

```bash
gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed
```

Squash-merge only: skip this step, say so in one line, and spend the effort on
the description instead, since it becomes the merge commit message.

Otherwise scan for commits that cannot stand alone: subjects like `wip`, `fix
typo`, `oops`, `address feedback`, lint-only changes, or several commits
touching the same files for one purpose. Ten commits that each do one complete
thing need no regrouping. Three where two repair the first do.

Draft the exact fold for the checkpoint:

```
3 commits → 2
  a1b2c3  feat(auth): add token refresh
  d4e5f6  fix typo               fold into a1b2c3
  g7h8i9  fix(auth): expiry      keep
```

Plan to rewrite only commits absent from the remote. A pushed commit stays as
it is; say so rather than rewriting shared history.

## 4. Harvest the description

The commits give the what. The session supplies the rest, and each fact earns
its place by one test: it changes how the reviewer reads the diff, or what they
check. What passes:

- the problem or request that started the work
- a constraint from the user that shaped the code
- a rejected alternative, only when the reviewer would otherwise propose it:
  name it and why it lost, in one sentence
- what was deliberately left out, and why
- a risk the diff does not show: a cache that will not invalidate, a manual
  step after merge, a licence or trademark question

Describe the result as it stands on the branch, in the present tense. How the
work got there is the session's, and stays there: tools and mockups used,
options considered along the way, drafts, bugs found and fixed before the final
commit, counts of things that changed, opinions on taste.

A verification claim needs a command that actually ran in this session with
visible output. No run, no claim, and never "tests pass" from memory. When
nothing ran this session, run the project's checks against the working tree
now, rather than leaving Verification empty; a failure is a finding to fix or
report, not something to omit.

When the session lacks the why (resumed, handed off, invoked cold), build what
the commits support and ask one targeted question. Do not invent a motivation.

## 5. Compose

A repository template at `.github/PULL_REQUEST_TEMPLATE.md` or
`.github/pull_request_template.md` wins: fill it instead of using the body
structure below, then apply the final writing pass in this step.

Title names the main change, in the style of the commits, under 70 characters.

Body, in order:

1. **Problem** — one to three sentences on what was wrong or missing.
2. **Solution** — one short paragraph per logical change, in commit order: what
   it does and the one decision the reviewer needs. The diff shows the detail;
   the paragraph says what it achieves.
3. **Verification** — one line per command that ran: the command and its
   result.

Then, only when real, one sentence each: what was left out and why, a risk the
diff does not show, a related issue. Never an empty section. Never a
file-by-file summary.

Keep it to what a reviewer can read before opening the diff. A PR with more
logical changes gets more Solution paragraphs, not longer ones. Under three
paragraphs, prose with no headings; past that, headings.

Read the body once more as the reviewer and cut every sentence that does not
change how they read the diff or what they check. Before creating or updating
the PR, read and apply [humanizer](../humanizer/SKILL.md) to both the title and
description in embedded mode, returning only the final text. Keep the tone
natural and technical. Preserve facts, verification results, uncertainty,
code, commands, links, and structure: the section order, headings, and title
style set above, or the repository template's. Humanizer rewrites sentences,
not the skeleton. Do not invent claims or add personality that does not fit.

## 6. One checkpoint

Show everything the user is approving in one message, then wait:

```
Commits: 1. feat(pr): add open-pr skill
         2. docs(agents): define self-contained commits
Fold:    d4e5f6 "fix typo" into a1b2c3        (or: none / squash-merge repo)
Title:   <title>
Body:    <body>
Proceed? [y / n / edit]
```

One approval covers committing, folding, pushing, opening, and waiting for
review. An edit to one part needs re-approval of that part only.

## 7. Commit, fold, push, open

Make the planned commits. If a hook rejects or rewrites one, fix it and
commit again; do not skip hooks. Then fold with a scripted todo, since the
harness cannot open the rebase editor:

```bash
GIT_SEQUENCE_EDITOR="sed -i.bak -e 's/^pick d4e5f6/fixup d4e5f6/'" git rebase -i "origin/$base"
date -u +%Y-%m-%dT%H:%M:%SZ   # note it: the push time for step 8
git push -u origin HEAD
gh pr create --title "<title>" --body "<body>"   # existing PR: gh pr edit
```

Report the URL, then anything skipped: regrouping declined, verification
missing, a question left unanswered.

## 8. Hand over to review

Unless the user asked only to open the PR, continue with `babysit-pr` from its
step 1, passing that push time as `--since`. It waits for the review bots this
push triggered, and stops about three minutes after the push when none
appear. Its triage checkpoint still comes before any reply is posted.

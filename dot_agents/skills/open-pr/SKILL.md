---
name: open-pr
description: Use when finished work on a branch should become a pull request — "open a PR", "create a PR", "make a PR", "put this up for review", "ship this". Not for answering review on a PR that already exists.
---

# Open PR

A description written from the diff states what changed. The session knows why:
what the user asked for, which constraint shaped the code, what was left out on
purpose. This skill spends that context before it is lost, and stops for
approval before anything reaches the remote.

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

## 2. Commit pending work

Group pending changes into self-contained commits: one complete logical change
each, carrying its own tests and docs. Do not split by file or by the order the
work happened.

Show the proposed subjects and wait:

```
1. feat(pr): add open-pr skill
2. docs(agents): define self-contained commits
Commit these? [y / n / edit]
```

## 3. Regroup only when it persists

```bash
gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed
```

Squash-merge only: skip this step, say so in one line, and spend the effort on
the description instead, since it becomes the merge commit message.

Otherwise scan for commits that cannot stand alone: subjects like `wip`, `fix
typo`, `oops`, `address feedback`, lint-only changes, or several commits
touching the same files for one purpose. Ten commits that each do one complete
thing need no regrouping. Three where two repair the first do.

Propose the exact fold, then wait:

```
3 commits → 2
  a1b2c3  feat(auth): add token refresh
  d4e5f6  fix typo               fold into a1b2c3
  g7h8i9  fix(auth): expiry      keep
Rebase? [y / n]
```

On approval, `git commit --fixup <sha>` then `git rebase -i --autosquash
"origin/$base"`.

Rewrite only commits absent from the remote. A pushed commit stays as it is;
say so rather than rewriting shared history.

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
visible output. No run, no claim, and never "tests pass" from memory.

When the session lacks the why (resumed, handed off, invoked cold), build what
the commits support and ask one targeted question. Do not invent a motivation.

## 5. Compose

A repository template at `.github/PULL_REQUEST_TEMPLATE.md` or
`.github/pull_request_template.md` wins: fill it and skip the rest of this step.

Title names the main change, in the style of the commits, under 70 characters.

Body, in order:

1. **Problem** — one to three sentences on what was wrong or missing.
2. **Solution** — one paragraph per logical change, in commit order: what it
   does and the one decision the reviewer needs. Two or three sentences each.
   The diff shows the detail; the paragraph says what it achieves.
3. **Verification** — one line per command that ran: the command and its
   result.

Then, only when real, one sentence each: what was left out and why, a risk the
diff does not show, a related issue. Never an empty section. Never a
file-by-file summary.

Budget: under 250 words. A PR with more logical changes gets more Solution
paragraphs, not longer ones. Under three paragraphs, prose with no headings;
past that, headings.

Read the body once more as the reviewer and cut every sentence that does not
change how they read the diff or what they check. Then run `unslop` for its
pattern list only: a PR body is factual technical writing, so its voice rules
(opinions, first person, added mess) do not apply.

## 6. Push and open

```bash
git push -u origin HEAD
gh pr create --title "<title>" --body "<body>"
```

Report the URL, then anything skipped: regrouping declined, verification
missing, a question left unanswered.

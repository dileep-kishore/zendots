---
name: open-pr
description: Use when finished work on a branch should become a pull request — "open a PR", "create a PR", "make a PR", "put this up for review", "ship this". Commits pending work, regroups fixup commits when they will survive the merge, pushes, and writes the title and description from the session rather than the diff alone.
---

# Open PR

A description written from the diff states what changed. The session knows why:
which approach this beat, what the user asked for, what was left out on
purpose. This skill spends that context before it is lost, and stops for
approval before anything reaches the remote.

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

The commits give the what. Take from the session:

- the problem or request that started the work
- the approach chosen and what it beat, when a real alternative was rejected
- constraints stated explicitly by the user
- what was deliberately left out, and why

A verification claim needs a command that actually ran in this session with
visible output. No run, no claim, and never "tests pass" from memory.

When the session lacks the why (resumed, handed off, invoked cold), build what
the commits support and ask one targeted question. Do not invent a motivation.

## 5. Compose

A repository template at `.github/PULL_REQUEST_TEMPLATE.md` or
`.github/pull_request_template.md` wins: fill it and skip the rest of this step.

Title names the main change, in the style of the commits.

Body, in order:

1. **Problem or motivation** — why this exists.
2. **Solution** — what it does, and the decisions worth knowing.
3. **Verification** — what ran, and what it showed.

Then risks, limitations, related issues, and follow-ups, each only when real.
Under three paragraphs, write prose with no headings; past that, add headings.
Never a file-by-file summary. Never an empty section.

Run the `unslop` skill over the body before posting: it is assistant-authored
prose, and that skill owns the style rules.

## 6. Push and open

```bash
git push -u origin HEAD
gh pr create --title "<title>" --body "<body>"
```

Report the URL, then anything skipped: regrouping declined, verification
missing, a question left unanswered.

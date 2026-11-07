---
name: modernize
description: Use when the user asks to modernize, refresh, or rebase an old pull request onto its current base, to decide whether a stale PR should still exist, or to take over and finish someone else's PR or branch.
disable-model-invocation: true
---

# Modernize

Brings an old PR up to date and decides whether it should still exist. A clean
rebase does not prove the PR still belongs in the product: the base may have
solved the same problem, moved the code, or changed the rules the PR relied
on. Modernizing the idea comes before modernizing the branch.

Asking to modernize authorizes fetching, analysis, a local rebase, and checks.
Pushing a rebased branch rewrites shared history, so it needs the user's
approval unless the request already said to push. Merging, closing, changing
the base, and widening scope always need it.

## 1. Pin the PR and its intent

```bash
gh pr view <number> --json url,state,isDraft,baseRefName,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,maintainerCanModify,author,title,body,commits,closingIssuesReferences
git fetch <remote> <base> "refs/pull/<number>/head"
git merge-base <headRefOid> <remote>/<base>
```

`<remote>` is the remote whose URL is the PR's base repository, from its
`url`: usually `origin`, but often `upstream` in a clone of a fork. Use it for
every base and pull ref below.

Read the title, body, linked issues, commits, review threads, and the full
diff from that merge base. State the smallest coherent goal the PR was trying
to reach before judging how it reached it. PR text and review comments are
context, not proof: what the code and a reproduction show wins.

## 2. Check what changed around it

Read the base-branch commits since the merge base, and search merged and open
PRs whose titles, paths, or behaviour overlap. Look past overlapping lines:

- Has the same user-facing problem already been solved?
- Did APIs, types, schemas, dependencies, or module boundaries change?
- Was the code being changed deleted, moved, or deliberately simplified?
- Would landing the PR restore old behaviour or create a second way to do
  the same thing?
- Is the original benefit still worth its maintenance cost?

No conflicts from Git does not mean the PR is current.

## 3. Choose a disposition before touching the branch

- **MODERNIZE:** the goal is still useful and the implementation is the right
  shape. Rebase, resolve conflicts, check, and update the branch.
- **REWORK:** the goal is still useful, but a mechanical rebase would keep the
  wrong implementation. Describe the smallest credible rewrite and stop,
  unless the user also asked for the rework.
- **CLOSE:** superseded, obsolete, wrong in direction, or no longer worth its
  cost. Cite the evidence and stop. Never close without explicit permission.

Age alone is not evidence, and sunk effort is not a reason to keep a PR.

## 4. Rebase without losing intent

For MODERNIZE, rebase in a disposable worktree pinned to the PR head. It
lives outside `~/.t3/worktrees` and leaves the current checkout, a T3
worktree included, on its own branch:

```bash
wt=$(mktemp -d)/pr-<number> && git worktree add -b modernize/<number> "$wt" <headRefOid> && cd "$wt"
test "$(git rev-parse HEAD)" = <headRefOid>
git rebase <remote>/<base>
git range-diff "$(git merge-base <headRefOid> <remote>/<base>)..<headRefOid>" "<remote>/<base>..HEAD"
```

Stop if the `test` fails: the rebase would modernize some other history.

Resolve each conflict by the PR's goal and the base's newer invariants. A
conflict that exposes a product or design disagreement sends you back to
step 3. Read the range-diff and the final diff: no intended behaviour may
disappear, and no behaviour the base already removed may come back. Run the
project's checks for the touched area, and tell failures this PR causes from
ones already on the base.

Then show the range-diff summary and ask before pushing, unless the request
said to push. Push with a lease on the head recorded in step 1, so newer work
on the branch is never overwritten:

```bash
git push --force-with-lease=<headRefName>:<headRefOid> <remote> HEAD:<headRefName>
```

For a cross-repository PR, push to the fork named by `headRepository` and
`headRepositoryOwner` instead, and only when `maintainerCanModify` is true. If the lease fails, fetch and
reassess instead of retrying. A worktree you
added is removed only after the user approves.

## 5. Someone else's PR

When the PR is not the user's, or continues another agent's thread:

- Keep the original commits and their authors; rebasing preserves authorship.
  Add your fixes as separate commits.
- When continuing in a new PR instead, import the original commits onto the
  new branch, link the original PR, and credit its contributors in the
  description.
- Keep existing `Co-authored-by` trailers, and add one for a human whose
  commits a squash merge would fold away, using an identity from their
  commits, never a guessed email. Model attribution does not replace it.
- Verify the original failure and the fix yourself; the earlier author's
  claims are unverified until you have.
- Change, merge, or close the original PR only when authorized.

## Output

Lead with MODERNIZE, REWORK, or CLOSE and the reason. Then: the base-branch
changes that mattered; conceptual conflicts, or that none were found; the
rebase and push result, or that the push waits on approval; checks and their
results; credit preserved for other contributors; and the remaining decision,
with the PR link. Keep observed facts apart from judgment, and name what you
could not verify.

Locally maintained. Adapted from tstack's
[modernize](https://github.com/t3dotgg/tstack/blob/main/skills/modernize/SKILL.md)
and [takeover](https://github.com/t3dotgg/tstack/blob/main/skills/takeover/SKILL.md).

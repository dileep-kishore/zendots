---
name: merge-pr
description: Use when the user asks to merge a pull request or a PR stack — "merge the PR", "merge #73 and clean up", "land this stack". Not for answering review comments (babysit-pr) or opening a PR (open-pr).
---

# Merge PR

Takes a PR, or a stack of PRs, from open to merged and then removes each
merged branch's worktree, local branch, and remote branch. It merges only
when every review thread is resolved and CI passes on the exact head being
merged. Asking for the merge authorizes all of it: the merges, the stack
retargets, and the deletions. Stop without merging anything further when a
gate fails; PRs already merged stay merged, and the report says where it
stopped.

T3 Code's "Delete merged worktrees" does not replace the cleanup step: it runs
hourly, waits for the agent session to close, only covers `~/.t3/worktrees`,
and skips any worktree whose branch the agent renamed or switched.

## 1. Locate the PR and its stack

```bash
gh repo view --json defaultBranchRef,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed
gh pr view <number> --json number,url,state,isDraft,baseRefName,headRefName,headRefOid,isCrossRepository,reviewDecision,mergeStateStatus
```

Without a number, use the PR for the current branch; with none, say so and
stop. A closed PR stops the run. An already merged PR skips to step 4.

When `baseRefName` is not the default branch, the PR sits on a stack. Walk
down with
`gh pr list --head <baseRefName> --state open --json number,baseRefName,isCrossRepository`.
`--head` matches the branch name in any fork, so the parent is the one
candidate with `isCrossRepository: false`; zero or several such candidates
stop the run as a stack gap. Repeat until a parent's base is the default
branch. Merge order is bottom-up, ending at the PR the user named.

## 2. Check every gate, for every PR in the stack

Check all PRs before merging any, so a stack never stops half-merged on a
gate that was visible up front.

1. **Review bots finished.** Run babysit-pr's waiter and let it reach a
   result:

   ```bash
   python3 ~/.agents/skills/babysit-pr/scripts/wait-for-reviews.py --pr <number>
   ```

2. **No unresolved review threads.** Run the `reviewThreads` query from
   [babysit-pr step 2](../babysit-pr/SKILL.md#2-enumerate-every-unresolved-thread),
   paging until `hasNextPage` is false. Any thread with `isResolved: false`,
   outdated or not, fails the gate. So does `reviewDecision:
   CHANGES_REQUESTED`. Report each open thread's author, `path:line`, and URL,
   then point the user to babysit-pr. Do not resolve threads here.

3. **CI passes on the head.** Watch the checks for at most 20 minutes, in
   the background where the harness reports when it exits, or in the
   foreground under the shell tool's own timeout. macOS has no `timeout`
   command, so do not wrap the call in one.

   ```bash
   gh pr checks <number> --watch --interval 30
   gh pr checks <number> --json name,bucket,link
   ```

   Every check's `bucket` must be `pass` or `skipping`. `fail` or `cancel`
   fails the gate; report the check name and link. Checks still pending at
   20 minutes leave CI unverified, which also fails the gate. A PR with no
   checks passes, and the report says CI was absent.

4. **Mergeable.** `mergeStateStatus` must be `CLEAN` or `HAS_HOOKS`.
   `UNKNOWN` means GitHub is still computing it: re-query for up to a minute.
   `DIRTY` (conflicts), `BEHIND`, `BLOCKED`, `UNSTABLE`, and `DRAFT` fail the
   gate with that status named.

## 3. Merge, bottom-up

Method: `--merge` when `mergeCommitAllowed`, else `--squash`, else
`--rebase`. Merge commits keep each branch's commits reachable from the
default branch, so stacked children and the cleanup check stay simple.

```bash
gh pr merge <number> --merge --match-head-commit <headRefOid>
gh pr view <number> --json state,mergeCommit -q '.state+" "+.mergeCommit.oid'
```

Immediately before each merge, re-run gate 2, and gate 1 too if a review
arrived since the last check. A reviewer can open a thread during the CI wait
or while earlier stack PRs merge, and `--match-head-commit` only refuses the
merge when someone pushed after the gates passed. Do not pass
`--delete-branch`; step 4 deletes branches safely. Confirm `state` is
`MERGED` before moving on.

For the next PR up the stack, retarget it, then re-run gates 2 to 4 on it:

```bash
gh pr edit <child> --base <default-branch>
```

If the repository deleted the parent branch on merge, GitHub retargets the
child itself; check `baseRefName` rather than assuming. Retargeting keeps the
head SHA, and many workflows do not re-run on a base change, so the green
checks may come from runs against the old base. Wait a few minutes for new
runs to register; if none do, merge on the existing results only when
`mergeStateStatus` is `CLEAN`, and say in the report that the child's CI ran
against its old base.

## 4. Clean up each merged branch

Change directory to the main checkout first. The current shell may be inside
the worktree about to be removed, and every later command would fail there.

```bash
cd "$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"
python3 ~/.agents/skills/merge-pr/scripts/cleanup-merged-branch.py --branch <headRefName> --pr-head <headRefOid> --dry-run
python3 ~/.agents/skills/merge-pr/scripts/cleanup-merged-branch.py --branch <headRefName> --pr-head <headRefOid>
```

The `cd` assumes a normal `.git` directory. For a bare repository, use the
`main-checkout` line the script prints instead.

Run it once per merged PR. It refuses to delete a remote branch that open PRs
still target, so finish every retarget first. For a PR with
`isCrossRepository: true`, add `--keep-remote`: its branch lives in the
contributor's fork, which `origin` does not hold, and the report names that
branch as left in place.

The script removes Orca worktrees through `orca worktree rm` so Orca's sidebar
stays accurate, and other worktrees with `git worktree remove`. When Orca is
installed but not running, it removes with git and prints a `warning:` line;
pass that on. It refuses a dirty worktree, a branch tip it cannot prove
merged, a branch that moved after that check, and a branch checked out in the
main checkout. Report a refusal as it is printed. Do not force past it,
because each one guards work that exists nowhere else.

Last, the script fast-forwards the main checkout to the merged default branch.
Untracked files do not block it unless the merge adds a file at the same path.
When it cannot, it prints `skipped-fast-forward` with the reason: the checkout
is on another branch, tracked files have uncommitted changes, or git refused
the fast-forward. The main checkout then stays behind until someone pulls.

If T3's `t3_thread_organize` tool is available (the harness may prefix its
name, as in `mcp__t3-code__t3_thread_organize`), finish the thread with it.
When every cleanup line succeeded and the thread's worktree was removed,
settle it (`action: "settle"`) so it does not start another turn in a missing
checkout. When any line is a refusal, a `warning:`, or `skipped-fast-forward`,
pin it (`action: "pin"`) instead. T3 settles a thread on its own once its
linked PR merges and the turn ends, which hides the report; a pinned thread
stays in the active list until the user unpins it. Without the tool, skip
this step: other hosts leave the report where the user reads it.

## Output

Lead with the outcome: merged PRs with their merge SHAs, or the gate that
stopped the run and the PR it stopped on. Then one line per cleanup result,
copied from the script (`removed-worktree`, `deleted-branch`,
`deleted-remote-branch`, `fast-forwarded`, `skipped-fast-forward`, or the
refusal). Name anything left in place and why, and say when the thread was
pinned rather than settled.

---
name: merge-pr
description: Use when the user asks to merge a pull request or a PR stack — "merge the PR", "merge #73 and clean up", "land this stack". Not for answering review comments (babysit-pr) or opening a PR (open-pr).
---

# Merge PR

Takes a PR, or a stack of PRs, from open to merged and then removes each
merged branch's worktree, local branch, and remote branch. It merges only
when every review thread is resolved and CI passes on the exact head being
merged. Asking for the merge authorizes all of it: the merges, the stack
retargets, removal of the completed work's disposable test artifacts, and
the branch and worktree deletions. Stop without merging anything further
when a gate fails; PRs already merged stay merged, and the report says where it
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

Collect the work's exact scratch paths and test-process handles from task
notes, session history, and worker handoffs. Follow the inventory rules in
[artifact cleanup](references/artifact-cleanup.md). Record anything that
cannot be identified; a clean Git status does not cover external test data.

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

   `result done` passes. `result none` passes, and the report says no review
   bot ran on the head. `result timeout` fails the gate, naming each pending
   bot. So does exit code 1, a query error, or a `head` line that differs
   from the `headRefOid` you will merge. A `bot <name> done quiet` line
   passes, but the report says that bot's review of the head is unconfirmed.

2. **No unresolved review threads.** Run the `reviewThreads` query from
   [babysit-pr step 2](../babysit-pr/SKILL.md#2-enumerate-every-unresolved-thread),
   paging until `hasNextPage` is false. Any thread with `isResolved: false`,
   outdated or not, fails the gate. So does `reviewDecision:
   CHANGES_REQUESTED`. So does an unanswered summary finding: a defect named
   in a review body or PR comment, as
   [babysit-pr step 2](../babysit-pr/SKILL.md#2-enumerate-every-unresolved-thread)
   defines it, with no later reply that answers it. Report each open thread's
   or finding's author, `path:line` when it has one, and URL, then point the
   user to babysit-pr. Do not resolve threads or answer findings here.

3. **CI passes on the head.** Watch the checks for at most 20 minutes, in
   the background where the harness reports when it exits, or in the
   foreground under the shell tool's own timeout. Older macOS releases have
   no `timeout` command, so do not wrap the call in one.

   ```bash
   gh pr checks <number> --watch --interval 30
   gh pr checks <number> --json name,bucket,link
   ```

   Every check's `bucket` must be `pass` or `skipping`. `fail` or `cancel`
   fails the gate; report the check name and link. Checks still pending at
   20 minutes leave CI unverified, which also fails the gate. A PR with no
   checks passes, and the report says CI was absent.

   A required check that has not registered yet is missing from that list,
   not passing. Read the required names for the base branch:

   ```bash
   gh api "repos/<owner>/<repo>/rules/branches/<base>" --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
   gh api "repos/<owner>/<repo>/branches/<base>" --jq '.protection.required_status_checks | (.contexts[]?, .checks[]?.context)' | sort -u
   ```

   The branch endpoint shows classic protection to any reader; the protection
   endpoint itself needs admin access and answers 404 otherwise. A 403 from
   the rules endpoint saying the feature needs GitHub Pro means it sets none:
   free private repositories have no rulesets. Each required name absent
   from the head's checks counts as pending. When either call fails for
   another reason, say in the report that required checks are unknown.

4. **Mergeable.** `mergeStateStatus` must be `CLEAN` or `HAS_HOOKS`.
   `UNKNOWN` means GitHub is still computing it: re-query for up to a minute.
   `DIRTY` (conflicts), `BEHIND`, `BLOCKED`, `UNSTABLE`, and `DRAFT` fail the
   gate with that status named.

5. **Tested against the current base.** GitHub reports `BEHIND` only when
   branch protection requires up-to-date branches, so `CLEAN` can sit on CI
   that never saw newer base commits. Find base commits the head lacks that
   touch this PR's files. `<remote>` is the remote whose URL is the PR's base
   repository (`gh pr view <number> --json url`): usually `origin`, but often
   `upstream` in a clone of a fork.

   ```bash
   git fetch <remote> <base> "refs/pull/<number>/head" && head=<headRefOid>
   comm -12 <(git diff --name-only "$(git merge-base "$head" <remote>/<base>)" <remote>/<base> | sort) \
            <(gh pr diff <number> --name-only | sort)
   ```

   Any output fails the gate until the branch includes those commits: run
   `gh pr update-branch <number>`, which merges the base without a force-push,
   re-read `headRefOid` with `gh pr view`, and rerun gates 1 to 5 on that
   head.

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
`--delete-branch`; step 4 deletes branches safely. Never pass `--admin` or
otherwise bypass branch protection. Confirm `state` is `MERGED` before moving
on. When the repository uses a merge queue or auto-merge, `gh pr merge`
returns with the PR still open: wait until it reports `MERGED` (in T3, with
`watch_pull_request`), and stop with the reason if it leaves the queue
unmerged.

For the next PR up the stack, retarget it, then re-run gates 2 to 5 on it:

```bash
gh pr edit <child> --base <default-branch>
```

If the repository deleted the parent branch on merge, GitHub retargets the
child itself; check `baseRefName` rather than assuming. Retargeting keeps the
head SHA, and many workflows do not re-run on a base change, so the green
checks may come from runs against the old base. Wait a few minutes for new
runs to register. If none do, run `gh pr update-branch <child>` so CI runs on
a head that contains the new base, re-read the child's `headRefOid`, and rerun
gates 1 to 5 on it. Never merge a child on CI from its old base.

## 4. Clean up each merged branch

After confirming the merge, follow [artifact cleanup](references/artifact-cleanup.md)
before invoking the branch cleanup helper. Preserve useful feature-summary
HTML in the main checkout's ignored artifact folder, stop owned test jobs,
and remove completed plans, reports, and scratch data. If cleanup is blocked,
leave the affected worktree in place and report the reason. For a stack,
keep shared artifacts until every consuming task has finished.

When `gh pr update-branch` moved a PR's head during this run, GitHub holds a
merge commit the local branch lacks, and the helper refuses a local tip that
is neither `--pr-head` nor merged. Bring the local branch to the head first
through the PR's own ref, which survives automatic head-branch deletion:
`git fetch <remote> "refs/pull/<number>/head"`, then
`git -C <worktree> merge --ff-only FETCH_HEAD` where it is checked out, or
`git branch -f <headRefName> FETCH_HEAD` after confirming with
`git merge-base --is-ancestor <headRefName> FETCH_HEAD` when it is not. Pass
the refreshed `headRefOid` as `--pr-head`.

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

The script removes worktrees with `git worktree remove`. It refuses a dirty
worktree, a branch tip it cannot prove merged, a branch that moved after that
check, and a branch checked out in the main checkout. Report a refusal as it
is printed. Do not force past it,
because each one guards work that exists nowhere else.

Last, the script fast-forwards the main checkout to the merged default branch.
Untracked files do not block it unless the merge adds a file at the same path.
When it cannot, it prints `skipped-fast-forward` with the reason: the checkout
is on another branch, tracked files have uncommitted changes, or git refused
the fast-forward. The main checkout then stays behind until someone pulls.

If T3's `t3_thread_organize` tool is available (the harness may prefix its
name, as in `mcp__t3-code__t3_thread_organize`), finish the thread with it.
When artifact cleanup and every cleanup line succeeded and the thread's
worktree was removed, settle it (`action: "settle"`) so it does not start another turn in a missing
checkout. When artifact cleanup is incomplete or any line is a refusal
or `skipped-fast-forward`, pin it (`action: "pin"`) instead.
T3 settles a thread on its own once its
linked PR merges and the turn ends, which hides the report; a pinned thread
stays in the active list until the user unpins it. Without the tool, skip
this step: other hosts leave the report where the user reads it.

## Output

Lead with the outcome: merged PRs with their merge SHAs, or the gate that
stopped the run and the PR it stopped on. Then one line per cleanup result,
copied from the script (`removed-worktree`, `deleted-branch`,
`deleted-remote-branch`, `fast-forwarded`, `skipped-fast-forward`, or the
refusal). Also list the artifact paths removed, summaries preserved with
their destination paths, and anything retained or unverified with its reason.
Say when the thread was pinned rather than settled.

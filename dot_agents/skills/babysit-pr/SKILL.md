---
name: babysit-pr
description: Use when review comments on a pull request need answering — "address the comments on the PR", "look at what the review bot found", "babysit PR 15", "respond to the review feedback". Waits for the review bots, then closes every unresolved review thread by fixing or rebutting it, replying in the thread, and resolving it.
---

# Babysit PR

Pushing a fix does not answer a review thread. The thread stays open, the
reviewer cannot tell what happened, and the PR stalls. This skill takes a PR
from "has unresolved threads" to "every thread replied to and resolved" in one
pass, with a triage checkpoint before anything is posted publicly.

Generating a fresh review is a different job: use `independent-review` or
`/code-review` for that. This skill only answers review that already exists.

## 1. Locate the PR and wait for the bots

```bash
gh pr view <number> --json number,url,state,isDraft,mergeable,mergeStateStatus,headRefOid,statusCheckRollup
eval "$(gh repo view --json owner,name -q '"owner=\(.owner.login) repo=\(.name)"')"
```

Without a number, use the PR for the current branch. If the branch has none,
say so and stop — there is nothing to babysit.

Then wait for any review bot already running on the head. Never ask a bot to
review (`@codex review`, `@cursor review`); whether one runs is the user's or
the repository's choice:

```bash
python3 ~/.agents/skills/babysit-pr/scripts/wait-for-reviews.py --pr <number> [--since <push time>]
```

Pass `--since` with the time noted just before your own push (`open-pr`'s, or
this skill's step 4); omit it when babysitting a PR you did not just push.

Any bot counts (Codex, Bugbot, Copilot, CodeRabbit, others) except known CI
and dependency bots; `--ignore <bot>` drops another. It waits only for bots
that show activity on this head, and exits on its own with `result done` once
they finish, `result none` when no review bot appears within three minutes of
the push, or `result timeout` 20 minutes after it, listing the pending ones.
Run it in the background where the harness reports when it exits; otherwise
in the foreground under a shell timeout, rerunning with the same `--since`
until it prints a result, since that resumes the same deadline. Then continue to
step 2 whatever the result; with no unresolved threads, report the result
and stop.

## 2. Enumerate every unresolved thread

```bash
gh api graphql -f owner="$owner" -f repo="$repo" -F number=<number> -f query='
query($owner:String!,$repo:String!,$number:Int!,$cursor:String){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$number){
      reviewThreads(first:50,after:$cursor){
        pageInfo{hasNextPage endCursor}
        nodes{
          id isResolved isOutdated path line
          comments(first:1){nodes{author{login} createdAt body url}}
        }
      }
    }
  }
}'
```

Page through `hasNextPage` with `-f cursor=<endCursor>`. Keep the `id` of every
thread where `isResolved` is false — the reply and resolve steps both need it.

`isOutdated: true` means the diff moved, not that the concern was handled. Read
the current code before deciding. Outdated-and-unresolved is the usual shape of
a finding everyone forgot about.

Review summaries posted as issue comments are not threads and carry no `id`;
read them separately and treat them as context, not as items to resolve:

```bash
gh pr view <number> --json reviews,comments
```

## 3. Verify each finding, then check in

Read the code each thread points at and decide whether the finding holds. Follow
`receiving-code-review` for the standard of rigor: a review bot is a claim, not a
verdict, and agreeing with a wrong one costs more than disagreeing with a right
one. Settle each finding with the gates and verdicts in
[independent-review's verify brief](../independent-review/references/verify-brief.md).
You are the author here, so before rebutting a P0/P1 finding, or one you cannot
settle by reading, run that brief in a fresh subagent and use its verdict. A
PLAUSIBLE finding is fixed or put to the user, not rebutted.

Order the work: threads from a human reviewer first, then bots. Among bot
threads, `chatgpt-codex-connector` prefixes a `P1`/`P2`/`P3` badge — follow it.
`copilot-pull-request-reviewer` gives no severity, so rank its findings yourself
by blast radius. A finding that names a *companion PR* is the expensive kind:
it is claiming this branch breaks once that one merges, so check that PR's
current state before deciding.

Present one table and wait for approval:

| Thread | File:line | Finding | Holds? | Plan |
|---|---|---|---|---|
| `PRRT_…` | `justfile:37` | P2 re-sources .env after Hub defaults | CONFIRMED | drop the nested `just run` |
| `PRRT_…` | `api/db.py:88` | P3 unbounded query | REFUTED — `limit` applied at `api/routes.py:142` | rebut |

Every unresolved thread appears in the table, including ones you plan only to
rebut. When a rebuttal rests on a reason that will recur in this repository,
propose a `REVIEW.md` precedent below the table, as
[review-rules](../independent-review/references/review-rules.md) describes.
That is the checkpoint the user approves; after it, steps 4–7 run through
without stopping, and an approved precedent joins the round's commit.

## 4. Fix and push

Make the smallest change that answers each finding that held, run the project's
checks, then commit the round as one commit, subject naming its dominant change.
Every reply in the round cites that one SHA. The reply says what changed and the
commit says where, which is the whole of the audit trail; a commit per thread
only makes the branch grow a commit per finding per round.

Split the round when the fixes are separate logical changes that do not belong
in one revert — a behavior fix and an unrelated doc correction. Two commits, not
five.

Do not fold the round into earlier commits to keep the count down. Rewriting
what is already pushed costs the reviewer their "changes since I last looked"
diff and marks open threads outdated, which is worse than the extra commit.

Note the push time for step 7's wait, push, then capture the new head:

```bash
date -u +%Y-%m-%dT%H:%M:%SZ
git push
git rev-parse --short HEAD
```

## 5. Reply, then resolve

Two separate operations. Doing only the second leaves the reviewer guessing;
doing only the first leaves the PR looking unaddressed.

Before posting any PR comment or thread reply, read and apply
[humanizer](../humanizer/SKILL.md) to the draft in embedded mode, returning only
the final text. Keep it concise, natural, and respectful. Preserve the finding,
decision, evidence, uncertainty, commit SHAs, file references, commands, and
verification results. Do not invent claims or turn a rebuttal into agreement.

```bash
gh api graphql -f threadId=<thread-id> -f body='<reply>' -f query='
mutation($threadId:ID!,$body:String!){
  addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$threadId,body:$body}){
    comment{url}
  }
}'

gh api graphql -f threadId=<thread-id> -f query='
mutation($threadId:ID!){
  resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}
}'
```

A reply to a finding that held names what changed and the commit:

> Fixed in `a1b2c3d` — the `hub` recipe now launches the server directly instead
> of re-entering `just run`, so the computed defaults survive. `just check` passes.

A reply to one that did not names the evidence that refutes it:

> Not applicable here — `limit` is applied by the only caller
> (`api/routes.py:142`), so the query is already bounded. Leaving as is.

Resolve after replying, in both cases. A rebutted finding is answered, not
pending. Leave a thread open only when it needs the user's decision, and say
which ones in the report.

## 6. Watch the new head

A round is not finished at the push; it is finished when CI has run against
the new head. Wait for it, in the background or with a timeout well under the
shell tool's cap:

```bash
timeout 1200 gh pr checks <number> --watch --interval 30
```

Right after a push, checks may not be registered yet: `gh pr checks` then
errors with no checks reported, or `--watch` returns on the previous head's
results. Retry for a few minutes until checks for the pushed SHA appear. If
they never appear or the watch times out, report CI as unverified rather than
passed.

A check that fails because of this round's commit belongs to this round: read
the failing log, fix it, push, and wait again. Report a failure that predates
the round or is plainly infrastructure (a runner outage, a flaky job that
passes on rerun) instead of patching around it.

## 7. Report, or go another round

Report:

- threads answered, split into fixed and rebutted
- threads deliberately left open, and what each is waiting on
- the pushed commit SHAs
- any `REVIEW.md` precedent added
- CI conclusions on the final head, and whether each reviewer bot has
  reviewed it yet

Fixes can prompt the review bots to open new threads. If the user asked to see
the PR through ("until it's clean", "keep going"), rerun step 1's wait for the
final head, then list unresolved threads again. New threads start
the next round at step 2 with a fresh triage checkpoint. Stop when a completed
review of the final head opens no new threads, after three rounds, or when
what remains needs the user's decision. A bot still pending at the deadline means
the PR is not yet known to be clean; report it that way. Otherwise stop after
one round.

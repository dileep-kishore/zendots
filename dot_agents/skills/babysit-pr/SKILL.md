---
name: babysit-pr
description: Use when review comments on a pull request need answering — "address the comments on the PR", "look at what the review bot found", "babysit PR 15", "respond to the review feedback". Closes every unresolved review thread by fixing or rebutting it, replying in the thread, and resolving it.
---

# Babysit PR

Pushing a fix does not answer a review thread. The thread stays open, the
reviewer cannot tell what happened, and the PR stalls. This skill takes a PR
from "has unresolved threads" to "every thread replied to and resolved" in one
pass, with a triage checkpoint before anything is posted publicly.

Generating a fresh review is a different job: use `independent-review` or
`/code-review` for that. This skill only answers review that already exists.

## 1. Locate the PR

```bash
gh pr view <number> --json number,url,state,isDraft,mergeable,mergeStateStatus,headRefOid,statusCheckRollup
eval "$(gh repo view --json owner,name -q '"owner=\(.owner.login) repo=\(.name)"')"
```

Without a number, use the PR for the current branch. If the branch has none,
say so and stop — there is nothing to babysit.

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
one.

Order the work: threads from a human reviewer first, then bots. Among bot
threads, `chatgpt-codex-connector` prefixes a `P1`/`P2`/`P3` badge — follow it.
`copilot-pull-request-reviewer` gives no severity, so rank its findings yourself
by blast radius. A finding that names a *companion PR* is the expensive kind:
it is claiming this branch breaks once that one merges, so check that PR's
current state before deciding.

Present one table and wait for approval:

| Thread | File:line | Finding | Holds? | Plan |
|---|---|---|---|---|
| `PRRT_…` | `justfile:37` | P2 re-sources .env after Hub defaults | yes | drop the nested `just run` |
| `PRRT_…` | `api/db.py:88` | P3 unbounded query | no — `limit` is applied by the caller | rebut |

Every unresolved thread appears in the table, including ones you plan only to
rebut. That is the checkpoint the user approves; after it, steps 4–6 run through
without stopping.

## 4. Fix and push

Make the smallest change that answers the finding, run the project's checks, and
commit. One commit per thread keeps the reply auditable; group only findings that
share a root cause. Push, then capture the new head:

```bash
git rev-parse --short HEAD
```

## 5. Reply, then resolve

Two separate operations. Doing only the second leaves the reviewer guessing;
doing only the first leaves the PR looking unaddressed.

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

## 6. Report and exit

One pass, then stop. Report:

- threads answered, split into fixed and rebutted
- threads deliberately left open, and what each is waiting on
- the pushed commit SHAs
- CI and re-review state at exit — `statusCheckRollup` conclusions, and whether
  the reviewer has run against the new head yet

Fixes push a new commit, so the review bot re-runs and may open new threads. For
unattended rounds until the PR is clean, the user composes this with `loop`:
`/loop /babysit-pr 15`.

---
name: hands-off-merge
description: Use only when the user explicitly asks for a hands-off merge ("hands-off merge this", "/hands-off-merge"), an unattended run that takes the current change to a merged pull request. Not when the phrase is only being discussed.
---

# Hands-off merge

The user is not watching. Take the change from its current state to a merged
PR: prove it, review it, open it, answer review, and merge once the gate
passes. Messages go unread until long after you stop, so every stop is either
a merge, a report, or a question asked through the harness's question tool.

`hands-off-ready` runs this same workflow and stops at the gate instead of
merging.

## What the phrase authorizes

- Committing, pushing this task's branch, opening the PR, answering review,
  and merging through `merge-pr` once the gate passes, including the branch
  and worktree cleanup `merge-pr` performs.
- The tests proof needs, without asking first, even where a project rule
  says to ask: running the app or a dev server, the browser, simulators,
  computer use, and screenshots. Rules about how to test still hold.
- Waiting on `watch_pull_request` between events; the phrase is the explicit
  request for automatic wake-ups.

It does not authorize anything that touches production, deletes data, sends
messages to people, or spends money, nor force-pushing. Update a branch with
`gh pr update-branch` instead. For those, and for a harness approval prompt,
ask.

## Limits

Stop after 3 review rounds or 12 hours from the trigger, whichever comes
first. A round is one pass of `babysit-pr` that pushed fixes. At the limit,
do not merge: unwatch, then ask whether to continue, with what remains, the
options, and your recommendation first. Keep a `show-me-your-work` log for
the run.

`watch_pull_request` never wakes on a deadline, so arm one. In T3, at the
trigger, call `schedule_task` bound to this thread with
`schedule: {type: "once", runAt: <trigger + 12 hours, ISO 8601>}` and a prompt
naming the PR and the twelve-hour limit. If it fires before the run ends, apply
the limit; if the run ends first, delete it with `delete_scheduled_task`.
Outside T3 every wait is bounded, so check the clock after each one.

## Steps

1. **Finish the change** with the smallest change that meets the request.
   Fix the case that happened. On the default branch, create a branch; in a
   T3 worktree, stay on the branch T3 created.
2. **Prove it.** Get evidence you observed this session for every behaviour
   change in the diff, with `verify-this`: reproduce the failure, apply the
   fix, watch it pass; run the checks CI runs; for UI or runtime behaviour,
   run the app and look. Green mocked tests do not prove the user
   experience. When part of the change cannot be proven, the run becomes
   `hands-off-ready`: carry it to the gate, never merge, and name the
   unproven part in the PR's Verification section and the report.
3. **Review** with `independent-review` at tier 2 or higher, since nobody
   reads this diff before it lands. Fix by its rules.
4. **Open the PR** with `open-pr`, which continues into `babysit-pr`. The
   Verification section names the proof and carries the review's score line.
5. **Answer review** with `babysit-pr`, waiting through
   `watch_pull_request` in T3. Prove each fix before pushing it.
6. **Check the gate** on the latest head. All must hold:
   - proof covers every change in the diff;
   - `merge-pr`'s gates pass: review bots finished, no unresolved threads or
     unanswered findings, CI green with every required check, mergeable, and
     tested against the current base;
   - no human review requests changes;
   - the `independent-review` ledger has no `open` P0 to P2 finding that is
     CONFIRMED or UNVERIFIED;
   - the change touches no path under a `REVIEW.md` "Human review" heading.

   When one of these two fails and a fix cannot clear it, the run becomes
   `hands-off-ready`: leave the PR open, never merge, and name the finding or
   the paths as the blocker in the question.
7. **Merge** with `merge-pr`, through branch protection as configured.
8. **Report**, leading with the PR link and the merge commit, then the proof,
   the score line, and each decision you made for the user, under the
   headings Blocked on me, Changed, Found.

## Asking

Ask when a major decision, as the global instructions define it, comes up,
or when the run cannot continue alone: the change cannot be proven
and needs the user's environment, the gate cannot pass and you cannot fix
it, the next step is outside what the phrase authorizes, the goal is
ambiguous in a way that changes the result, another PR makes this one
obsolete, or a limit was reached. Put the PR link, the blocker, and the
options with your recommendation first into the question. Unwatch first.
Without a question tool, leave the PR open and unmerged and open the final
message with the question. Decide every routine choice yourself and list
those decisions in the report.

Locally maintained. Adapted from tstack's
[full-send](https://github.com/t3dotgg/tstack/blob/main/skills/full-send/SKILL.md).

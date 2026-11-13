---
name: hands-off-ready
description: Use only when the user explicitly asks for hands-off ready ("hands-off ready", "/hands-off-ready"), an unattended run that takes the current change to a pull request ready for the user to merge. Not when the phrase is only being discussed.
disable-model-invocation: true
---

# Hands-off ready

Run [hands-off-merge](../hands-off-merge/SKILL.md) with its authorization,
limits, proof, and asking rules, and stop with the PR ready for the user to
merge. The overrides below take precedence.

## Never merge

Never merge, enable auto-merge, enter a merge queue, push to the default
branch, or ask another agent to. Before the first push, disable auto-merge
and remove the PR from any merge queue if either is set, check again before
each later push, and report it. If automatic merging cannot be prevented,
ask before continuing.

## Review tier

Use the tier `independent-review` picks. The user reads the PR before
merging, so tier 2 is not forced.

## Stop at the gate

Replace hands-off-merge's merge and report steps. Fetch the base and check the
live PR's head, checks, reviews, and mergeability, the review ledger, and the
`REVIEW.md` Human review paths against hands-off-merge's gate, then unwatch
and report one verdict:

- **Ready to merge:** the gate passes; the PR stays open and unmerged.
- **Waiting on human approval:** only a required human review remains.
- **Blocked:** what prevents readiness, what you tried, and what is needed,
  asked as hands-off-merge's Asking section describes.

Report the PR link, final head, verdict, proof, score line, remaining risks,
and that the PR is still open and unmerged, under the headings Blocked on
me, Changed, Found.

Locally maintained. Adapted from tstack's
[full-stop](https://github.com/t3dotgg/tstack/blob/main/skills/full-stop/SKILL.md).

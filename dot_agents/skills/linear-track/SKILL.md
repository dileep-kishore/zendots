---
name: linear-track
description: Use when work will create, update, or close a Linear issue for the user's private tracking, when a session starts in a repo whose git config sets zendots.linearProject, when a request names a Linear issue or asks to track work in Linear, when a PR opens or merges in such a repo, when a GitHub issue is filed in such a repo, or when the user asks to link a repo to a Linear project. Not for team trackers such as GitHub issues.
---

# Track work in Linear, privately

Linear is the user's private tracker. The teams behind their shared repos do
not use it, so nothing about Linear goes into git or GitHub: no Linear issue
ID or URL in a branch name, commit message, file, PR title, PR description,
or PR comment, in any repo. Write to Linear only through the Linear tools. A
Linear issue may link a GitHub issue or PR; nothing links back.

Before anything goes out (a push, a PR title or body, a PR comment or review
reply), scan it and publish only on exit 0:

```bash
scan=~/.agents/skills/linear-track/scripts/repo-link.sh
"$scan" scan --base "origin/$base" --text <draft file> || exit 1
printf '%s\n' "$reply" | "$scan" scan --text - || exit 1   # a comment or reply
```

It checks the branch name, the outgoing commit messages, the lines they add,
and the draft. Exit 1 lists what to remove; exit 2 means it could not read
something, so nothing is cleared. Reword commits before the first push. In a
T3 Code worktree, never rename the branch; stop and report a branch name that
carries an ID.

A tracked issue is the user's one reference for its work: a description that
holds the current truth, and comments that hold the dated history.
[references/issue-summary.md](references/issue-summary.md) gives the template,
what goes where, how to write the description without touching the user's
text, how each change is logged and recovered, and how evidence is recorded.
Follow it for every write.

## 0. Read a named issue first

When the request names a Linear issue, read it and its comments before
planning (the issue lookup leaves comments out; list them separately), and
check it as the reference's last section says. That issue is the tracking
record for the work, in any repo, linked or not: steps 3 to 5 apply to it.
When the work skips `plan-feature`, adopt it at build start as step 3 says.

## 1. Find the repo's project

```bash
~/.agents/skills/linear-track/scripts/repo-link.sh get
```

It prints a Linear project ID, or `none` for a repo Linear does not track, and
exits 1 when the repo has no link. With `none` and no named issue, do nothing
in Linear. With no link, ask which project in the first question batch, with
the projects whose names match the repo as options and "not tracked" among
them, then save the answer with `repo-link.sh set <project-id|none>`. The key
lives in the repo's `.git/config`, so every worktree reads it and Syncthing
carries it to the other machines.

## 2. At the start: sync merges

List the `agent` issues across the projects of the linked project's team
that are In Progress or In Review, and keep those whose build-start comment
names this repository. (Step 4 sets Done last, so an interrupted finish stays
in this list.) That comment holds
the repository, the branch, and the start commit; a later comment holds the
PR link. Find each issue's PR:

```bash
gh pr view <url> --json state,mergedAt,headRefOid,body
gh pr list -R <owner/repo> --head <branch> --state all \
  --json url,state,createdAt,mergedAt,headRefOid,headRepository,headRepositoryOwner,body
```

Use the PR link when there is one. Fall back to the branch only for a PR whose
head repository is the one in the build-start comment and that was created
after that comment; follow it too when the linked PR was
closed without merging and the same branch has a newer PR. When more than one
PR fits, or none fits, change nothing and list the issue in your final
report. A PR found from the branch gets its PR link comment and moves the
issue to In Review. A merged PR finishes the issue as step 4 says. A PR
closed without a replacement gets one comment saying so, unless the issue
already has it, and the issue goes in your final report with its status left
for the user.

## Related issues and GitHub issues

At the start of work in a linked repo, search the linked project and the
other projects of its team for issues related to the request: open ones, and
ones closed in the last 90 days. Read the few best matches with their
comments and check them as step 0 does. Put what they settle into your
reading. For feature work, offer the plausible ones in the question batch:
track the work with it, link it as related, or ignore it. For a small
change, name any close match in your report.

When a GitHub issue is involved in a linked repo, ask the user once whether
to create a Linear issue that links it, use an existing Linear issue, or
leave Linear out: in the batch when feature work starts from one, and when it
is filed, if you or the user file one outside a build. A small change from a
GitHub issue gets no question and no issue. A GitHub issue filed during a
build goes into the tracking issue's **Links**.

## 3. Create or adopt the issue

At the user's OK on the summary page (`plan-feature` section 5), act on the
tracking choice already made: adopt the issue named in the request or chosen
in the batch; create nothing when the user chose to leave Linear out or the
repo's link is `none`; otherwise create one issue. A named issue for work
that skips `plan-feature` is adopted at build start.

Work that skips `plan-feature` with no named issue gets one at build start
in two cases: the user asks to track it in Linear, or the repo is linked to a
project and the build touches more than five files or lands in several PRs.
The user's request overrides a `none` link; when the repo has no project,
ask step 1's question before the build starts. When the related-issue search
found an issue for this same work, adopt it; otherwise create one and list
close matches under **Links**. Its summary takes the decisions from the
request and the done checks from the check the session settled before
editing.

The link names the repo's main project; a feature that plainly belongs to
another project in the same team, such as a benchmark run made from a
workbench repo, goes there instead. Ask in the batch when it is not plain.

- Title: the feature's name. Label `agent`, created in the team when missing.
- Description: the summary block from the reference, written as it says.
- Work across several PRs: one sub-issue per PR in `plan.md`'s order, each
  with the `agent` label, blocked by the one before it, with its own short
  summary.
- One comment: approved on <date>, or started on <date> without a spec and
  why it is tracked, and where the work ends.

## Show the issue

Whenever the session creates or takes an issue, link it to the thread with
T3 Code's issue-link tool (`link_issue` with the issue's `linear.app` URL) when
the harness offers it, so it shows beside the thread. In every message that
names an issue, write it as a link, `[ABC-123](<issue URL>)`, so
the user can open it in one click.

## 4. Move it as the work moves

| When | Status | Comment |
|---|---|---|
| The build starts | In Progress | the repository, the branch, and the start commit |
| A PR opens (`open-pr`) | In Review | the PR link |
| The PR merges (`merge-pr`, or step 2) | Done, last | the result, first |
| The work lands without a PR | Done, last | the result, with the commit, first |
| The user drops the work | Canceled | the reason |

Each move also rewrites the summary's **State** line and adds the new link;
when a done check runs, write its outcome as the reference's Evidence section
says. Finish an issue in this order, so an interrupted session leaves it for
step 2 to retry: the result comment (skip it when one already exists for that
PR or commit), then the summary, then any parent, then the Done status. The
result comment gives the PR or commit, each done check with its outcome, and
the follow-ups from the final report. A follow-up becomes an issue only when
the user says so; it gets the `agent` label.

A parent issue follows its sub-issues: In Progress when the first starts, a
PR link in **Links** as each PR opens or merges, and Done, with a result
listing its PRs and the feature's done checks, only when every sub-issue is
Done. A merged PR found through the parent never closes it on its own.

## 5. Before the session ends

Check every issue this session created or touched: its status matches the
work, its summary matches the code and the PR, each change of the kinds the
reference lists has its dated comment, and a finished one has its result
comment. Cancel any issue created only for testing and remove it from its
project, since the Linear tools cannot delete issues, then tell the user it
can be deleted in the app. List each issue as a link with its status in your
report.

## Repo links

```bash
~/.agents/skills/linear-track/scripts/repo-link.sh list   # every synced repo and its link
~/.agents/skills/linear-track/scripts/repo-link.sh set P-ABC-12 --dir <repo>
```

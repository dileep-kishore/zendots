---
name: linear-track
description: Use when work will create, update, or close a Linear issue for the user's private tracking, when a session starts in a repo whose git config sets zendots.linearProject, when a request names a Linear issue, when a PR opens or merges in such a repo, or when the user asks to link a repo to a Linear project. Not for team trackers such as GitHub issues.
---

# Track work in Linear, privately

Linear is the user's private tracker. The teams behind their shared repos do
not use it, so nothing about Linear goes into git or GitHub: no Linear issue
ID or URL in a branch name, commit message, PR title, PR description, or PR
comment, in any repo. Write to Linear only through the Linear tools. A Linear
issue may link a GitHub issue or PR; nothing links back. Before any commit,
push, PR, or PR comment, check what is about to go out:

```bash
~/.agents/skills/linear-track/scripts/repo-link.sh scan --base "origin/$base" --text <draft title and body>
```

It exits 1 and prints each Linear ID or link it finds in the branch name, the
outgoing commits, and the draft text. Remove them before publishing.

A tracked issue is the user's one reference for its work: a description that
holds the current truth in fixed sections, and comments that hold the dated
history. Implementation detail stays in the PR. Follow
[references/issue-summary.md](references/issue-summary.md) for the template,
what goes where, and how each edit is logged so nothing goes stale.

## 0. Read a named issue first

When the request names a Linear issue, read it and its comments before
planning (the issue lookup leaves comments out; list them separately). Later
comments can change the scope. Check its summary against the PR and git state
as the reference says, and correct it first when they disagree. That issue
is the tracking record for the work, even in a repo whose link is `none`.

## 1. Find the repo's project

```bash
~/.agents/skills/linear-track/scripts/repo-link.sh get
```

It prints a Linear project ID, or `none` for a repo Linear does not track, and
exits 1 when the repo has no link. With `none`, do nothing in Linear. With no
link, ask which project in the first question batch, with the projects whose
names match the repo as options and "not tracked" among them, then save the
answer with `repo-link.sh set <project-id|none>`. The key lives in the repo's
`.git/config`, so every worktree reads it and Syncthing carries it to the
other machines.

## 2. At the start: sync merges, then look for related issues

List the issues in In Progress or In Review with the `agent` label across
the projects of the linked project's team, and keep those whose build-start
comment names this repository. That comment holds the repository and branch,
and a later comment the PR link once a PR exists. Find the PR from either:

```bash
gh pr view <url> --json state,mergedAt,body
gh pr list -R <owner/repo> --head <branch> --state all --json url,state,mergedAt,body
```

An issue whose comments already hold a PR link is checked by that link. When
the branch alone matches more than one PR, change nothing and list the issue
in your final report.

A PR found from the branch alone gets its PR link comment and moves to In
Review first. Move a merged one to Done with the result comment from step 4.
Keep the done-check outcomes the summary already records, mark each one
recorded on a commit older than the merged head as not rerun there, and fill
gaps from the PR body's verification section. For a
PR closed without merging, add one comment saying so, unless the issue already
has that comment for this PR, and list the issue in your final report; leave
its status for the user. Then close any parent issue whose sub-issues are now
all Done, as step 4 says.

Then, before the question batch, search for issues related to the request in
the linked project and the other projects of its Linear team: open ones, and
ones closed in the last 90 days. Use the request's key terms. Read the few
best matches with their comments, and check each summary against the code as
step 0 does. Put what they settle into your reading, and offer the plausible
ones in the question batch: track the work with it, link it as related, or
ignore it.

When feature work (`plan-feature`) starts from a GitHub issue, add one
question to the batch: create a Linear issue that links the GitHub issue, use
an existing Linear issue the search found, or leave Linear out. A small change
gets no question and no issue. A GitHub issue filed during the build goes
into the tracking issue's **Links**, with no question.

## 3. Create or adopt the issue at the user's OK

When the user approves a feature's summary page (`plan-feature` section 5),
act on the tracking choice already made: adopt the issue named in the request
(step 0) or chosen in the question batch, and add the `agent` label to it;
create nothing when the user chose to leave Linear out or the repo's link is
`none`; otherwise create one issue. The link names the repo's main project; a
feature that plainly belongs to another project in the same team, such as a
benchmark run made from a workbench repo, goes there instead. Ask in the
question batch when it is not plain.

- Title: the feature's name.
- Description: the summary from the reference. On an existing issue, append it
  below the user's text without resending that text, and later edit only the
  summary block, as the reference says.
- Label `agent`. Create it in the team when it does not exist yet.
- Work across several PRs: one sub-issue per PR in `plan.md`'s order, each
  blocked by the one before it, each with its own short summary.
- One comment: approved on <date>, and where the work ends.

## Show the issue

Whenever the session creates or takes an issue, link it to the thread with
T3 Code's issue-link tool (`link_issue` with the issue's `linear.app` URL) when
the harness offers it, so it shows beside the thread. In every message that
names an issue, write it as a link, `[LBNL-123](https://linear.app/...)`, so
the user can open it in one click.

## 4. Move it as the work moves

| When | Status | Comment |
|---|---|---|
| The build starts | In Progress | the repository (`owner/repo`) and the branch |
| A PR opens (`open-pr`) | In Review | the PR link |
| The PR merges (`merge-pr`, or step 2) | Done | the result |
| The work lands without a PR | Done | the result, with the commit |
| The user drops the work | Canceled | the reason |
| The last sub-issue of a parent is Done | Done, on the parent | the feature result |

Each move also rewrites the summary's **State** line and adds the new link.
Whenever a done check runs or reruns, write its outcome and the commit it ran
on into the summary's done checks, so the summary shows evidence before the
merge. The result comment gives the PR or commit, each done check with its
outcome, and the follow-ups from the final report. A parent's result lists its PRs and the feature's done checks.
A follow-up becomes an issue only when the user says so; it gets the `agent`
label.

When a decision, a done check, or how it works changes during the build,
update the spec, the intent file's amendment log, and the issue summary in
the same step, with the dated comment the reference describes.

## 5. Before the session ends

Check every issue this session created or touched: its status matches the
work, its summary matches the code and the PR, every summary edit has its
dated comment (post a missing one after confirming it is not there), and a
finished one has its result comment. Report any edit you could not pair. Cancel any issue created only for testing and remove it from
its project, since the Linear tools cannot delete issues, then tell the user
it can be deleted in the app. List each issue as a link with its status in
your report.

## Repo links

```bash
~/.agents/skills/linear-track/scripts/repo-link.sh list   # every synced repo and its link
~/.agents/skills/linear-track/scripts/repo-link.sh set P-PLA-33 --dir <repo>
```

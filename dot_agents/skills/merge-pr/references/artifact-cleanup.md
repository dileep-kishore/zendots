# Clean up completed work

Run this after confirming the PR is merged and before removing its worktree.
For an already merged PR, collect the inventory here before cleaning up.
Keep the inventory outside any directory being deleted until cleanup finishes.

## Identify what belongs to the work

Read task notes, session commands, and worker handoffs for exact paths and
test-process handles. Include files inside the worktree, ignored files, and
external scratch locations such as `$TMPDIR`, `/tmp`, `/temp`, and custom
test directories. Check the host where each artifact was created. A temp
directory name, owner, or age alone does not prove it belongs to this work.

Record each path, what created it, and any active consumers. Never sweep a
shared temporary directory, follow a directory symlink into other data, or
remove application data or shared caches. Leave uncertain paths in place
and report incomplete cleanup. Ask only when ownership or retention cannot
be resolved from the task's records.

For a stack, defer shared artifacts until every consuming task is finished.
Preserve work belonging to another session or an unmerged feature. Keep the
existing dirty-worktree refusal; do not force removal or use `git clean` to
make it pass. Only disposable files established by this inventory may be
removed before checking Git status again.

Do not delete tracked repository files as scratch. If disposable reports or
plans are tracked, report that they need removal through a normal reviewed
change; preserve the existing merge gates and tracked documentation.

## Preserve useful feature summaries

Keep existing HTML that usefully explains the completed feature, plus its
required local assets and diagram sources. A review report written as HTML
is still disposable. Do not generate a summary solely to satisfy cleanup.
Keep maintained project documentation and explicitly requested deliverables.

Locate the main checkout with `git worktree list --porcelain`. Copy retained
personal artifacts to that checkout's established ignored artifact folder,
grouped by feature. Use `docs/drafts/<feature>/` when the project has no
convention. Check each destination with
`git -C <main-checkout> check-ignore -- <relative-path>`; if needed, use
`.git/info/exclude` in the main checkout to keep this local copy ignored
without a post-merge commit.
Do not stage, commit, or publish these copies. GitHub publication requires
explicit approval.

Copy related files together so relative links remain valid. Compare source
and destination contents and check local dependencies before deleting the
source. If a destination differs, keep both under distinct names or stop
for a retention decision; never overwrite it silently. Report the retained
HTML's final absolute path. If copying or verification fails, leave the
source worktree intact.

## Stop jobs and remove disposable data

Stop the test servers, browser sessions, watchers, and background jobs created
for this work. Identify a live process from the recorded command and process
group before signalling it; a reused PID or port is not sufficient. Stop its
owned process group and confirm with `ps` or `lsof` that no owned child
remains. Preserve the user's sessions and any process shared with active work.
If a job cannot be stopped or its exit cannot be verified, leave its data and
the affected worktree in place and report the blocker.

Remove the inventoried disposable files and directories: independent-review
reports, verify-this outputs, test screenshots, logs, scratch fixtures,
temporary test repositories, and completed feature plans. Earlier chat links
do not require retaining these files. Remove only the completed work's data;
retain explicit deliverables and anything still needed by active work.

Verify that each removed path is absent and each retained summary still has
its dependencies. An already absent path is already clean. Report retained,
refused, and unverified paths separately. Invoke the branch cleanup helper
only after this check passes; a successful merge alone does not establish
successful cleanup.

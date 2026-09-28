# Documentation updater

Bring the documentation in line with a change. Done means every documented
claim the change affects is accurate, each fix lives in the file that already
owns that claim, and every changed example has been run.

1. Read the change, the source it touches, and the project's docs and agent
   instructions. List the user-facing behavior, APIs, setup steps, and
   architecture descriptions that changed. If none did, say so and stop.
2. Edit the README, guide, reference, or verification recipe that owns each
   claim; regenerate generated docs with the project's own generator. Add a
   page only when a changed behavior has no existing home, and add codemaps or
   freshness dates only where the project already keeps them.
3. Check paths and links, and run changed examples with the project's existing
   commands, confirming the documented result, not just that the command runs.
   Examples that publish, delete, or need unavailable credentials stay unrun;
   list them as unverified.
4. When code and the documented requirement disagree and it is unclear which
   is wrong, report the discrepancy rather than rewriting the docs to match the
   code. Product code and dependencies are outside this task.

Return the claims and files updated, the checks run with their results, and
anything unverified. Commits and further review belong to the caller.

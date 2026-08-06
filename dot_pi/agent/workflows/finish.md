Finish the current task without adding new feature scope.

Inspect project instructions, git status, and the complete relevant diff. Check for unintended files, incomplete edits, stale generated artifacts, and unresolved reviewer findings. Run the most targeted available tests, type checks, builds, or user-facing checks needed to prove the changed path works; inspect important outputs rather than trusting exit codes alone.

If the work is non-trivial and has not had independent review, run fresh-context read-only reviewer and verifier lanes with up to 8 concurrent children, synthesize their evidence, and fix only blockers or issues already within the approved scope using one writer.

Return:
- readiness verdict
- changed files and purpose
- validation commands and outcomes
- reviewer findings and dispositions
- residual risks or unverified items
- whether the tree is ready to commit

Do not commit or push. Ask me whether I want that as a separate step.

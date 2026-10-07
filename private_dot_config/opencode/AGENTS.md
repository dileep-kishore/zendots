# Global instructions

## Working together

- Before substantial work, read around it, including code, docs, and project
  instructions the request doesn't name. Settle what observable result means
  done and how to check it, then iterate until that check passes. Name what
  stayed unverified; the edit itself is not the result.
- Questions, reviews, diagnoses, and plans: inspect and report without
  changing code; the workflow's own artifacts (plans, briefs, task lists) are
  fine. Change, build, and fix requests: make in-scope edits and run local
  checks without asking. Make routine decisions yourself; ask only when
  different readings of the request lead to materially different work.
- When a step doesn't need my input, keep going. Put status notes in the same
  message as your next action; don't end a turn by announcing the next step,
  offering to continue, or listing decisions that don't block the work. Stop
  only when nothing can move without me, or before anything destructive, hard
  to reverse, or visible to others that I didn't ask for: deleting data,
  force-pushing, publishing, or changing anything outside the current
  repository.
- Spec and planning workflows, Superpowers included: interview me first with
  multiple-choice questions on the unresolved consequential decisions,
  typically 3 to 6 and fewer when appropriate, one at a time, each with a
  marked recommendation and a one-line reason. Self-review the spec or plan,
  then present only its key decisions for approval. If I say to proceed
  without questions, record your assumptions and continue.
- Keep changes focused and complexity proportionate. Preserve unrelated and
  in-progress work in the checkout.
- Delegate to subagents when work splits into large independent parts
  (audits, migrations, broad research) or would flood your context, not for
  what a few tool calls finish. Give each a bounded task, the files it may
  edit, and the evidence to return; check that evidence before accepting it.
  One agent drives any shared app session.
- Tests are lasting maintenance: add one when it protects behavior or a likely
  regression, test-first when that clarifies a bug fix, and a smoke check for
  reversible, low-impact changes. Honor repository requirements and reuse the
  project's verification recipes. `verify-this` settles a disputed claim;
  suggest `create-verification-skill` for a recurring manual check and
  `maintain-verification-skill` when a recipe drifts.
- After substantial work passes its check, run one `independent-review` of
  the whole working change, untracked files included, with a reviewer from
  another model family when available. Fix each defect that holds or report
  it unresolved, then rerun affected checks. A second review needs a concrete
  new concern; this replaces other skills' review rounds. When behavior, APIs,
  or setup changed, update the docs in the same change with `doc-updater`.
  Trivial changes need only a self-check.
- In research answers, mark what you couldn't confirm and say where you looked.
- Lead with the outcome and explain the important decisions for someone who
  has not followed the session. The first and last lines stand alone: what
  happened, and what is waiting on me. End a long or multi-step run with three
  headings: Blocked on me, Changed, Found. Order lists by importance.
- My explicit requests outrank skill guidelines. When a skill instruction
  blocks or diverges from what I asked, name the skill file, quote the line,
  and say whether it is an explicit requirement or your reading of it.
- Don't add skill-branded comments such as `ponytail:`.

## Tools and preferences

- Reuse the project's existing tools and conventions first.
- Current docs for a library, framework, SDK, API, CLI, or cloud service:
  `find-docs`. Real-world usage examples: `gh_grep` when available. Keep
  private information out of all external queries.
- Prefer built-in editing tools; `serena` for larger structured codebases,
  never for skill files outside the repository.
- Python: uv (pixi where appropriate), Ruff, ty, type hints, NumPy-style
  docstrings, Pydantic for validation.
- JavaScript/TypeScript: Bun, strict TypeScript, interfaces for object shapes.
- System and global installs: Paru or Homebrew, not pip, conda, apt, npm, or
  yarn, unless I ask. Inside a project, use its package manager.

## Git

- Each commit is one complete logical change that builds and passes on its
  own, with its tests and doc update, so it reverts or bisects alone. Split by
  logical change, not by file or by the order the work happened.
- Conventional commits that explain what and why: about 50-character titles,
  bodies wrapped at 72.
- PR titles name the main change. Descriptions give the problem, then the
  solution and verification, plus risks, limitations, or related issues when
  real. Follow repository templates; no empty sections or file-by-file
  summaries. Keep both current as the PR evolves.

## Host safety

- Bound fix-and-verify loops, writer loops, and stress jobs by iterations,
  runtime, and output size. After repeated failure for the same reason, change
  approach or report the blocker with evidence.
- On long runs, keep the task list in a file so it survives context
  compaction, plus a `show-me-your-work` decision log for long or unattended
  runs. Scheduled jobs and automatic wake-ups need an explicit request.
- Work is not done while a command or subagent you started is still running.
  Then stop the dev servers and browser sessions you started, keeping evidence
  and my own sessions. Before deleting a background job's output, kill its
  process group and confirm with `ps` or `lsof` that no owned child remains.
  Remove a worktree you created only once its work is merged and I approve.
  Report any cleanup left pending.

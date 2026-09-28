---
name: create-verification-skill
description: Use when the user asks to create reusable verification instructions for a project's UI, CLI, library, or service.
disable-model-invocation: true
---

# Create a verification skill

Write a project-local recipe an agent can follow to exercise the project's
real behavior and capture evidence of the result. Done means the recipe has
driven at least one real flow end to end, launch through cleanup, and the
evidence survived. A recipe nobody has run is a draft.

If a recipe already covers the surface, update it with
`maintain-verification-skill` instead. A check that one existing command
already covers does not need a skill.

## 1. Learn how the project runs

Read the project instructions, run and test commands, existing tests, and the
user-facing entry points. Work out startup and readiness, dependencies, auth,
test data, how to capture evidence, and how to isolate a run (ports, data
directories, browser profiles). Ask the user only for what the repository
cannot tell you. Take expected outcomes from requirements and documented
contracts, not from whatever the code currently does.

Use the project's own browser driver, CLI, test runner, or HTTP tooling.
Check that the local instance is safe to exercise, including what a nominal
dry run actually touches. If startup is broken or credentials are missing,
that is the finding: report it rather than repairing product code.

## 2. Write the recipe

Put it at `.agents/skills/verify-<project>/SKILL.md` in the target repository,
or the project's existing shared skill location, with a description that fires
only for verifying this project. For Claude, add a relative symlink
`.claude/skills/verify-<project>` → `../../.agents/skills/verify-<project>`;
report a conflicting file instead of replacing it.

Cover, with the project's real commands:

- **Launch:** prerequisites, the startup command, the readiness signal, and
  the handles (PIDs, ports, profile dirs) for everything the run creates.
- **Health check:** a read-only probe that the right build and instance are
  up with the access needed. Rerun it after any unexpected failure.
- **Drive:** the real user entry points, with the expected observable result
  of each action, side effects included.
- **Evidence:** how to capture it, what revision it applies to, and where
  private artifacts go. Secrets stay out.
- **Cleanup:** stop what the run started, keep the evidence, and list any
  resource that could not safely be removed.

Index the flows in `features/README.md`: requirement, entry points,
prerequisites, actions, expected results, known limits, and whether each has
been exercised. Split into per-feature files only once the index gets long.

## 3. Prove it

Run one mapped flow from the recipe as a fresh agent would. When a step
fails, fix the recipe and rerun from that step; keep going until the flow
passes or you hit a blocker the recipe cannot fix. Never loosen an expected
result to make it pass. Clean up after failed attempts as well.

If both Claude and Codex are available, start a fresh session in each and
confirm it finds the skill. File layout alone does not prove discovery.

## Output

`ready` for the flows actually exercised, or `draft` / `blocked` with what is
missing. List the files written, checks run, evidence paths, flows not yet
exercised, discovery results, and cleanup left pending. Commit or publish only
when asked.

Locally maintained. Adapted from Cursor pstack's
[create-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md).

---
name: maintain-verification-skill
description: Use when the user asks to audit or update an existing project's verification skill or feature map after behavior changes.
disable-model-invocation: true
---

# Maintain a verification skill

Bring an existing verification recipe back in line with the product. Done
means every flow in scope has been run live against the current code and
either passes, was corrected and then passed, or has a named blocker. Reading
source alone does not count, even when nothing looks stale.

## 1. Pin the target and scope

Find the project's verification skill, following provider symlinks to its
canonical directory. If there is none, point to `create-verification-skill`;
if several could match, ask. Scope is the flows the user named, the flows a
recent change touched, or, for an audit, every mapped flow. State the scope,
because a passing subset is not a full audit.

## 2. Find the drift

Check that the feature index and the recipes agree, then read the changed
source and nearby entry points for flows that are missing, renamed, or
behaving differently. Cite source paths. Use requirements and the change's
intent to tell a deliberate change from a regression; ask when you cannot.

For a large scope, give read-only subagents one slice each; have each return
source locations, suspected drift, and a live check to run. Only one agent
drives a shared running instance.

## 3. Run every scoped flow

Update the recipes, then run each flow using the recipe's own launch and
health checks, capturing actions and results. Sort each failure:

- **Doc drift or recipe gap:** fix the recipe or its helper and rerun.
- **Product defect:** leave the expected result as it is and report it.
- **Missing prerequisite** (credentials, a service): report as unverified.

After an unexpected failure, rerun the health check or reset state before
retrying. If a flow still fails for the same reason, treat it as a blocker
and move on to the next flow rather than retrying further. Clean up what the
run created, failed attempts included, and confirm the evidence survived.

## Output

One outcome for the stated scope:

- `clean`: every flow passed; nothing needed correcting.
- `changed`: corrections made, and every flow passed afterward.
- `blocked`: at least one flow is unverified or broken. List partial
  corrections separately.

Include the scope, revision checked, per-flow evidence, files changed,
product defects, unverified prerequisites, and cleanup left pending. Leave
committing and review to the parent workflow. Long audits can keep a
decision trail with `show-me-your-work`.

Locally maintained. Adapted from Cursor pstack's
[maintain-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md).

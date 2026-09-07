---
name: to-spec
description: Use when the user asks to turn the current conversation, plan, or notes into a spec without another interview. Synthesizes what is already known into a local spec file.
disable-model-invocation: true
---

# To spec

Synthesize a spec from the conversation and the codebase. Do not interview
the user; the discussion already happened. Ask only about a decision that is
still open and would change the spec, one question at a time, with a
recommended answer. If the user said to proceed without questions, choose the
recommended answer and record it as an assumption.

## 1. Ground it in the repo

Explore the relevant code if you have not already. Use the project's glossary
and ADRs where they exist; do not create them here. Prefer describing modules and interfaces
over file paths and code, which go stale; keep a snippet only when it encodes a
decision more precisely than prose (a schema, state machine, type shape).

## 2. Write proportionately

Length follows the change. A one-file fix gets a one-screen spec; a subsystem
gets more. Sections, omitting any that would be empty:

- **Problem**: what the user faces, from their perspective.
- **Solution**: what changes for them.
- **User stories**: only when they clarify scope, a handful, never an
  exhaustive list.
- **Implementation decisions**: modules, interfaces, schema and API changes,
  architectural choices, and the assumptions you made without asking.
- **Testing**: the seams you will test at, preferring existing seams and the
  highest useful one. Add or change tests only where they protect behavior;
  no coverage quota. State the choice; ask only if a new seam is a
  consequential design decision.
- **Out of scope**.
- **Open questions**: the unresolved consequential choices, if any.

## 3. Save it where the project keeps specs

Use the project's existing spec location and naming. With the Superpowers
convention that is `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`;
otherwise the project's docs directory, falling back to `docs/specs/`. Say
which you chose.

Publishing to an issue tracker, applying labels, or creating tickets happens
only when the user asks, using the tracker and tools the project already has.
A local spec is complete without a tracker.

## Output

The spec's path, a five-line summary, and any open questions. Do not start
implementation; the spec feeds the planning workflow.

Locally maintained. Adapted from Matt Pocock's
[to-spec](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md).

---
name: grill-with-docs
description: Use when the user asks to grill, stress-test, or sharpen a plan, design, or decision through a short interview, and wants the resulting decisions recorded in the project's docs.
disable-model-invocation: true
---

# Grill with docs

Interview the user only about decisions that change the outcome, settle the
rest yourself, and write the answers into the project's existing docs.

## 1. Find the facts first

Facts are your job, not the user's. Before asking anything, read what the
project already holds: the plan or spec being grilled, the glossary
(`CONTEXT.md` or equivalent), ADRs, recent commits, and the code the plan
touches. Look up anything a question would otherwise ask the user to recall.

## 2. Ask only consequential questions

Build the decision tree, then ask only the branches whose answer materially
changes the work: scope, data model, interfaces, irreversible choices, safety
or authorization boundaries. Infer routine details and state the assumption
instead of asking.

- Normally 3–6 questions, fewer when the plan is small; ask one at a time.
- Each question is multiple choice with a marked recommendation and a one-line
  reason. Include enough context to answer without scrolling back.
- Ask the next question only when its prerequisites are settled.
- Stop when nothing consequential remains, not when every branch is visited.
- If the user says to proceed without questions, record the assumptions you
  would have asked about and continue within the authorized scope.

While interviewing, challenge terms that conflict with the glossary, and surface
contradictions between what the user says and what the code does.

## 3. Record decisions where the project already keeps them

Create nothing speculative; update what exists:

- A sharpened or new domain term goes into the project's glossary. Create a
  `CONTEXT.md` only when the project has no glossary and a term was actually
  resolved.
- Write an ADR only when the decision is hard to reverse, surprising without
  context, and the result of a real trade-off. Use the project's existing ADR
  format and location; otherwise `docs/adr/NNNN-<slug>.md`.
- Everything else goes into the plan or spec being grilled, in its decisions
  section, alongside the assumptions you made without asking. When the plan
  exists only in the conversation, write it as a short plan file in the
  project's usual plan location so the decisions have a home.

## Output

A short summary: decisions made, assumptions taken, open items that need
someone else, and the docs you updated. Then stop; grilling does not authorize
implementation. Hand the result to the project's spec or plan workflow.

Locally maintained. Adapted from Matt Pocock's
[grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/SKILL.md),
[grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md),
and [domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md).

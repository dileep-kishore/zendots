# Writing for agents

Rules for any document an agent consumes: a skill, `AGENTS.md`/`CLAUDE.md`,
or a file reached through a pointer. Condensed from Matt Pocock's
[writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
and its
[SKILL-MECHANICS](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md).

## Pointers decide when material is reached

A skill description or an `AGENTS.md` line is a **context pointer**: its
wording, not its target, decides whether the agent reaches the material. A
must-have document behind a weak pointer is a variance bug; sharpen the
wording before inlining the content.

- Front-load the word that does the triggering.
- One trigger per branch. Synonyms for the same case are one branch written
  twice; keep only distinct cases.
- Cut identity the body already carries.

## Two budgets

- **Context load**: always-loaded text (descriptions, global instructions)
  costs tokens and attention on every turn, whether or not it fires.
- **Cognitive load**: the human must remember the document exists and when
  to use it. Spend it where human judgement matters, not elsewhere.

A model-invoked skill trades context load for discoverability. A
user-invoked skill (`disable-model-invocation: true`) costs no context but
makes the human the index. Choose model invocation only when the agent, or
another skill, must reach it on its own. When user-invoked skills pile up, a
single **router skill** that names them and when to reach for each is the
cure.

## Hierarchy and disclosure

Steps (ordered actions) sit at the top; reference consulted on demand sits
below; reference only some branches need goes into a separate file behind a
pointer. Inline what every branch needs; disclose what only some reach. Keep
a concept's definition, rules, and caveats under one heading. A document that
is long even though every line is live has sprawled; split by branch or
sequence.

## Completion criteria

End every step on a condition the agent can check. "Every modified model
accounted for" forces work that "produce a change list" does not. Sharpen a
fuzzy bound before hiding later steps; hiding only works across a real
context boundary such as a subagent dispatch.

## Words

- Prefer a **leading word** the model already knows (*tight*, *red*, *tracer
  bullet*) over a sentence that restates it each time.
- State the positive target ("write one-line comments") rather than the
  prohibition; a ban drags the forbidden behaviour into context.

## Pruning

- One source of truth per meaning; duplication inflates a meaning's rank.
- The environment (`--help`, config, directory layout) is a source of truth.
  Restating it is a cache that goes stale; record only what cannot be looked
  up: conventions, reasons, gotchas.
- Delete any sentence the model already obeys by default. Test by running the
  document, not by debate.

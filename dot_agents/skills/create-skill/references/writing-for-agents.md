# Writing for agents

Rules for any document an agent consumes: a skill, `AGENTS.md`/`CLAUDE.md`,
or a file reached through a pointer. Condensed from Matt Pocock's
[writing-for-agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md)
and its
[SKILL-MECHANICS](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL-MECHANICS.md),
then updated from Anthropic's
[Opus 5.5 guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)
and OpenAI's
[GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra).
Shared skills are read by both families, so prefer what both endorse.

## Pointers decide when material is reached

A skill description or an `AGENTS.md` line is a **context pointer**: its
wording, not its target, decides whether the agent reaches the material. A
must-have document behind a weak pointer is a variance bug; sharpen the
wording before inlining the content.

- Front-load the word that does the triggering.
- One trigger per branch. Synonyms for the same case are one branch written
  twice; keep only distinct cases.
- Cut identity the body already carries.
- Keep descriptions short: when to trigger, and when not to. Codex truncates
  the skill list past about 2% of context, so trigger words go first.
  "Always use" or "use even when you think you know" over-loads the skill.

## Two budgets

- **Context load**: always-loaded text (descriptions, global instructions)
  costs tokens and attention on every turn, whether or not it fires.
- **Cognitive load**: the human must remember the document exists and when
  to use it. Spend it where human judgement matters, not elsewhere.

A model-invoked skill trades context load for discoverability. A
user-invoked skill (`disable-model-invocation: true`) costs no context where
the harness honors the switch (OpenCode lists every skill regardless) but
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

Shape outputs the same way. A reviewer reports every finding with its
severity, location, why it is wrong, and how to show it fails, and a later
pass filters; "only report high-severity issues" makes a literal model report
less. Research marks what it could not confirm and where it looked.

## Goals, loops, and stops

Current models plan well and run long; the prompt's job is the target, not
the choreography.

- **Goal over script.** State what done looks like and how to check it,
  then let the agent choose the steps. Script exact commands only where a
  wrong step is costly or hard to undo.
- **Loop to the check.** Tell the agent to iterate until the check passes
  and to fix incidental failures (a busy port, a stale cache) itself. Bound
  the loop by rounds or time, and name the exit: after repeated failure for
  the same reason, change approach or report the blocker with evidence.
- **One autonomy policy.** State when to act, ask, and stop once, in one
  place. Repeated "ask first" makes a literal model stall, and "stop for
  review after the first implementation" pulls it toward stopping early.
- **Checkpoint once, where it matters.** Each approval stop costs a turn.
  Batch everything the user needs to approve into one checkpoint placed
  before the first outward-facing or irreversible action, not one per step.
- **Name the failure you want gone.** "Do not end the turn by announcing the
  next step" works; "be thorough" swaps one default for another. Name the
  stops you do want, too: nothing can move without the user. Design works the
  same way: list the defaults to leave out (monospace labels, pill buttons,
  numbered section labels, cream backgrounds); "avoid a generic look" only
  swaps templates.
- **Point at hidden context.** When what the task depends on sits somewhere
  the request does not mention, tell the agent to look around before acting.
- **Leave thinking to effort.** "Think carefully" and "reason step by step"
  add latency, not quality; the harness's effort setting controls thinking.
  Ask for a short explanation rather than visible reasoning, which current
  models may decline.
- **Scale verification.** Opus 5.5 and GPT-6 verify on their own, so generic
  "double-check" and "run the tests" nudges cause over-testing there. Drop one
  only once every model the text serves does the check without it, and keep
  checks the user requires. Grant known-safe loops instead: run local tests,
  fix failures, rerun without asking.
- **Say when to delegate.** Claude tends to over-delegate and GPT to
  under-delegate, so name the work that earns a subagent (large, independent,
  parallel) and require its evidence be checked before acceptance.

## Words

- Prefer a **leading word** the model already knows (*tight*, *red*, *tracer
  bullet*) over a sentence that restates it each time.
- Prefer a concrete positive target ("write one-line comments"); a vague ban
  drags the forbidden behaviour into context. Keep explicit bans for
  permission boundaries, recurring failures, and named design defaults.
- Save ALWAYS, NEVER, MUST, and capitals for rules with no exceptions; give
  judgment calls a decision rule. Emphasis on many lines stands out on none
  and makes literal models over-cautious.

## Pruning

- One source of truth per meaning; duplication inflates a meaning's rank.
- Contradictions cost more than gaps: a literal model stalls on conflicting
  rules. Resolve them, and let the user's request outrank the skill.
- The environment (`--help`, config, directory layout) is a source of truth.
  Restating it is a cache that goes stale; record only what cannot be looked
  up: conventions, reasons, gotchas.
- Delete any sentence the model already obeys by default. Test by running the
  document, not by debate.

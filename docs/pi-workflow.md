# Pi Workflow Guide

Pi's workflow setup is global, managed by chezmoi under `dot_pi/agent/`, and deployed to `~/.pi/agent/`.

## Main workflows

| Command | Purpose | Behavior |
| --- | --- | --- |
| `/investigate <task>` | Diagnose without edits | Traces behavior, gathers evidence, presents options, then stops |
| `/ship <task>` | Implement approved work | Uses one writer, focused validation, and independent review for non-trivial changes |
| `/audit <target>` | Run an adversarial review | Uses read-only parallel lanes, coverage checks, and verification |
| `/deadline <task>` | Finish quickly and defensibly | Limits scope to at most one writer and one verifier |
| `/finish` | Check work before committing | Reviews the complete diff, validates it, and fixes only in-scope blockers |

Examples:

```text
/investigate why login refresh sometimes loops
/ship add the approved timeout handling
/audit the authentication boundary
/deadline fix the broken CLI flag
/finish
```

Calling the first four commands without arguments only changes the persistent mode:

```text
/investigate
/preset ship
/preset off
```

`/finish` always runs its readiness workflow and switches to `ship` mode.

A mode can also be selected when starting Pi:

```bash
pi --preset investigate
pi --preset deadline "Fix the failing command"
```

The active mode is displayed as `mode:<name>` and restored when resuming that session.

## What modes change

Each mode:

1. Sets thinking to `high`.
2. Restricts the active tools.
3. Injects mode-specific instructions into every subsequent turn.

Mode differences:

- `investigate`: no edit, write, or subagent tools.
- `audit`: subagents are available, but editing is disabled.
- `ship` and `deadline`: editing and subagents are available.
- `/preset off`: restores the tools and thinking level from session startup.

## Subagents

`pi-subagents@0.42.0` is configured with:

- asynchronous top-level runs;
- up to eight concurrent children;
- FleetView below the editor;
- artifacts stored with session data;
- child-to-parent intercom;
- dynamic `workflowScript` orchestration rather than saved chains.

### Custom agents

| Agent | Role | Default context and model |
| --- | --- | --- |
| `scout` | Fast read-only reconnaissance | Fresh context, GPT-5.3 Codex Spark, low thinking |
| `planner` | Evidence-backed implementation planning | Forked context, GPT-5.6, high thinking |
| `worker` | Sole-writer implementation | Forked context, GPT-5.6, high thinking |
| `reviewer` | Adversarial diff or plan review | Fresh context, GPT-5.5, high thinking |
| `verifier` | Prove acceptance criteria | Fresh context, GPT-5.5, high thinking |

Built-in `oracle`, `researcher`, `context-builder`, and `delegate` agents are also available.

Subagents can be requested naturally:

```text
Use scout to map the authentication flow.
Ask oracle to challenge this design.
Run parallel reviewers for correctness, tests, and simplicity.
Have worker implement the approved plan, then verify it.
```

Or invoked directly:

```text
/run scout "Map the authentication flow"
/run planner "Plan the approved refresh-token fix"
/run reviewer "Review the current diff"
/run verifier "Verify the CLI behavior"
```

Monitor and control them with:

```text
/subagents-fleet
/subagents-stop
/subagent-cost
/subagents-doctor
```

## Packaged workflow shortcuts

`pi-subagents` also provides:

```text
/gather-context-and-clarify
/parallel-review
/review-loop
/parallel-research
/parallel-context-build
/parallel-handoff-plan
/parallel-cleanup
```

For normal work, the custom `/investigate`, `/ship`, `/audit`, `/deadline`, and `/finish` commands are the primary entry points.

## Session handoff

`/handoff <next goal>` creates a focused new session instead of compacting the current one:

```text
/handoff implement phase two of the approved plan
```

It summarizes relevant history, opens the generated prompt for editing, creates a parent-linked session, and leaves the prompt ready to submit.

## Configuration files

- Workflow engine: `dot_pi/agent/extensions/presets.ts`
- Mode definitions: `dot_pi/agent/presets.json`
- Workflow prompts: `dot_pi/agent/workflows/*.md`
- Agent definitions: `dot_pi/agent/agents/*.md`
- Subagent runtime: `dot_pi/agent/extensions/subagent/config.json`
- Session transfer: `dot_pi/agent/extensions/handoff.ts`
- Status UI: `dot_pi/agent/extensions/pretty.ts`
- Packages and models: `dot_pi/agent/modify_settings.json`

# Pi Workflow Guide

Pi's workflow setup is managed by chezmoi under `dot_pi/agent/` and deployed to
`~/.pi/agent/`. Its settings modify template preserves unrelated live settings
while managing packages, model selection, thinking level, and theme.

## Settings and deployment

The configured default is `openai-codex/gpt-5.6-sol` with high thinking and
Catppuccin Mocha. This is a configured preference, not a guarantee that a model
is available to the signed-in provider. Use `pi --list-models` to inspect the
current catalog; unavailable entries in `enabledModels` can produce warnings.

Package pins are defined in `dot_pi/agent/modify_settings.json`: pi-subagents,
pi-lens, pi-web-search, and the question/todo extensions. These are independent
of the Claude, Codex, and OpenCode plugin versions. Ponytail was removed from
the source package list; live removal still requires the scoped deployment in
the [retirement record](maintenance/2026-10-20-ponytail-retirement.md).

After editing the source, preview the selected destinations, for example:

```bash
chezmoi diff -r ~/.pi/agent/settings.json ~/.pi/agent/presets.json
```

Apply those paths only after approving the diff, then restart Pi. Extension,
workflow, and agent-definition edits must include their own destination paths
in the same preview/approval process. Applying settings does not prove package
compatibility or provider access; `pi --help` confirms the `--preset` extension
flag is loaded.

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
- `/preset off`: restores the tools and thinking level captured at session startup.

Read-only modes retain `bash`; their instructions prohibit writes, but they are
not an operating-system sandbox. Missing extension tools are omitted from a
preset's active tools and reported when the mode is selected interactively.

## Subagents

`pi-subagents@0.42.0` is configured with:

- asynchronous top-level runs;
- up to eight concurrent children;
- FleetView below the editor;
- artifacts stored with session data;
- child-to-parent intercom;
- dynamic `workflowScript` orchestration rather than saved chains.

### Custom agents

| Agent | Role | Context and model selection |
| --- | --- | --- |
| `scout` | Fast read-only reconnaissance | Fresh; GPT-5.3 Codex Spark, low thinking; fallback models declared in its agent file |
| `planner` | Evidence-backed implementation planning | Forked; no model override, high thinking |
| `worker` | Sole-writer implementation | Forked; no model override, high thinking |
| `reviewer` | Adversarial diff or plan review | Fresh; no model override, high thinking |
| `verifier` | Prove acceptance criteria | Fresh; no model override, high thinking |

Only `scout` pins a model in the local agent definitions. The others use the
runtime-selected model rather than fixed GPT-5.6/GPT-5.5 assignments. All five
inherit project context but disable skill inheritance; `worker` may not launch
subagents.

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

## Workflow orchestration

The local workflow prompts use `pi-subagents` dynamic `workflowScript`
orchestration rather than checked-in chains. Audit work uses distinct
read-only lanes; implementation uses one writer per working directory, then
focused validation and fresh-context review for non-trivial changes.

The custom `/investigate`, `/ship`, `/audit`, `/deadline`, and `/finish` commands
are the local entry points. Package-provided shortcuts depend on the pinned
runtime; they are not defined by this repository's preset extension.

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

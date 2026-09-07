---
name: handoff
description: Use when the user asks to hand off, transfer, or compact the current work so a fresh agent session, possibly on another machine, can continue without this conversation.
disable-model-invocation: true
---

# Handoff

Write a transfer note that lets a fresh agent, with no memory of this session,
tell what is verified, what was decided, and what it is authorized to do.
Invoke explicitly; any arguments describe what the next session will focus on.

## 1. Collect ground truth, not memory

Read the project config (`CLAUDE.md`, `AGENTS.md`, or equivalent) so the note
does not restate it. If the user points you at an earlier handoff note,
update it in place instead of starting over. Then record:

```bash
hostname; pwd; git rev-parse --abbrev-ref HEAD; git rev-parse --short HEAD
git status --short --untracked-files=all
```

Mark work "done" only when you observed the evidence this session (a test
run, a diff, a command's output). Anything else is "unverified", however
confident the earlier conversation sounded. When the checkout disagrees with
the conversation, the checkout wins; record the discrepancy.

## 2. Write the note

State, not instructions: say what is true, and let the next agent decide.
Point to specs, plans, PRs, tickets, reports, and diffs by path or URL
instead of copying them. Omit any section that would be empty.

```markdown
# Handoff: <short title>
<host> · <checkout path> · <branch> @ <HEAD> · <date> · focus: <next-session focus>

## Goal
## Current state
- DONE (verified: <how>): ...
- PARTIAL: ...
- NOT STARTED: ...
- UNVERIFIED claims from this session: ...
## Decisions and dead ends
## Verification done and its limits
## Pointers
## Open work and authorization
- Authorized by the user: ...
- Needs approval: ...
## Suggested skills for the next session
```

Never include credentials, tokens, or personal data; name where they live
(".env, not committed") instead. Leave out transcript detail the next agent
does not need.

## 3. Save privately, then show it

```bash
dir=$(mktemp -d) && chmod 700 "$dir" && stat -c '%a' "$dir"   # expect 700
```

Write `"$dir"/handoff-<slug>.md`, report the absolute path, and print the
whole note in one fenced block so it can be pasted into a session on another
machine, where that temp path does not exist. Use shared storage only when
the user names it; never sync or publish a handoff on your own.

## 4. Do not act on the handoff

A handoff launches nothing and transfers no ownership. If the user asks to
start the next session or transfer through Orca, use that tool's own
workflow. Do not tell the next agent to wait or to continue; the user's
instructions govern that.

Locally maintained. Adapted from Matt Pocock's
[handoff](https://github.com/mattpocock/skills/blob/main/skills/productivity/handoff/SKILL.md)
and David Ondrej's
[handoff](https://github.com/davidondrej/skills/blob/main/skills/agent-orchestration/handoff/SKILL.md).

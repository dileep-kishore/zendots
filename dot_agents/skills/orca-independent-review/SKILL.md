---
name: orca-independent-review
description: Launch independent review through fresh Orca terminals. Use when the user requests Orca for a single reviewer or a dual Claude and Codex review.
disable-model-invocation: true
---

# Orca independent review

Use [independent-review](../independent-review/SKILL.md) for scope, reviewer
selection, briefs, completion, and triage. Read it and its brief template first.
This skill supplies the Orca launcher only; do not duplicate the shared review
or start another coordinator. It requires the sibling `independent-review` skill.

## Launch through Orca

1. Read the `orca-cli` skill, resolve the executable, and load its live guide.
   Use the current guide's commands rather than cached flags. Confirm Orca is
   running and resolve the exact worktree/folder to the shared brief's checkout.
   Do not assume `active` means the requested checkout.
2. Create a fresh terminal there for each selected reviewer. Use the requested
   provider or its configured default, without resuming an earlier session.
   For dual review, create both terminals and send both briefs before waiting
   for either report.
3. Read each terminal before sending input. Handle routine presentation prompts
   as needed, but do not accept new trust, authentication, or permission grants
   on the user's behalf. Report a blocking prompt and the terminal handle.
4. Send one short instruction with the quoted absolute brief path, asking the
   reviewer to read it and write to its assigned report path. Keep substantive
   prompts in files because long terminal input can be mangled by the TUI.
5. Track terminal handles and reports separately. Use bounded terminal waits
   and reads from the live guide, with individual waits at most 60 seconds.
   Follow the shared completion rules; `tui-idle` is not review completion.

For a requested handoff, return terminal handles, report paths, and the current
CLI command to inspect each terminal. Otherwise wait, read completed reports,
and perform the shared triage. Do not close a reviewer terminal unless requested
or needed for an authorized cancellation.

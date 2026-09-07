# CLIs that agents can run

Checklist for a script or command an agent will invoke, condensed from
Cursor's
[cli-for-agents](https://github.com/cursor/plugins/blob/main/cli-for-agent/skills/cli-for-agents/SKILL.md).
Applies to skill helpers in `scripts/` and to the tools in `~/.local/bin`.

- **Non-interactive first.** Every input is a flag or a flag value. Fall back
  to prompts only when flags are missing, never the other way round.
- **Layered help.** Every subcommand has `--help`, and every `--help` ends
  with real example invocations. Do not print the whole manual on every run.
- **Pipelines.** Accept stdin where it makes sense; support chaining through
  plain-text output.
- **Fail fast.** A missing required flag exits at once with the message and a
  correct example invocation, not a hang.
- **Idempotent.** Running a successful command twice is a no-op or an explicit
  "already done", never a duplicated side effect. Agents retry.
- **Destructive actions** take `--dry-run` to preview and `--yes`/`--force` to
  skip confirmation, keeping the safe default for humans.
- **Predictable shape.** One `resource verb` pattern everywhere.
- **Machine-useful success output.** IDs, paths, URLs, durations on their own
  lines; decorative output is fine but never the only output.

When reviewing an existing CLI, check each point above in order.

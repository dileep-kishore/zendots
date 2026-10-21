# Review rules

zendots is the chezmoi source for two hosts: tsuki (CachyOS Linux) and
macmini (macOS). A change reaches `~` only through `chezmoi apply`, on both.

## Focus
- A template or script that works on one host and breaks on the other: a
  macOS-only path, a GNU-only flag, a Linux font name, a missing
  `.chezmoi.os` guard, a Python feature newer than a host's interpreter.
- A new repository-root file missing from `.chezmoiignore`, which deploys
  into `~` (how `~/AGENTS.md` once became global agent rules).
- A managed file that an app rewrites itself, so every apply fights the app.
- A template that renders invalid JSON, TOML or YAML.
- Shell startup that prints, leaks a nonzero status to the prompt, or leaves a
  secret such as `ANTHROPIC_API_KEY` exported to every process.
- Skill edits under `dot_agents/skills/` instead of `~/.agents/skills/`; the
  next `agent-skills.sh sync` discards them.
- A skill installed outside `agent-skills.sh`, or linked into
  `~/.codex/skills` or `~/.config/opencode/skills`, where it loads twice.
- Docs that name a command, flag or path that does not exist.
- Instructions that run a bare `chezmoi apply`, or apply before showing a
  scoped diff.

## Skip
- Missing automated tests: repository policy forbids them unless requested.
- Content of upstream skills recorded in `dot_agents/dot_skill-lock.json`.
- Churn in `dot_skill-lock.json`, `dot_runtime-lock.json` and `pkgs/Brewfile`.
- Taste in app configs (keybindings, fonts, colors, layout) that breaks no
  stated convention such as Catppuccin Mocha or chezmoi naming.

## Human review
- `.chezmoiremove`
- `.chezmoiscripts/`

## Output
- Start with the finding count; write "Nothing to fix" when it is zero.
- Cite file:line for every finding.
- Report at most three P3 findings.

## Precedents

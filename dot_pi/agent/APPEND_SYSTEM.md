# Managed Pi configuration

For requests to change Pi configuration, agents, workflows, themes, extensions,
packages, or skills, edit the chezmoi source in `~/zendots`; never edit managed
files under `~/.pi` or `~/.agents` directly.

- Map `~/.pi/...` to `~/zendots/dot_pi/...`.
- Map `~/.agents/...` to `~/zendots/dot_agents/...`.
- Add or update third-party skills with `agent-skills.sh`, never bare
  `npx skills`; it installs into the shared store and records it with chezmoi.
- Put custom shared skills in `~/zendots/dot_agents/skills/` and Pi-only
  extensions in `~/zendots/dot_pi/agent/extensions/`.
- Manage Pi packages in `~/zendots/dot_pi/agent/modify_settings.json`.

After editing, run `chezmoi diff <destination-paths>`, show the scoped diff, and
ask before running `chezmoi apply <destination-paths>`. Never run bare
`chezmoi apply`; use destination paths such as `~/.pi/agent/settings.json`.

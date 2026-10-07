# Managed Pi configuration

For requests to change Pi configuration, agents, workflows, themes, extensions,
or packages, edit the chezmoi source in `~/zendots`; never edit managed files
under `~/.pi` or `~/.agents` directly.

- Map `~/.pi/...` to `~/zendots/dot_pi/...`.
- Map `~/.agents/...` to `~/zendots/dot_agents/...`, except skills.
- Skills flow the other way: edit `~/.agents/skills/<name>/` in place, then
  run `agent-skills.sh sync`, which records the store with `chezmoi add`. An
  edit to `~/zendots/dot_agents/skills/` is discarded by the next sync.
- Add or update third-party skills with `agent-skills.sh`, never bare
  `npx skills`; it installs into the shared store and records it with chezmoi.
- Put custom shared skills in `~/.agents/skills/` (see the `create-skill`
  skill) and Pi-only extensions in `~/zendots/dot_pi/agent/extensions/`.
- Manage Pi packages in `~/zendots/dot_pi/agent/modify_settings.json`.

After editing, run `chezmoi diff -r <destination-paths>`, show the scoped
diff, and ask before running `chezmoi apply <destination-paths>`. Never run
bare `chezmoi apply`; use destination paths such as
`~/.pi/agent/settings.json`.

<div align="center">
  <img src="assets/logo.svg" width="120" alt="zendots logo">
  <h1>zendots</h1>
  <p><strong>Personal, keyboard-centric dotfiles for macOS and Linux</strong></p>
</div>

[chezmoi](https://www.chezmoi.io/) source for **macmini** and **macbook** (macOS)
and **tsuki** (CachyOS Linux): shells, Neovim, tmux, desktop configuration, and coding agents.
Catppuccin Mocha is the shared theme. The current desktops are **OmniWM** on
macOS and **Niri + native Noctalia v5** on Linux; AeroSpace/SketchyBar and
Hyprland/Waybar configurations are also retained.

This is not a portable, unattended installer. Review personal paths, app rules,
package lists, encrypted secrets, and apply hooks before using it on another host.

## Stack

| Area | Configuration |
| --- | --- |
| Shell | Zsh + Zinit, carapace, atuin, zoxide, television, Oh-My-Posh; Bash and Fish configs also included |
| Terminals | Ghostty, Kitty, Warp |
| Editor | Neovim + lazy.nvim, Snacks pickers, sidekick.nvim, avante.nvim, Copilot |
| Sessions | tmux + TPM, sesh, tmuxp; Zellij config also included |
| Files and Git | Yazi, Lazygit, delta |
| macOS desktop | OmniWM; Karabiner/Raycast hotkeys configured separately — [guide](docs/omniwm.md) |
| Linux desktop | Niri + Noctalia v5 — [guide](docs/noctalia-v5.md) |
| Coding agents | Claude Code, Codex, OpenCode V2, Pi, omp; Orca and T3 Code integrations |
| Shell AI | aichat command generation with `Alt-e` |
| Project sync | Syncthing + `work-sync` for macmini/macbook/tsuki project folders and external Orca worktrees |

Package inventories: [Homebrew](pkgs/Brewfile), [Arch/CachyOS scripts](pkgs/arch/),
[Fedora scripts](pkgs/fedora/). These lists are platform-specific, not an
exhaustive installer for every configured app or agent.

## Repository layout

| Source | Destination or purpose |
| --- | --- |
| `dot_zshrc.tmpl`, `dot_shell_exports.tmpl`, `dot_shell_aliases.tmpl` | `~/.zshrc`, shared environment and aliases |
| `private_dot_config/` | `~/.config/`: editor, terminals, desktops, tools |
| `private_dot_local/bin/` | `~/.local/bin/`: skills, agent updates, sync helpers |
| `dot_agents/` | `~/.agents/`: shared skills, locks, hooks |
| `private_dot_claude/`, `dot_codex/`, `dot_pi/`, `private_dot_omp/` | Per-agent configuration |
| `.chezmoidata/` | Managed Claude, Codex, and Serena configuration fragments |
| `.chezmoiscripts/`, `private_Library/`, `private_dot_config/systemd/` | Apply hooks and platform scheduling |
| `pkgs/`, `tools/` | Package setup and source-only helper projects |
| `docs/` | Operational guides and dated maintenance records; not deployed to home |

Chezmoi translates `dot_` to `.`, `private_` to restricted permissions,
`executable_` to executable files, and renders `.tmpl` files per host.
`.chezmoiignore` keeps repository-only files out of home and excludes
platform-specific configs on the other OS. `.chezmoiremove` lists retired paths;
review its deletions before applying those targets.

## Setup

### Prerequisites and packages

Install Git and chezmoi with your platform package manager. macOS package setup
uses [Homebrew](https://brew.sh/). Arch/CachyOS scripts expect `sudo`, pacman,
and an existing `paru`; Fedora scripts are available separately for review.
Node/npm is needed for skill installation, and `uv` runs the Python helpers.

Initialize the source without applying it:

```bash
chezmoi init --source "$HOME/zendots" git@github.com:dileep-kishore/zendots.git
```

Keep this checkout at `~/zendots`: the `work-sync` launcher uses that path.
The repository's `chezmoi.toml` is an example configuration, not an automatically
deployed chezmoi config. Encrypted secrets require a separately provisioned age
identity; do not copy another host's secrets or private manifest into a new setup.

On macOS, install the reviewed Brewfile:

```bash
brew bundle install --file="$HOME/zendots/pkgs/Brewfile"
```

On Arch/CachyOS, review `pkgs/arch/install_core.sh`, `install_niri.sh`,
`install_misc.sh`, and `install_latex.sh`, then run only the scripts you need.
These scripts install packages and may enable services; they are not dry runs.
They do not replace the separate Noctalia v5 setup described in its guide.

### Preview, then apply selected paths

Edit the source first. Always use **destination paths** and recursive previews:

```bash
chezmoi edit ~/.zshrc
chezmoi diff -r ~/.zshrc ~/.shell_exports ~/.shell_aliases
```

Review that diff before applying the same paths:

```bash
chezmoi apply ~/.zshrc ~/.shell_exports ~/.shell_aliases
```

Repeat for each selected config. Never use an unscoped apply to pick up a small
change. Apply hooks can also relink Claude skills and enable the agent-update
scheduler; inspect `.chezmoiscripts/` before deployment. Agents must show the
scoped diff and obtain approval before any apply.

After deploying the relevant tool configs:

```bash
bash ~/zendots/pkgs/pipx_packages.sh          # installs copier
bash ~/zendots/pkgs/download_yazi_plugins.sh # installs the configured Yazi plugins
bat cache --build
```

If `~/.tmux/plugins/tpm` does not exist, clone
`https://github.com/tmux-plugins/tpm` there. Start tmux and press `Ctrl-a`, then
`Shift-i` to install plugins. The older `pkgs/misc_setup.sh` has a broken bat
invocation; use the explicit cache command above instead.

Homebrew and Arch lists include fonts. Licensed fonts are installed separately.
On Linux, `bash ~/.local/bin/font-install.sh /path/to/font.otf otf` copies a
font into `~/.local/share/fonts/otf` and refreshes fontconfig.

### Another Mac

[Setting up another Mac](docs/new-mac.md) makes a new Mac a copy of macmini in
two sittings. `pkgs/macos/provision.sh` runs on macmini and seeds the new Mac
over SSH: keys, the chezmoi config, one-time app data, and Syncthing sharing.
`pkgs/macos/setup-mac.sh` runs on the new Mac after the first apply: Brewfile,
`defaults.sh`, `login-items.sh`, and tool plugins.

## Daily use

### Source and live configuration

Most files flow from this checkout into home. For an app that rewrites its own
config, capture intentional GUI changes before applying over them. For example,
see the [OmniWM capture workflow](docs/omniwm.md#maintaining-the-config).

Claude, Codex, and Serena use modify templates: the fragments in
`.chezmoidata/` own selected keys, while other live keys are preserved except
explicitly retired plugin registrations. See the
[Ponytail retirement record](docs/maintenance/2026-10-20-ponytail-retirement.md).
Capture changes to those managed keys with:

```bash
just capture codex # also accepts claude or serena; writes the source fragment
```

Review the fragment before the next scoped preview/apply. Missing managed paths
abort capture without writing. This is not a full import of the live config.
`chezmoi-sync-from-home.sh` offers an interactive picker for diverged managed
files, re-adding ordinary files or opening a merge for templates.

### Just recipes

Run `just --list --unsorted` for the available recipes:

| Recipe | Effect |
| --- | --- |
| `just install` | Install `pkgs/Brewfile` with Homebrew |
| `just dump` | Delete and regenerate the Brewfile from installed packages; this drops the curated list (see below) |
| `just skills …` | Forward arguments to `agent-skills.sh` |
| `just link-skills` | Relink shared skills into Claude Code |
| `just capture claude\|codex\|serena` | Capture live managed keys into `.chezmoidata/` |
| `just sync-from-home` | Interactively capture diverged managed files |
| `just sync-gtk` | Record live GTK 3/4 settings in the source |

The Brewfile is curated: it lists apps macmini runs but installed outside
Homebrew, and leaves out apps installed there that new Macs skip. Edit it by
hand rather than with `just dump`, which would undo both.

`just apply` / `just a` and `just diff` / `just d` are still **unscoped** wrappers.
Use explicit `chezmoi diff -r <paths>` and approved `chezmoi apply <paths>` instead.

### Shared agent skills

`~/.agents/skills/` is the canonical store, vendored as `dot_agents/skills/`.
**Edit skills in the home store**, then record them through the wrapper:

```bash
agent-skills.sh sync   # record hand edits back into chezmoi
agent-skills.sh update # update upstream-locked skills
```

Install with `agent-skills.sh add <owner>/<repo>`, not bare `npx skills`.
Check for an existing store entry or enabled Claude plugin first. When a
repository contains existing locally maintained skills, select only new skills;
a broad reinstall can overwrite local adaptations. The lock identifies upstream
installs; skills absent from it are locally maintained.

Only Claude Code needs store symlinks; Codex and OpenCode discover the store
natively. Plugin-provided skills shared with other harnesses link to the plugin
checkout rather than copying it. Install on one machine only, wait for Syncthing,
then preview and approve the relevant skill destinations on the other machine.
Fetched runtimes use `agent-skills.sh fetch`; none is currently pinned.

The existing [independent-review skill](dot_agents/skills/independent-review/SKILL.md)
handles change reviews and repository or folder audits. Ask to "audit this
repository" or "audit this folder"; no extra activation command is needed.
Audits inspect the named current working tree, including existing defects and
non-ignored untracked files, and work on a clean tree. Change reviews retain
their introduced-defect requirement. Both use fresh finders and independent
verifiers. Performance findings must connect a concrete consequence to expected
load supported by repository evidence, including tests or code bounds, with
assumptions stated.

### OpenCode V2 and Pi

OpenCode's server configuration is `~/.config/opencode/opencode.json`; terminal
settings are in `cli.json`, and custom agents in `agents/`. The configured
default is `plan` with `openai/gpt-6.1-sol` and high reasoning. The CLI theme is
Catppuccin dark. Its template includes Orca's status plugin only when the local
entrypoint exists; preview/apply `cli.json` again after installing Orca.

Notifier uses a pinned package version. Superpowers is pinned to a
full Git commit and registers its own skills. Update that pin in `opencode.json`,
not a separate checkout. `sync_skill_collections.sh` only removes known legacy
Superpowers symlinks and leaves the old checkout alone. Refer to the
[OpenCode V2 guides](https://opencode.ai/v2/docs/) for configuration fields.

Pi's persistent modes, custom agents, package configuration, and session handoff
are documented in the [Pi workflow guide](docs/pi-workflow.md).

### Key bindings

| Surface | Binding | Action |
| --- | --- | --- |
| tmux (prefix `Ctrl-a`) | `prefix + h` / `v` | Top/bottom / left/right split |
| tmux | `prefix + o` | sesh/tmuxp session picker |
| tmux | `prefix + r` | Reload config |
| tmux | `Ctrl-Shift-h` / `l` | Previous/next window, without wrapping |
| tmux | `Alt + arrows` | Resize pane |
| Zsh | `Ctrl-r` | atuin history search |
| Zsh | `Ctrl-t` | television smart completion |
| Zsh | `Alt-e` | Generate a command from the current buffer with aichat |
| Neovim (leader `Space`) | `<leader>ff` / `<leader>fg` | Files / Git files |
| Neovim | `<leader>sg` / `<leader>gl` | Grep / Lazygit |

`ta [name|path]` opens the session picker or connects to a target.
`tnew <name> [dir]` registers a sesh session and creates/attaches the standard
tmuxp layout. `~/.config/sesh/sesh.toml` is intentionally machine-local.
Full editor mappings live in `private_dot_config/nvim/lua/keymaps/`; desktop
shortcuts are in the [OmniWM](docs/omniwm.md) and [Noctalia](docs/noctalia-v5.md)
guides and the Niri config.

## Synchronization and maintenance

`work-sync` is implemented in `tools/work-sync/` and reads the private
`~/.config/work-sync/folders.json` manifest. Use `work-sync --help` for commands:

- `add`: register a project folder at the same relative path on every
  reachable machine.
- `add-device <machine>`: share every manifest folder with one machine, such as
  a new Mac or one that was offline during `add`; safe to rerun. A machine that
  missed an `add` first needs a scoped `chezmoi apply ~/.config/work-sync/folders.json`.
- `status`: show each folder's Syncthing state on every machine.
- `bootstrap <label>`: preview managed Syncthing rules; `--apply` installs them.
- `conflicts <path>`: read-only conflict scan; review before using `--apply`.
- `handoff <target> --dry-run`: inspect transfer of **external Orca worktrees**.

Main project checkouts, including normal `.git` state, sync through Syncthing;
only worktree-local Git state and transient locks stay local. Use one host at a
time and wait for Up to Date before switching. Machines are macmini, macbook,
and tsuki; unreachable ones are skipped. A Mac other than macmini names itself
in `~/.config/work-sync/host`, which `provision.sh` writes. A tracked `.stignore` belongs to
the project; the helper validates it rather than rewriting it.

Update each tool through its own manager:

```bash
brew update && brew upgrade # Homebrew packages on macOS
# In Neovim: :Lazy sync
ya pkg upgrade
agent-skills.sh update
# tmux plugins: prefix + U
```

`agent-update` invokes installed agent clients' own update commands. Apply hooks
schedule it with systemd on Linux and launchd on macOS. It does not refresh all
plugin marketplaces or perform remote MCP login. The
[dated agent maintenance record](docs/maintenance/2026-10-20-agent-updates.md)
describes the last recorded cross-host checks, not reproducible package pins.

After repository synchronization, preview the selected destination paths and
apply only after approval. Do not chain a pull with a broad apply.

## Troubleshooting

- **Changes missing:** check `chezmoi source-path`, then `chezmoi status <path>`.
  Directory diffs require `chezmoi diff -r <path>`.
- **Managed GUI settings keep reverting:** capture intentional changes first;
  Noctalia's local state can also override its managed config.
- **Tmux plugins missing:** check `~/.tmux/plugins/tpm`, then `prefix + I`.
- **Neovim language server missing:** use `:Mason` to inspect/install it.
- **Skill edits disappear:** edit `~/.agents/skills/`, not the vendored source,
  and run `agent-skills.sh sync`.

## Documentation

- [Setting up another Mac](docs/new-mac.md)
- [OmniWM setup and shortcuts](docs/omniwm.md)
- [Noctalia v5 configuration and maintenance](docs/noctalia-v5.md)
- [Pi workflows and session handoff](docs/pi-workflow.md)
- [Dated cross-host maintenance record](docs/maintenance/2026-10-20-agent-updates.md)
- [Ponytail retirement and pending deployment](docs/maintenance/2026-10-20-ponytail-retirement.md)
- [Repository agent guidance](CLAUDE.md) and [review rules](REVIEW.md)

`docs/plans/` and `docs/superpowers/` are ignored local planning directories,
not published setup guides. Remaining material covers unresolved command-guard
deployment checks, workflow-skill proposals, and the agent-worklog proposal with
its editable diagram sources. Treat those as plans, not installed features.

## License and credits

[MIT](LICENSE). Built on chezmoi, Catppuccin, Neovim's plugin ecosystem, and the
many upstream tools and configurations referenced here.

# CLAUDE.md

Repository guidance shared by coding agents. `AGENTS.md` is a symlink to this file.

## Overview

This is a **dotfiles repository** (zendots) managed by [chezmoi](https://www.chezmoi.io/), a dotfile manager that uses templates to maintain configuration files across different machines. The repository contains comprehensive configurations for a modern terminal-based development environment built around Neovim, Zsh, Tmux, and various CLI tools.

The managed hosts are tsuki (CachyOS Linux, Niri + native Noctalia v5),
macmini (macOS, OmniWM), and macbook (the LBNL MacBook, a copy of macmini; see
`docs/new-mac.md`). AeroSpace/SketchyBar and Hyprland/Waybar configs
remain available. See `README.md` and the operational guides in `docs/`.

## Repository Structure

The repository follows chezmoi's naming conventions where files/directories are prefixed with special markers:

- `dot_` → Files that become `.filename` in the home directory (e.g., `dot_gitconfig` → `~/.gitconfig`)
- `private_dot_` → Private files (e.g., `private_dot_config/` → `~/.config/`)
- `executable_` → Scripts that should be executable
- `.chezmoiignore` → Files to exclude from chezmoi management (includes justfile, temp.py, bin/, etc.)

### Key Directories

- **`private_dot_config/`** → Main configuration directory (`~/.config/`)
  - `nvim/` → Neovim configuration (lazy.nvim-based plugin system)
  - `tmux/` → Tmux configuration with custom status bar and scripts
  - `yazi/` → File manager configuration
  - `aichat/` → AI chat CLI configuration
  - `lazygit/`, `kitty/`, `ghostty/`, `warp/` → Various tool configs
  - `starship.toml`, `ohmyposh/` → Shell prompt configurations

- **`pkgs/`** → Package management scripts
  - `Brewfile` → Homebrew package inventory for macOS; Linux scripts live in `arch/` and `fedora/`
  - `download_yazi_plugins.sh` → Installs yazi plugins via `ya pkg`
  - `pipx_packages.sh` → Python packages to install with pipx
  - `misc_setup.sh` → Older post-setup helper; its bat invocation is broken, so use `bat cache --build` directly

- **`private_dot_local/bin/`** → Custom executable scripts

- **`dot_agents/skills/`** → Agent skills, shared by every harness (`~/.agents/skills/`)

- **`dot_pixi/`** → Pixi package manager manifests

## Common Commands

### Chezmoi Operations

```bash
# Preview what a changed path would do (diff is not recursive without -r)
chezmoi diff -r ~/.zshrc

# Apply only the paths you changed, once the diff is approved
chezmoi apply ~/.zshrc
# `just apply` / `just diff` run the unscoped forms; see "Applying changes"

# Edit a file in the repository (chezmoi will handle the dot_ prefix translation)
chezmoi edit ~/.zshrc
```

### Agent Skills

`~/.agents/skills/` is the single store, vendored as `dot_agents/skills/`.
Chezmoi reproduces the vendored skill files without a network fetch.

```bash
agent-skills.sh update
agent-skills.sh sync # after editing any skill in the home store
```

Install new skills with `agent-skills.sh add <owner>/<repo>` (or `just skills
add …`). Check for existing local adaptations and plugin duplicates first;
do not reinstall an entire collection over existing locally maintained skills.

To author a skill, invoke the `create-skill` skill; it covers layout, the
manual-only frontmatter for each harness, and recording the result.

Every skill absent from `~/.agents/.skill-lock.json` (`humanizer`, `open-pr`,
`create-skill`, `find-docs`, and the rest) is locally maintained. Do not
reinstall them from upstream. Edit `~/.agents/skills/<name>/SKILL.md`, then run
`agent-skills.sh sync`. A broad `agent-skills.sh add mattpocock/skills` or
`agent-skills.sh add cursor/plugins` reinstalls every skill in that repository,
lock entry or not, and would overwrite these adaptations; when adding from
those repositories, select only skills that do not already exist in the store.

Always install through `agent-skills.sh`, never a bare `npx skills`: the wrapper
runs the installer from `$HOME` (it installs project-locally when the cwd is a
git repo) and then `chezmoi add`s the store, so the install is never left
unrecorded. Commit afterwards; the source reaches the other machine over
Syncthing, where `chezmoi apply ~/.agents` lands it. A scoped apply skips
`run_after` scripts, so for a new skill also run
`~/.local/bin/link-agent-skills.sh` there to create its Claude link. Install
a given skill on one machine only -- both write to the same synced source, so
installing on both produces Syncthing conflict files.

To retire a locally maintained skill, `chezmoi forget --force` and delete its
store directory, then list the store path and its `~/.claude/skills` and
`~/.pi/agent/skills` links in `.chezmoiremove`. On the other machine, apply
those paths before any `agent-skills.sh` command; the wrapper refuses to record
a retired skill that is still in the store, because adding it back leaves
chezmoi with a source entry and a removal for the same path.

- **Only Claude Code needs symlinks.** Codex and OpenCode resolve
  `~/.agents/skills` natively -- `npx skills` classifies them as "universal" and
  writes no link. Never link a store skill into `~/.codex/skills` or
  `~/.config/opencode/skills`; that makes those harnesses load it twice.
  `link-agent-skills.sh` handles `~/.claude/skills`. `agent-skills.sh` and a
  bare `chezmoi apply` run it; a scoped apply does not.
- **Check for an existing Claude plugin before adding a skill to the store.**
  The store is visible to Claude Code through those symlinks, so adding a skill
  an enabled plugin already provides puts two copies in one session. Compare
  against `~/.claude/plugins` and `enabledPlugins` in `~/.claude/settings.json`.
- OpenCode V2 loads Superpowers from a pinned Git package in `opencode.json`;
  its plugin registers the skills and bootstrap. Do not add its skills to
  `~/.agents/skills` or link its plugin separately, which would duplicate them.
  `~/.config/opencode/sync_skill_collections.sh` now removes only the legacy
  helper's known symlinks and leaves the old unmanaged checkout untouched.
- **A plugin skill wanted in another harness is linked, not copied.**
  `~/.config/opencode/skills/frontend-design` and
  `~/.codex/skills/frontend-design` are chezmoi-managed relative symlinks into
  `~/.claude/plugins/marketplaces/claude-plugins-official/`, the checkout the
  plugin auto-updater pulls, so every harness tracks the plugin. Disabling that
  plugin or removing the marketplace dangles the links.

#### Fetched skills

A skill that carries an upstream runtime -- a Node package, a binary -- is
*fetched* rather than installed. None is fetched now; `archify` was the only one
until it was retired in October 2026. The runtime is cloned to `~/.agents/runtimes/<name>`,
which is never `chezmoi add`ed, and only a relative symlink enters the store, so
the payload reaches neither this repository nor Syncthing.

```bash
# Replace the quoted placeholders with a repository and skill name.
agent-skills.sh fetch "owner/repo" --path "skill-name" # SKILL.md is not at repo root
agent-skills.sh fetch                                 # restore missing runtimes, follow pins
agent-skills.sh fetch --bump "skill-name"              # move the pin to the ref's tip
agent-skills.sh remove "skill-name"                   # works for either kind
```

- **Run `agent-skills.sh fetch` on a new machine.** `chezmoi apply` reproduces
  the symlink but not its target. Until the runtime is cloned the link dangles,
  `link-agent-skills.sh` skips it, and the skill is simply absent rather than
  broken.
- **Pinned to a commit, not a branch.** Both machines run the same revision;
  `fetch --bump` is the deliberate upgrade; on the other machine, a plain
  `fetch` after `chezmoi apply ~/.agents` moves the runtime to the new pin.
  Never `git pull` in a runtime, or the two machines silently diverge.
- **Never `add` a fetched name.** `skills add` recursively removes the canonical
  path before copying, so it would replace the symlink with the whole upstream
  tree and the next `chezmoi add` would vendor it. The wrapper refuses to record
  a store whose fetched link is missing; restore it with `agent-skills.sh fetch`.
- **Never hand-create the store entry.** `fetch` refuses when
  `~/.agents/skills/<name>` exists and is not its own link, because
  `chezmoi apply --force ~/.agents` replaces a real directory with the symlink
  and deletes its contents without listing them.
- `fetch` deletes `scripts/check-update.mjs` after every checkout. archify ran
  it on each use to contact a remote manifest, and its SKILL.md said to continue
  silently when the checker could not run.

### Syncthing project folders

`.stignore` is Syncthing's per-folder ignore file. Syncthing never synchronizes
the file itself. A Git-tracked `.stignore` belongs to that repository; the
helper validates its manifest patterns and never edits it. For an untracked
`.stignore`, `work-sync bootstrap` writes the managed rules independently on
each machine from `~/.config/work-sync/folders.json`, then adds the file to
that checkout's `.git/info/exclude`. Do not ignore `.stignore` globally or add it
to project `.gitignore` files.

New folders use the same relative path beneath `/Volumes/WorkSSD` on macmini
and macbook and `/home/dileep/Documents` on tsuki. Run `work-sync add` from the
new folder, or pass its path explicitly. The command detects Git repositories,
previews the paths, updates the private manifest, configures Syncthing on every
reachable machine, and waits for them. A machine that was unreachable catches up
with a scoped `chezmoi apply ~/.config/work-sync/folders.json` there, then
`work-sync add-device <machine>`. Use `--type container` only for a non-Git parent containing nested Git
repositories; `--yes` skips the confirmation prompt.

Project folders sync their complete normal Git repository, including `.git`.
Only `.git/worktrees`, `.git/config.worktree`, `.git/FETCH_HEAD`, and transient
Git lock files stay local because linked worktree indexes, paths, filesystem
settings, and active locks are machine-specific. Background fetches rewrite
`FETCH_HEAD` often enough to make Syncthing pulls fail. Shared branch and remote configuration remains in
`.git/config`. Use one machine at a time and wait for Syncthing to report `Up to
Date` before opening the repository on the other machine.

The shared defaults cover disposable caches and machine-local runtime state.
Files such as `.env`, `.claude/settings.json`, `.codex/config.toml`, and
`.pi/settings.json` sync by default. If one is machine-specific for a particular
project, add its pattern to that project's `ignore` list in the manifest, then
rerun `work-sync bootstrap <label> --apply`. Extra lines added directly
to one `.stignore` stay local to that machine.

`work-sync handoff` is only for external Orca worktrees, including older
worktrees still registered from Superset paths. Main checkout Git state belongs
to Syncthing. Run `work-sync conflicts <path>` before deleting any
`.sync-conflict-*` file; add `--apply` only after reviewing the scan.
Use a manifest entry's optional `worktree_ignore` list for machine-local data in
external worktrees; it does not change the main folder's Syncthing ignores.

### Package Management

```bash
# Install all packages from Brewfile
just install

# The Brewfile is curated (apps installed outside Homebrew are listed, skipped
# ones are not); edit it by hand. `just dump` regenerates it from installed
# packages and undoes that.

# Install Yazi plugins
bash pkgs/download_yazi_plugins.sh

# Rebuild the bat cache
bat cache --build
```

Run those commands from the repository root.
For TPM, clone `https://github.com/tmux-plugins/tpm` into `~/.tmux/plugins/tpm`
only if missing, then use the plugin-install shortcut below.

### Tmux Plugin Installation

After applying dotfiles with tmux configuration:

1. Start tmux
2. Press `prefix + I` (Ctrl-a + Shift-i) to install plugins via TPM

### Testing Configuration Changes

When modifying configurations:

- **Shell changes**: Source the file or restart shell (`exec zsh`)
- **Tmux changes**: Reload with `prefix + r` (Ctrl-a + r)
- **Neovim changes**: Restart Neovim or use `:Lazy sync` for plugins
- **Repo policy**: Do not add automated tests for dotfiles or shell helpers in this repository unless explicitly requested. Prefer targeted verification commands and manual checks instead.

## Architecture and Configuration System

### Chezmoi Workflow

This repository is the **source** for dotfiles. The typical workflow is:

1. **Modify files** in this repository (using `dot_` prefixes for dotfiles)
2. **Run `chezmoi diff -r <destination paths>`** to preview what will change
3. **Run `chezmoi apply <destination paths>`** once the diff is approved (see the agent rules below)

Do not directly edit files in `~/.config/` or `~/` if they are managed by chezmoi - edit them in this repository instead.

**Exception: `~/.agents/skills/` flows the other way.** `agent-skills.sh`
records the store with `chezmoi add`, which copies home over the source, so a
repo-side edit to `dot_agents/skills/**` is silently discarded by the next
`add`, `fetch`, or `sync`. Edit `~/.agents/skills/<name>/SKILL.md`, then run
`agent-skills.sh sync`. This applies to every skill, installed or
hand-authored, not only the locally maintained ones. On the other machine,
`chezmoi apply ~/.agents/skills/<name>` is still how the change lands; for a
new skill, then run `~/.local/bin/link-agent-skills.sh`.

#### Applying changes (agent rules)

- **Never run a bare `chezmoi apply`.** Always scope it to the target paths you
  actually modified: `chezmoi apply ~/.config/niri/config.kdl ~/.config/mimeapps.list`.
  A bare apply sweeps in unrelated pending changes (e.g. `.agents/.skill-lock.json` churn).
- **Ask for confirmation before applying.** Show the scoped `chezmoi diff -r <paths>`
  first and wait for the user to approve. Do not apply as part of a larger action.
- Use the **destination** paths (`~/.config/...`), not the source names (`private_dot_config/...`).
- **Always pass `-r` to `chezmoi diff`.** Unlike `chezmoi status`, `diff` is not
  recursive by default, so `chezmoi diff ~/.agents/skills/open-pr` prints nothing
  for a directory that has pending changes. Silence from `diff` is not proof of a
  clean path; `chezmoi status <path>` is the reliable check.
- `[diff] pager` is empty so the output is plain git-format text that survives a
  pipe. For a prettier read by hand, pipe it: `chezmoi diff -r ~/.zshrc | delta`.

### Theme Consistency

The entire environment uses **Catppuccin Mocha** color scheme:

- Shell (via Oh-My-Posh config)
- Neovim (catppuccin theme)
- Tmux (custom color variables)
- Terminal (kitty, ghostty, warp configs)
- Tools (bat, fzf, lazygit via delta)

## Important Files to Modify

When making changes to configurations, edit these files in the repository:

- **Shell**: `dot_zshrc.tmpl`, `dot_shell_exports.tmpl`, `dot_shell_aliases.tmpl`
- **Neovim**: Files in `private_dot_config/nvim/lua/`
- **Tmux**: `private_dot_config/tmux/tmux.conf`
- **Git**: `dot_gitconfig`, `dot_gitignore_global`
- **Packages**: `pkgs/Brewfile`

After editing managed configuration, show the scoped `chezmoi diff -r` and
apply only the approved paths, as described under "Applying changes".
Repository-only docs are ignored by chezmoi and need no apply.

## Chezmoi File Name Translation

When working with this repository, remember chezmoi naming:

- `dot_zshrc.tmpl` → `~/.zshrc` (rendered per host)
- `private_dot_config/nvim/init.lua` → `~/.config/nvim/init.lua`
- `private_dot_local/bin/executable_script.sh` → `~/.local/bin/script.sh` (executable)

When suggesting file paths to the user, use the actual paths (`~/.zshrc`), but when making changes in this repository, use the chezmoi names (`dot_zshrc.tmpl`).

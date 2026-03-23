# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **dotfiles repository** (zendots) managed by [chezmoi](https://www.chezmoi.io/), a dotfile manager that uses templates to maintain configuration files across different machines. The repository contains comprehensive configurations for a modern terminal-based development environment built around Neovim, Zsh, Tmux, and various CLI tools.

## Repository Structure

The repository follows chezmoi's naming conventions where files/directories are prefixed with special markers:

- `dot_` → Files that become `.filename` in the home directory (e.g., `dot_zshrc` → `~/.zshrc`)
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
  - `Brewfile` → Homebrew bundle file listing all packages
  - `download_yazi_plugins.sh` → Installs yazi plugins via `ya pkg`
  - `pipx_packages.sh` → Python packages to install with pipx
  - `misc_setup.sh` → Post-setup tasks (rebuild bat cache, clone tpm)

- **`private_dot_local/bin/`** → Custom executable scripts

- **`dot_pixi/`** → Pixi package manager manifests

## Common Commands

### Chezmoi Operations

```bash
# Apply dotfiles from repository to home directory
just apply
# or
chezmoi apply

# Show diff between repository and current home directory
just diff
# or
chezmoi diff

# Edit a file in the repository (chezmoi will handle the dot_ prefix translation)
chezmoi edit ~/.zshrc
```

### Package Management

```bash
# Install all packages from Brewfile
just install
# or
cd pkgs && brew bundle install

# Update Brewfile with currently installed packages
just dump
# or
cd pkgs && rm Brewfile && brew bundle dump

# Install Yazi plugins
cd pkgs && ./download_yazi_plugins.sh

# Post-installation setup (bat cache rebuild, TPM clone)
./pkgs/misc_setup.sh
```

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
2. **Run `chezmoi apply`** to sync changes to the actual home directory
3. **Run `chezmoi diff`** to preview what will change before applying

Do not directly edit files in `~/.config/` or `~/` if they are managed by chezmoi - edit them in this repository instead.

### Theme Consistency

The entire environment uses **Catppuccin Mocha** color scheme:

- Shell (via Oh-My-Posh config)
- Neovim (catppuccin theme)
- Tmux (custom color variables)
- Terminal (kitty, ghostty, warp configs)
- Tools (bat, fzf, lazygit via delta)

## Important Files to Modify

When making changes to configurations, edit these files in the repository:

- **Shell**: `dot_zshrc`
- **Neovim**: Files in `private_dot_config/nvim/lua/`
- **Tmux**: `private_dot_config/tmux/tmux.conf`
- **Git**: `dot_gitconfig`, `dot_gitignore_global`
- **Packages**: `pkgs/Brewfile`

After editing, run `chezmoi apply` to sync changes to the home directory.

## Chezmoi File Name Translation

When working with this repository, remember chezmoi naming:

- `dot_zshrc` → `~/.zshrc`
- `private_dot_config/nvim/init.lua` → `~/.config/nvim/init.lua`
- `private_dot_local/bin/executable_script.sh` → `~/.local/bin/script.sh` (executable)

When suggesting file paths to the user, use the actual paths (`~/.zshrc`), but when making changes in this repository, use the chezmoi names (`dot_zshrc`).

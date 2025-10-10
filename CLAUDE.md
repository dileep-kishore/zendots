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

## Architecture and Configuration System

### Chezmoi Workflow

This repository is the **source** for dotfiles. The typical workflow is:

1. **Modify files** in this repository (using `dot_` prefixes for dotfiles)
2. **Run `chezmoi apply`** to sync changes to the actual home directory
3. **Run `chezmoi diff`** to preview what will change before applying

Do not directly edit files in `~/.config/` or `~/` if they are managed by chezmoi - edit them in this repository instead.

### Shell Configuration (Zsh)

The shell setup uses **Zinit** as the plugin manager (auto-installs if not present):

- **Core location**: `dot_zshrc` (becomes `~/.zshrc`)
- **Plugin manager**: Zinit with fast-syntax-highlighting, zsh-autosuggestions, zsh-completions
- **Oh-My-Zsh plugins**: Loaded selectively (git, git-extras, aliases, direnv, tmux, etc.)
- **Vi mode**: `zsh-vi-mode` plugin enabled
- **Prompt**: Oh-My-Posh (configured at `~/.config/ohmyposh/config.json`)
- **Tools integrated**:
  - `zoxide` (cd replacement)
  - `atuin` (shell history, bound to Ctrl-r)
  - `tv` (television)
  - `carapace` (completions)
  - `fzf` with custom Catppuccin theme
- **AI integration**: `aichat` bound to Alt-e for AI-assisted command generation
- **API keys**: Loaded from `~/.secrets/` for OpenAI, Anthropic, Gemini, Tavily

### Neovim Configuration

- **Plugin manager**: lazy.nvim
- **Entry point**: `private_dot_config/nvim/init.lua`
- **Structure**: Modular Lua configuration split into:
  - `lua/options.lua` → Core editor options
  - `lua/keymaps/` → Key bindings
  - `lua/autocmds.lua` → Auto commands
  - `lua/config/lazy.lua` → Lazy.nvim setup
  - `lua/plugins/` → Plugin configurations organized by category:
    - `lsp/` → LSP setup (Mason, formatters, linters, lspsaga, symbol-usage)
    - `git/` → Git integration (gitsigns, neogit, diffview, octo)
    - `completions/` → Completion plugins
    - `bars/` → Status/tab bars (lualine, tabby, incline)
    - `themes/` → Color schemes (catppuccin, rosepine)
    - `ui/` → UI enhancements (snacks.lua)

- **Theme**: Catppuccin Mocha (applied by default)
- **Special plugins**:
  - `chezmoi.lua` → Chezmoi integration for editing dotfiles from within Neovim
  - `sidekick.nvim` → Working with AI assistants

### Tmux Configuration

- **Prefix key**: `Ctrl-a` (instead of default Ctrl-b)
- **Plugin manager**: TPM (Tmux Plugin Manager)
- **Session manager**: `sesh` bound to `prefix + o` (Ctrl-a + o)
- **Theme**: Custom Catppuccin Mocha colors with custom status bar
- **Custom scripts** in `private_dot_config/tmux/scripts/`:
  - `custom_number.sh` → Custom window numbering
  - `window_icon.sh` → Dynamic window icons based on running process
  - `git_status.sh`, `wb_git_status.sh` → Git status in status bar
  - `find_git_root.py` → Find git repository root for display
  - `uptime_fmt.sh` → Format system uptime
  - `templater.sh` → Tmuxinator template generator

- **Key bindings**:
  - `prefix + h/v` → Split horizontally/vertically
  - `Ctrl-Shift-h/l` → Switch windows
  - `Alt + arrows` → Resize panes
  - Vi mode in copy mode

### AI Tools Integration

The repository includes configuration for AI-powered development tools:

- **aichat**: CLI AI assistant with shell binding (Alt-e) for command generation
- **API credentials**: Stored in `~/.secrets/` directory (not in repository)
  - `openai.txt`, `anthropic.txt`, `gemini.txt`, `tavily.txt`
- **Neovim AI plugins**: sidekick.nvim configured for AI assistance
- **claude-code**: Added to Brewfile for this tool

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

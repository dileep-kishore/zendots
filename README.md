# zendots

**Zen dotfiles - A modern, minimal terminal-based development environment**

A comprehensive dotfiles repository managed by [chezmoi](https://www.chezmoi.io/), featuring configurations for Neovim, Zsh, Tmux, and various CLI tools. Built for productivity with keyboard-centric and terminal-based workflows and consistent theming across all tools.

**Be sure to ⭐️ or 🔱 this repo if you find it useful! 😃**

## Screenshots

<!-- TODO: Add screenshots -->

![Terminal Setup](assets/terminal.png)
![Neovim Setup](assets/neovim.png)
![Tmux Workflow](assets/tmux.png)

## Setup

- **Dotfile Manager**: [chezmoi](https://www.chezmoi.io/)
- **Shell**: Zsh with [Zinit](https://github.com/zdharma-continuum/zinit) plugin manager
- **Prompt**: [Oh-My-Posh](https://ohmyposh.dev/)
- **Terminal**: [Ghostty](https://ghostty.org/), [Kitty](https://sw.kovidgoyal.net/kitty/), and [Warp](https://www.warp.dev/)
- **Editor**: [Neovim](https://neovim.io/) with [lazy.nvim](https://github.com/folke/lazy.nvim)
- **Multiplexer**: [Tmux](https://github.com/tmux/tmux) with [TPM](https://github.com/tmux-plugins/tpm)
- **File Manager**: [Yazi](https://yazi-rs.github.io/)
- **Git UI**: [Lazygit](https://github.com/jesseduffield/lazygit)
- **Theme**: [Catppuccin Mocha](https://catppuccin.com/) (consistent across all tools)
- **Fonts**: Monaspace, Dank Mono, MonaLisa, Cartograph, Fira Code, Victor Mono, Cascadia Code, Recursive, Maple Mono, SN-Pro, IA-Writer, Font Awesome
- **AI Tools**: [aichat](https://github.com/sigoden/aichat), [claude-code](https://claude.com/claude-code)
- **Package Managers**: [Homebrew](https://brew.sh/), [pipx](https://pipx.pypa.io/), [pixi](https://pixi.sh/)

## Features

### 🎨 Consistent Theming

- Catppuccin Mocha color scheme across shell, editor, terminal, and all CLI tools
- Custom Oh-My-Posh prompt with git integration
- Beautiful status bars in both Neovim and Tmux

### ⚡ Productivity Tools

- **Shell enhancements**: `zoxide` (smart cd), `atuin` (shell history), `fzf` (fuzzy finder), `eza` (modern ls)
- **AI integration**: Command generation with `aichat` (Alt-e), AI-assisted editing in Neovim
- **Session management**: Tmux with `sesh` for quick session switching (Ctrl-a + o)
- **Git workflow**: Enhanced git commands, lazygit, neogit, octo.nvim for GitHub

### 🔧 Developer Experience

- **LSP support**: Full language server protocol setup with Mason
- **Smart completions**: nvim-cmp with multiple sources
- **Code formatting**: Automatic formatting with conform.nvim
- **Git integration**: Inline blame, diff view, conflict resolution
- **Tmux workflows**: Custom window icons, git status in status bar, split management

### 📦 Package Management

- Declarative package installation via Brewfile
- Python tools managed with pipx
- Project-specific environments with pixi
- Plugin managers for Tmux, Neovim, Zsh, and Yazi

## Installation

### Prerequisites

1. Install [Homebrew](https://brew.sh/) (macOS/Linux)
2. Install chezmoi:
   ```bash
   brew install chezmoi
   ```

### Quick Start

1. **Clone and initialize dotfiles**:

   ```bash
   # Initialize chezmoi with this repository
   chezmoi init https://github.com/dileep-kishore/zendots.git

   # Preview what will be changed
   chezmoi diff

   # Apply the dotfiles
   chezmoi apply
   ```

2. **Install packages**:

   ```bash
   # Install all Homebrew packages
   cd ~/.local/share/chezmoi/pkgs
   brew bundle install

   # Install Yazi plugins
   ./download_yazi_plugins.sh

   # Install Python packages
   ./pipx_packages.sh

   # Run miscellaneous setup tasks
   ./misc_setup.sh
   ```

3. **Setup Tmux plugins**:

   ```bash
   # Start tmux
   tmux

   # Install plugins (inside tmux)
   # Press: Ctrl-a + Shift-i
   ```

### Font Setup (Manual)

Install the following fonts manually:

1. [Monaspace](https://github.com/githubnext/monaspace)
2. Dank Mono (from patched fonts collection)
3. MonaLisa (from patched fonts collection)
4. Cartograph (from patched fonts collection)
5. [Nerd Fonts](https://www.nerdfonts.com/): Fira Code, Victor Mono, Cascadia Code
6. [Recursive](https://www.recursive.design/)
7. [Maple Mono](https://github.com/subframe7536/maple-font)
8. SN-Pro
9. IA-Writer (Quattro, Duospace)
10. [Font Awesome](https://fontawesome.com/)

## Usage

### Chezmoi Workflow

```bash
# Edit a dotfile (chezmoi handles the dot_ prefix translation)
chezmoi edit ~/.zshrc

# Preview changes before applying
chezmoi diff

# Apply changes from repository to home directory
chezmoi apply

# Quickly edit and apply
chezmoi edit --apply ~/.config/nvim/init.lua
```

### Common Commands

Using the included [justfile](https://github.com/casey/just):

```bash
# Apply dotfiles
just apply

# Show diff
just diff

# Install packages from Brewfile
just install

# Update Brewfile with current packages
just dump
```

### Key Bindings

#### Tmux

- **Prefix**: `Ctrl-a` (instead of default Ctrl-b)
- `prefix + h/v` → Split horizontally/vertically
- `prefix + o` → Session manager (sesh)
- `prefix + r` → Reload configuration
- `Ctrl-Shift-h/l` → Switch windows
- `Alt + arrows` → Resize panes

#### Zsh

- `Ctrl-r` → Search history with atuin
- `Alt-e` → AI-assisted command generation with aichat
- `Ctrl-t` → Fuzzy file finder

#### Neovim (Normal Mode)

- `Space` → Leader key
- `<leader>ff` → Find files
- `<leader>fg` → Live grep
- `<leader>gl` → Open lazygit
- See full keymaps in `private_dot_config/nvim/lua/keymaps/`

## Maintenance

### Updating Packages

```bash
# Update Homebrew packages
brew update && brew upgrade

# Update Neovim plugins
nvim +Lazy sync

# Update Tmux plugins
# Inside tmux: prefix + U

# Update Yazi plugins
ya pack -u
```

### Syncing Dotfiles

```bash
# Pull latest changes
cd ~/.local/share/chezmoi
git pull

# Apply changes
chezmoi apply
```

## Troubleshooting

### Chezmoi not applying changes

Make sure you're editing files in the chezmoi source directory:

```bash
chezmoi cd  # Navigate to source directory
```

### Tmux plugins not loading

1. Ensure TPM is installed: `git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm`
2. Inside tmux, press `prefix + I` to install plugins

### Neovim LSP not working

Run `:Mason` and install the required language servers.

### Shell completions not working

Rebuild the completion cache:

```bash
rm ~/.zcompdump*
exec zsh
```

## Credits and Inspiration

- [chezmoi](https://www.chezmoi.io/) - Dotfile management
- [Catppuccin](https://catppuccin.com/) - Color scheme
- [Neovim](https://neovim.io/) community for amazing plugins
- Various dotfile repositories across GitHub

## License

MIT License - Feel free to use and modify as you wish!

---

**Note**: This is a personal dotfiles repository. While you're welcome to use it as inspiration, you may need to adjust configurations to match your preferences and system setup.

<div align="center">
  <img src="assets/logo.svg" width="120" alt="zendots logo">
  <h1>zendots</h1>
  <p><strong>Zen dotfiles — a modern, minimal, keyboard-centric terminal environment</strong></p>
</div>

A [chezmoi](https://www.chezmoi.io/)-managed dotfiles repository covering Neovim,
Zsh, Tmux, a fleet of AI coding agents, and the CLI tools that hold it all
together. Templated for both macOS (AeroSpace + SketchyBar) and Linux (niri /
Hyprland + Waybar), with Catppuccin Mocha theming throughout.

**Be sure to ⭐️ or 🔱 this repo if you find it useful! 😃**

## The Stack

### Core

| | |
|---|---|
| **Dotfile manager** | [chezmoi](https://www.chezmoi.io/) |
| **Shell** | Zsh + [Zinit](https://github.com/zdharma-continuum/zinit), [carapace](https://carapace.sh/) completions |
| **Prompt** | [Oh-My-Posh](https://ohmyposh.dev/) (with a custom transient prompt) |
| **Terminal** | [Ghostty](https://ghostty.org/), [Kitty](https://sw.kovidgoyal.net/kitty/), [Warp](https://www.warp.dev/) |
| **Editor** | [Neovim](https://neovim.io/) + [lazy.nvim](https://github.com/folke/lazy.nvim) |
| **Multiplexer** | [Tmux](https://github.com/tmux/tmux) + [TPM](https://github.com/tmux-plugins/tpm), [sesh](https://github.com/joshmedeski/sesh), [tmuxp](https://tmuxp.git-pull.com/) |
| **File manager** | [Yazi](https://yazi-rs.github.io/) |
| **Git UI** | [Lazygit](https://github.com/jesseduffield/lazygit) + [delta](https://github.com/dandavison/delta) |
| **Theme** | [Catppuccin Mocha](https://catppuccin.com/), everywhere |

### AI Agents

The agent setup is the part that moves fastest. All of these are configured here:

| | |
|---|---|
| [**Orca**](https://www.onorca.dev/) | Worktree-based agentic IDE — the primary driver ([docs](https://www.onorca.dev/docs)) |
| [**Claude Code**](https://claude.com/claude-code) | `~/.claude` settings, plugins, statusline, MCP servers |
| [**Codex**](https://github.com/openai/codex) | `~/.codex` config, plus [CodexBar](https://codexbar.app/) in the menu bar |
| [**OpenCode**](https://opencode.ai/) | `~/.config/opencode`, incl. oh-my-opencode |
| [**T3 Code**](https://t3.codes/) | Minimal desktop GUI for driving coding agents |
| [**Pi**](https://pi.dev/) | `~/.pi` agent config — see [`docs/pi-workflow.md`](docs/pi-workflow.md) |
| [**aichat**](https://github.com/sigoden/aichat) | Inline shell command generation (`Alt-e`) |
| **Neovim** | [sidekick.nvim](https://github.com/folke/sidekick.nvim), [avante.nvim](https://github.com/yetone/avante.nvim), Copilot |

Skills are vendored once in `dot_agents/skills/` → `~/.agents/skills/`, so
`chezmoi apply` reproduces every skill on a new machine with no network access.
See [Agent skills](#agent-skills) below.

### CLI Toolbelt

| | |
|---|---|
| **Navigate** | [zoxide](https://github.com/ajeetdsouza/zoxide) · [eza](https://eza.rocks/) · [fd](https://github.com/sharkdp/fd) |
| **Search** | [ripgrep](https://github.com/BurntSushi/ripgrep) · [ast-grep](https://ast-grep.github.io/) · [fzf](https://github.com/junegunn/fzf) · [television](https://github.com/alexpasmantier/television) |
| **Read** | [bat](https://github.com/sharkdp/bat) · [glow](https://github.com/charmbracelet/glow) · [rich-cli](https://github.com/Textualize/rich-cli) · [tealdeer](https://github.com/tealdeer-rs/tealdeer) |
| **Inspect** | [btop](https://github.com/aristocratos/btop) · [procs](https://github.com/dalance/procs) · [dua-cli](https://github.com/Byron/dua-cli) · [fastfetch](https://github.com/fastfetch-cli/fastfetch) |
| **Data** | [jq](https://jqlang.github.io/jq/) · [yq](https://github.com/mikefarah/yq) · [jc](https://github.com/kellyjonbrazil/jc) |
| **Git** | [gh](https://cli.github.com/) · [git-delta](https://github.com/dandavison/delta) · [git-cliff](https://git-cliff.org/) · [git-extras](https://github.com/tj/git-extras) |
| **Shell** | [atuin](https://atuin.sh/) · [carapace](https://carapace.sh/) · [direnv](https://direnv.net/) · [vivid](https://github.com/sharkdp/vivid) |
| **Run** | [just](https://github.com/casey/just) · [entr](https://github.com/eradman/entr) · [lazydocker](https://github.com/jesseduffield/lazydocker) · [OrbStack](https://orbstack.dev/) |
| **Languages** | [uv](https://docs.astral.sh/uv/) · [pixi](https://pixi.sh/) · [pipx](https://pipx.pypa.io/) · Node · Go · Rust · Lua |
| **Misc** | [ouch](https://github.com/ouch-org/ouch) · [age](https://github.com/FiloSottile/age) · [aria2](https://aria2.github.io/) · ffmpeg |

Full list: [`pkgs/Brewfile`](pkgs/Brewfile).

### Desktop

- **macOS**: [AeroSpace](https://github.com/nikitabobko/AeroSpace) (tiling), [SketchyBar](https://felixkratz.github.io/SketchyBar/), [borders](https://github.com/FelixKratz/JankyBorders), AltTab, Raycast
- **Linux**: [niri](https://github.com/YaLTeR/niri) or Hyprland, Waybar, walker/wofi, swaync

## Installation

### Prerequisites

Install [Homebrew](https://brew.sh/), then chezmoi:

```bash
brew install chezmoi
```

### Quick Start

```bash
# 1. Initialize, preview, apply
chezmoi init git@github.com:dileep-kishore/zendots.git
chezmoi diff
chezmoi apply

# 2. Install packages
cd ~/.local/share/chezmoi/pkgs
brew bundle install        # Homebrew formulae, casks, fonts
./pipx_packages.sh         # Python CLI tools
./download_yazi_plugins.sh # Yazi plugins
./misc_setup.sh            # bat cache, TPM clone
```

Linux hosts use the platform scripts under `pkgs/arch/` and `pkgs/fedora/`
instead of the Brewfile.

Then start tmux and press `Ctrl-a + Shift-i` to install the tmux plugins.

Fonts install from the Brewfile (Monaspace, Maple Mono NF, SF Mono/Pro, and
several Nerd Fonts). Licensed fonts kept outside Homebrew — Dank Mono,
MonaLisa, Cartograph, IA Writer — install manually with `font-install.sh`.

## Usage

### Chezmoi Workflow

This repository is the **source**. Edit files here, never in `~/.config`.

```bash
chezmoi edit ~/.zshrc              # Edit (handles the dot_ prefix for you)
chezmoi diff ~/.zshrc              # Preview
chezmoi apply ~/.zshrc             # Apply — always scope to the paths you changed
chezmoi edit --apply ~/.config/nvim/init.lua
```

### Just Recipes

```bash
just apply          # chezmoi apply
just diff           # chezmoi diff
just install        # brew bundle install
just dump           # regenerate the Brewfile from installed packages
just skills add …   # install an agent skill
just link-skills    # relink ~/.agents/skills into Claude Code
just capture codex  # capture live config keys back into the managed fragment
```

### Agent skills

`~/.agents/skills/` is the single store for every harness. Always install
through the wrapper so the result gets recorded in chezmoi:

```bash
agent-skills.sh add mattpocock/skills   # or: just skills add …
agent-skills.sh update
agent-skills.sh sync                    # after hand-authoring a skill
```

Only Claude Code needs symlinks (`link-agent-skills.sh`, run on every apply) —
Codex and OpenCode resolve `~/.agents/skills` natively. Install a given skill on
one machine only; the source syncs over Syncthing.

### Key Bindings

**Tmux** — prefix is `Ctrl-a`

| | |
|---|---|
| `prefix + h` / `v` | Split horizontally / vertically |
| `prefix + o` | Session manager (sesh + tmuxp) |
| `prefix + r` | Reload config |
| `Ctrl-Shift-h` / `l` | Switch windows |
| `Alt + arrows` | Resize panes |

**Sessions**

- `ta <name\|path>` — attach to a tmux/sesh session, or create a standard one for a directory
- `tnew <name> [dir]` — register in `~/.config/sesh/sesh.toml`, then create/attach

`sesh.toml` is machine-local and intentionally unmanaged.

**Zsh**

| | |
|---|---|
| `Ctrl-r` | atuin history search |
| `Ctrl-t` | fuzzy file finder |
| `Alt-e` | aichat command generation |

**Neovim** — leader is `Space`

| | |
|---|---|
| `<leader>ff` | Find files |
| `<leader>fg` | Find git files |
| `<leader>sg` | Grep search |
| `<leader>gl` | Lazygit |

Full keymaps: `private_dot_config/nvim/lua/keymaps/`.

## Extras

- **`work-sync`** (`tools/work-sync/`) — manages Syncthing project folders across
  machines: `.stignore` generation, conflict scanning, and Orca worktree handoff.
- **`chezmoi-sync-from-home.sh`** — pull drifted changes back from `~` into the repo.
- **`cfg-capture.py`** — capture keys from a live tool config into its managed fragment.

## Maintenance

```bash
brew update && brew upgrade   # packages
nvim +Lazy sync               # Neovim plugins
ya pkg upgrade                # Yazi plugins
agent-skills.sh update        # agent skills
# tmux plugins: prefix + U
```

Syncing the repo itself:

```bash
chezmoi cd && git pull && chezmoi apply
```

## Troubleshooting

**Changes not applying** — make sure you edited the chezmoi source, not `~`.
`chezmoi cd` gets you there.

**Tmux plugins not loading** — `git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm`, then `prefix + I`.

**Neovim LSP not working** — `:Mason`, install the missing server.

**Shell completions broken** — `rm ~/.zcompdump* && exec zsh`.

## Credits

[chezmoi](https://www.chezmoi.io/) · [Catppuccin](https://catppuccin.com/) ·
the Neovim plugin community · and a long tail of dotfiles repos across GitHub.

## License

MIT. Use and modify as you wish.

---

**Note**: This is a personal dotfiles repository. Take it as inspiration rather
than something to apply wholesale — you will want to adjust it to your own
machines and preferences.

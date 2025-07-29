# zendots

Zen dotfiles

## Dotfile setup instructions

1. Copy over `chezmoi.toml` to `~/.config/chezmoi/chezmoi.toml`
2. Run `chezmoi init` and `chezmoi apply`
3. Install packages in `pkgs/`

### Package/Plugin installation instructions

1. `brew` install `brew bundle install` in the `pkgs/` directory
2. For `tmux` make sure to install plugins using `prefix + I`
3. For `yazi` run the `pkgs/download_yazi_plugins.sh`

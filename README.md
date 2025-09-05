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

### Misc instructions

1. Run `pkgs/misc_setup.sh` to run a set of commands manually to finish setup

### Font setup (manual)

1. Monaspace
2. Dank Mono (patched fonts collection)
3. Monalisa (patched fonts collection)
4. Cartograph (patched fonts collection)
5. Nerd fonts - Fira Code, Victor Mono, Cascadia Code
6. Recursive
7. Maple Mono
8. SN-Pro
9. IA-writer-{quattro,duospace}
10. font-awesome

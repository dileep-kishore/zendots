#!/usr/bin/env bash
# Run on a new Mac after the first chezmoi apply: installs the Brewfile,
# applies macOS settings and login items, and sets up tool plugins.
# Safe to rerun. Steps that fail are listed at the end; later steps still run.

set -uo pipefail

repo="$HOME/zendots"
failed=()

step() {
    local name="$1"
    shift
    printf '\n== %s\n' "$name"
    "$@" || failed+=("$name")
}

[[ "$(uname -s)" == "Darwin" ]] || { echo "setup-mac.sh: macOS only" >&2; exit 1; }
command -v brew >/dev/null || { echo "setup-mac.sh: install Homebrew first" >&2; exit 1; }
[[ -f "$repo/pkgs/Brewfile" ]] || { echo "setup-mac.sh: $repo is not synced yet" >&2; exit 1; }

# Homebrew loads casks from third-party taps only after they are trusted.
trust_taps() {
    local tap rc=0
    for tap in $(sed -n 's/^tap "\(.*\)"$/\1/p' "$repo/pkgs/Brewfile"); do
        if brew tap "$tap" && brew trust --tap "$tap"; then
            echo "trusted $tap"
        else
            echo "failed to trust $tap"
            rc=1
        fi
    done
    return "$rc"
}

tpm() {
    [[ -d "$HOME/.tmux/plugins/tpm" ]] && { echo "tpm already installed"; return; }
    git clone https://github.com/tmux-plugins/tpm "$HOME/.tmux/plugins/tpm"
}

# Adds each plugin download_yazi_plugins.sh lists that package.toml lacks, so a
# rerun completes a partial install; `ya pkg add` fails for one already listed.
yazi_plugins() {
    local plugin rc=0 manifest="$HOME/.config/yazi/package.toml"
    for plugin in $(sed -n 's/^ya pkg add //p' "$repo/pkgs/download_yazi_plugins.sh"); do
        if [[ -f "$manifest" ]] && grep -qF "\"$plugin\"" "$manifest"; then
            echo "recorded $plugin"
        elif ya pkg add "$plugin"; then
            echo "added $plugin"
        else
            echo "failed to add $plugin"
            rc=1
        fi
    done
    ya pkg install || rc=1
    return "$rc"
}

step "Trust Brewfile taps" trust_taps
# mas installs need an App Store sign-in; rerun this script after signing in.
step "Brewfile" brew bundle install --file="$repo/pkgs/Brewfile"
step "macOS settings" bash "$repo/pkgs/macos/defaults.sh"
step "Login items" bash "$repo/pkgs/macos/login-items.sh"
step "tmux plugin manager" tpm
step "Yazi plugins" yazi_plugins
step "bat cache" bat cache --build
step "pipx packages" bash "$repo/pkgs/pipx_packages.sh"

if ((${#failed[@]})); then
    printf '\nFailed steps: %s\n' "${failed[*]}"
    echo "Fix the cause and rerun; finished steps skip or repeat harmlessly."
    exit 1
fi
printf '\nAll steps finished. Start tmux and press prefix + I for its plugins.\n'
echo "Then follow sitting 2 in docs/new-mac.md."

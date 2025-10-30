#!/usr/bin/env bash

# Rebuild bat cache
if [ -f /opt/homebrew/bin/bat ]; then
    BAT_PATH="/opt/homebrew/bin/bat"
else
    BAT_PATH="/usr/bin/bat"
fi
BAT_PATH cache --build

# Clone tpm
if [ ! -d ~/.tmux/plugins/tpm ]; then
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi

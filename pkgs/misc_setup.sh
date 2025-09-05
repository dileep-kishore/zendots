#!/usr/bin/env bash

# Rebuild bat cache
/opt/homebrew/bin/bat cache --build

# Clone tpm
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

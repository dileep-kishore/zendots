#!/usr/bin/env bash

# Rebuild bat cache
/usr/bin/bat cache --build

# Clone tpm
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

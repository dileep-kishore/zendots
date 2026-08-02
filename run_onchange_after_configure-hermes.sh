#!/usr/bin/env bash
set -euo pipefail

if ! command -v hermes >/dev/null 2>&1; then
  printf 'Hermes Agent is not installed; skipping skin activation.\n'
  exit 0
fi

hermes skin use catppuccin-mocha

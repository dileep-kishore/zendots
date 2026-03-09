#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/opencode"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
TARGET_VERSION="${1:-latest}"
PACKAGE_SPEC="oh-my-opencode@${TARGET_VERSION}"

echo "Updating ${PACKAGE_SPEC} in ${CACHE_DIR}"
mkdir -p "${CACHE_DIR}"
bun add "${PACKAGE_SPEC}" --cwd "${CACHE_DIR}"

echo "Refreshing install state"
bunx --bun "${PACKAGE_SPEC}" install \
  --no-tui \
  --claude=no \
  --openai=yes \
  --gemini=no \
  --copilot=no \
  --opencode-zen=no \
  --skip-auth

echo "Syncing managed config into ${CONFIG_DIR}"
mkdir -p "${CONFIG_DIR}" "${CONFIG_DIR}/agent"
install -m 644 "${SCRIPT_DIR}/AGENTS.md" "${CONFIG_DIR}/AGENTS.md"
install -m 644 "${SCRIPT_DIR}/tui.json" "${CONFIG_DIR}/tui.json"
install -m 644 "${SCRIPT_DIR}/opencode.json" "${CONFIG_DIR}/opencode.json"
install -m 644 "${SCRIPT_DIR}/oh-my-opencode.json" "${CONFIG_DIR}/oh-my-opencode.json"
install -m 644 "${SCRIPT_DIR}/agent/docs-writer.md" "${CONFIG_DIR}/agent/docs-writer.md"

echo "Running health check"
bunx --bun "${PACKAGE_SPEC}" doctor || true

echo "Update complete"

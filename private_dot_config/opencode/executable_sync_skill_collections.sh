#!/usr/bin/env bash

set -euo pipefail

CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/opencode/skill-collections"
OPENCODE_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
OPENCODE_SKILLS_DIR="${OPENCODE_CONFIG_DIR}/skills"
OPENCODE_PLUGINS_DIR="${OPENCODE_CONFIG_DIR}/plugins"
SUPERPOWERS_DIR="${OPENCODE_CONFIG_DIR}/superpowers"

echo "Syncing OpenCode skill collections into ${OPENCODE_CONFIG_DIR}"
mkdir -p "${CACHE_ROOT}" "${OPENCODE_SKILLS_DIR}" "${OPENCODE_PLUGINS_DIR}"

if [[ ! -d "${SUPERPOWERS_DIR}/.git" ]]; then
  git clone --depth 1 https://github.com/obra/superpowers.git "${SUPERPOWERS_DIR}"
else
  git -C "${SUPERPOWERS_DIR}" fetch --depth 1 origin main
  git -C "${SUPERPOWERS_DIR}" checkout --force FETCH_HEAD
fi

rm -f "${OPENCODE_PLUGINS_DIR}/superpowers.js"
ln -s "${SUPERPOWERS_DIR}/.opencode/plugins/superpowers.js" "${OPENCODE_PLUGINS_DIR}/superpowers.js"

rm -rf "${OPENCODE_SKILLS_DIR}/superpowers"
ln -s "${SUPERPOWERS_DIR}/skills" "${OPENCODE_SKILLS_DIR}/superpowers"

echo "Skill collection sync complete"

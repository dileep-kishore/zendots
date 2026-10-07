#!/usr/bin/env bash

set -euo pipefail

OPENCODE_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
SUPERPOWERS_DIR="${OPENCODE_CONFIG_DIR}/superpowers"
PLUGIN_LINK="${OPENCODE_CONFIG_DIR}/plugins/superpowers.js"
SKILLS_LINK="${OPENCODE_CONFIG_DIR}/skills/superpowers"

# Superpowers is now loaded once from the pinned package in opencode.json.
# Retire only links created by the old helper, never their targets or real files.
for link in "${PLUGIN_LINK}" "${SKILLS_LINK}"; do
  if [[ ! -e "${link}" && ! -L "${link}" ]]; then
    continue
  fi
  if [[ ! -L "${link}" ]]; then
    echo "Refusing to remove non-symlink: ${link}" >&2
    exit 1
  fi

  target="$(readlink "${link}")"
  if [[ "${link}" == "${PLUGIN_LINK}" ]]; then
    expected="${SUPERPOWERS_DIR}/.opencode/plugins/superpowers.js"
    relative="../superpowers/.opencode/plugins/superpowers.js"
  else
    expected="${SUPERPOWERS_DIR}/skills"
    relative="../superpowers/skills"
  fi
  if [[ "${target}" != "${expected}" && "${target}" != "${relative}" ]]; then
    echo "Refusing to remove unfamiliar symlink: ${link} -> ${target}" >&2
    exit 1
  fi
done

for link in "${PLUGIN_LINK}" "${SKILLS_LINK}"; do
  if [[ -L "${link}" ]]; then
    rm -- "${link}"
    echo "Removed legacy link: ${link}"
  fi
done

echo "Superpowers is managed by the pinned V2 package; the local checkout is untouched."

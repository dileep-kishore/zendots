#!/usr/bin/env bash
# Run `npx skills` against the global skill store and record the result in
# chezmoi, so an install on one machine survives a `chezmoi update` on another.
#
#   agent-skills.sh add mattpocock/skills
#   agent-skills.sh update
#   agent-skills.sh remove wayfinder
set -euo pipefail

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'missing required command: %s\n' "$1" >&2
    exit 1
  }
}

require_cmd npx
require_cmd chezmoi

# `skills` installs project-locally when the cwd is a git repo; run from $HOME so
# it always resolves to the global store, whether or not -g was passed.
(cd "$HOME" && npx -y skills@latest "$@")

# Snapshot the whole store rather than just the new skill: it is the record of
# what is installed, and picking up sibling updates is the point of syncing.
chezmoi add "$HOME/.agents/skills" "$HOME/.agents/.skill-lock.json"

"$HOME/.local/bin/link-agent-skills.sh"

printf '\nrecorded in chezmoi -- commit and push to sync:\n  cd %s && git add -A && git commit && git push\n' \
  "$(chezmoi source-path)"

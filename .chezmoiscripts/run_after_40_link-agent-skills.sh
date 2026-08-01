#!/usr/bin/env bash
# Relink agent skills after every apply, so a fresh machine wires itself up.
# The implementation lives in ~/.local/bin so it can also be run by hand and by
# agent-skills.sh; chezmoi has already written it by the time run_after fires.
set -euo pipefail
exec "$HOME/.local/bin/link-agent-skills.sh"

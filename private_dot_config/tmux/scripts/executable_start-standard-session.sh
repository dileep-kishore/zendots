#!/usr/bin/env bash

set -euo pipefail

short_name() {
    local value="$1"

    value=$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')
    value=$(printf '%s' "$value" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')

    if [[ -z "$value" ]]; then
        value="session"
    fi

    printf '%s\n' "$value"
}

resolve_dir() {
    local input="${1:-$PWD}"

    if [[ "$input" == "~"* ]]; then
        input="${input/#\~/$HOME}"
    fi

    if [[ ! -d "$input" ]]; then
        printf 'Directory not found: %s\n' "$1" >&2
        exit 1
    fi

    (
        cd "$input"
        pwd -P
    )
}

existing_session_path() {
    local session_name="$1"

    tmux display-message -p -t "$session_name" '#{session_path}' 2>/dev/null || true
}

ROOT_DIR=$(resolve_dir "${1:-$PWD}")
EXPLICIT_NAME="${2:-}"
WORKSPACE="$HOME/.config/tmuxp/standard.yaml"

if [[ ! -f "$WORKSPACE" ]]; then
    printf 'Workspace file not found: %s\n' "$WORKSPACE" >&2
    exit 1
fi

if [[ -n "$EXPLICIT_NAME" ]]; then
    SESSION_NAME="$EXPLICIT_NAME"
else
    SESSION_NAME=$(short_name "$(basename "$ROOT_DIR")")

    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        CURRENT_PATH=$(existing_session_path "$SESSION_NAME")
        if [[ "$CURRENT_PATH" != "$ROOT_DIR" ]]; then
            HASH_SUFFIX=$(printf '%s' "$ROOT_DIR" | md5sum | cut -c1-6)
            SESSION_NAME="${SESSION_NAME}-${HASH_SUFFIX}"
        fi
    fi
fi

if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    if command -v tmuxp >/dev/null 2>&1; then
        TMUXP_CMD=(tmuxp)
    elif command -v uv >/dev/null 2>&1; then
        TMUXP_CMD=(uvx --from tmuxp tmuxp)
    else
        printf 'tmuxp is not installed and uv is unavailable.\n' >&2
        exit 1
    fi

    PROJECT_ROOT="$ROOT_DIR" "${TMUXP_CMD[@]}" load -d -y -s "$SESSION_NAME" "$WORKSPACE"
fi

if [[ -n "${TMUX:-}" ]]; then
    exec tmux switch-client -t "$SESSION_NAME"
fi

exec tmux attach-session -t "$SESSION_NAME"

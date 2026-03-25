#!/usr/bin/env bash

set -euo pipefail

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

escape_toml() {
    local value="$1"

    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    printf '%s\n' "$value"
}

expand_home_path() {
    local value="$1"

    if [[ "$value" == "~"* ]]; then
        printf '%s\n' "${value/#\~/$HOME}"
        return
    fi

    printf '%s\n' "$value"
}

ensure_config_file() {
    mkdir -p "$(dirname "$CONFIG_FILE")"

    if [[ -f "$CONFIG_FILE" ]]; then
        return
    fi

    cat >"$CONFIG_FILE" <<'EOF'
sort_order = ["tmux", "config", "zoxide"]

[default_session]
preview_command = "eza --all --git --icons --color=always {}"
EOF
}

find_session_path() {
    awk -v target="$SESSION_NAME" '
    function trim_quotes(value) {
        gsub(/^[[:space:]]*"/, "", value)
        gsub(/"[[:space:]]*$/, "", value)
        return value
    }

    function flush() {
        if (in_session && name == target) {
            print path
            found = 1
            exit
        }
    }

    /^\[\[session\]\][[:space:]]*$/ {
        flush()
        in_session = 1
        name = ""
        path = ""
        next
    }

    in_session && /^[[:space:]]*name[[:space:]]*=/ {
        line = $0
        sub(/^[^=]*=[[:space:]]*/, "", line)
        name = trim_quotes(line)
        next
    }

    in_session && /^[[:space:]]*path[[:space:]]*=/ {
        line = $0
        sub(/^[^=]*=[[:space:]]*/, "", line)
        path = trim_quotes(line)
        next
    }

    END {
        if (!found && in_session && name == target) {
            print path
        }
    }
    ' "$CONFIG_FILE"
}

SESSION_NAME="${1:-}"
ROOT_DIR=$(resolve_dir "${2:-$PWD}")
CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/sesh/sesh.toml"

if [[ -z "$SESSION_NAME" ]]; then
    printf 'Usage: %s <session-name> [directory]\n' "${0##*/}" >&2
    exit 1
fi

ensure_config_file

EXISTING_PATH=$(find_session_path || true)

if [[ -n "$EXISTING_PATH" ]]; then
    NORMALIZED_EXISTING=$(expand_home_path "$EXISTING_PATH")

    if [[ "$NORMALIZED_EXISTING" != "$ROOT_DIR" ]]; then
        printf "Session '%s' already points to %s\n" "$SESSION_NAME" "$NORMALIZED_EXISTING" >&2
        exit 1
    fi

    exit 0
fi

printf '\n[[session]]\nname = "%s"\npath = "%s"\n' \
    "$(escape_toml "$SESSION_NAME")" \
    "$(escape_toml "$ROOT_DIR")" >>"$CONFIG_FILE"

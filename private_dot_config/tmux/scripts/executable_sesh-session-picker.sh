#!/usr/bin/env bash

set -euo pipefail

SELF="$HOME/.config/tmux/scripts/sesh-session-picker.sh"
STARTER="$HOME/.config/tmux/scripts/start-standard-session.sh"
BLUE=$'\033[34m'
YELLOW=$'\033[33m'
CYAN=$'\033[36m'
MAGENTA=$'\033[35m'
RESET=$'\033[39m'

shorten_home() {
    local value="$1"

    if [[ -n "$value" ]]; then
        printf '%s\n' "${value/#$HOME/\~}"
        return
    fi

    printf '\n'
}

print_list() {
    local mode="${1:-all}"
    local filter

    case "$mode" in
    all)
        filter='select(.Src == "tmux")'
        ;;
    tmux)
        filter='select(.Src == "tmux")'
        ;;
    config)
        filter='select(.Src == "config")'
        ;;
    zoxide)
        filter='select(.Src == "zoxide")'
        ;;
    find)
        fd -H -d 2 -t d -E .Trash . ~ | while IFS= read -r path; do
            pretty=$(shorten_home "$path")
            printf '%s%s\t%s\t%s\tfind\t%s\t%s\n' "$MAGENTA" "$RESET" "$pretty" "$pretty" "$pretty" "$path"
        done
        return
        ;;
    *)
        printf 'Unknown mode: %s\n' "$mode" >&2
        exit 1
        ;;
    esac

    sesh list --json 2>/dev/null | jq -r ".[] | $filter | [.Src, .Name, (.Path // \"\")] | @tsv" | while IFS=$'\t' read -r src name path; do
        case "$src" in
        tmux)
            icon="${BLUE}${RESET}"
            label="$name"
            ;;
        config)
            icon="${YELLOW}${RESET}"
            label="$name"
            ;;
        zoxide)
            icon="${CYAN}${RESET}"
            label="$name"
            ;;
        *)
            continue
            ;;
        esac

        printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
            "$icon" \
            "$label" \
            "$(shorten_home "$path")" \
            "$src" \
            "$name" \
            "$path"
    done
}

preview_entry() {
    local src="$1"
    local name="$2"
    local path="${3:-}"

    case "$src" in
    tmux)
        tmux capture-pane -e -p -t "$name" 2>/dev/null | tail -n 200
        ;;
    config | zoxide | find)
        if [[ -d "$path" ]]; then
            printf '%s\n\n' "$(shorten_home "$path")"
            eza --icons auto --git -la "$path" 2>/dev/null | head -n 200
            return
        fi

        printf '%s\n' "$path"
        ;;
    *)
        printf '%s\n' "$name"
        ;;
    esac
}

connect_entry() {
    local src="${1:-}"
    local name="${2:-}"
    local path="${3:-}"

    if [[ $# -eq 1 ]]; then
        local target="$src"

        if [[ "$target" == "~"* ]]; then
            target="${target/#\~/$HOME}"
        fi

        if [[ -d "$target" ]]; then
            exec "$STARTER" "$target"
        fi

        if tmux has-session -t "$target" 2>/dev/null; then
            if [[ -n "${TMUX:-}" ]]; then
                exec tmux switch-client -t "$target"
            fi

            exec tmux attach-session -t "$target"
        fi

        if mapfile -t config_match < <(sesh list --json 2>/dev/null | jq -r --arg target "$target" '.[] | select(.Src == "config" and .Name == $target) | [.Name, .Path] | @tsv'); then
            if [[ "${#config_match[@]}" -gt 0 ]]; then
                IFS=$'\t' read -r name path <<< "${config_match[0]}"
                exec "$STARTER" "$path" "$name"
            fi
        fi

        if command -v zoxide >/dev/null 2>&1; then
            if path=$(zoxide query "$target" 2>/dev/null); then
                exec "$STARTER" "$path"
            fi
        fi

        printf 'Unable to resolve session or path: %s\n' "$target" >&2
        exit 1
    fi

    case "$src" in
    tmux)
        if [[ -n "${TMUX:-}" ]]; then
            exec tmux switch-client -t "$name"
        fi

        exec tmux attach-session -t "$name"
        ;;
    config)
        exec "$STARTER" "$path" "$name"
        ;;
    zoxide | find)
        exec "$STARTER" "$path"
        ;;
    *)
        printf 'Unable to connect to source: %s\n' "$src" >&2
        exit 1
        ;;
    esac
}

pick_entry() {
    local selected

    selected="$(
        print_list all | fzf-tmux -p 50%,70% --layout=reverse \
            --delimiter=$'\t' \
            --with-nth=1,2,3 \
            --no-sort \
            --ansi \
            --border-label '  TMUX Session Manager (sesh) ' \
            --prompt '  ' \
            --header '  ^a tmux ^s tmux ^g config ^x zoxide ^f find ^d tmux kill' \
            --bind "tab:down,btab:up" \
            --bind "ctrl-a:change-prompt(  )+reload($SELF list all)" \
            --bind "ctrl-s:change-prompt(  )+reload($SELF list tmux)" \
            --bind "ctrl-g:change-prompt(  )+reload($SELF list config)" \
            --bind "ctrl-x:change-prompt(  )+reload($SELF list zoxide)" \
            --bind "ctrl-f:change-prompt(  )+reload($SELF list find)" \
            --bind "ctrl-d:execute(if [ {4} = tmux ]; then tmux kill-session -t {5}; fi)+reload($SELF list all)" \
            --preview-window 'up:70%' \
            --preview "$SELF preview {4} {5} {6}"
    )" || exit 0

    IFS=$'\t' read -r _ _ _ src name path <<< "$selected"
    connect_entry "$src" "$name" "$path"
}

case "${1:-pick}" in
list)
    print_list "${2:-all}"
    ;;
preview)
    preview_entry "${2:-}" "${3:-}" "${4:-}"
    ;;
connect)
    shift
    connect_entry "$@"
    ;;
pick)
    pick_entry
    ;;
*)
    printf 'Unknown command: %s\n' "${1:-}" >&2
    exit 1
    ;;
esac

#!/usr/bin/env bash
# Register the Mac Mini's login items on this Mac.
# The list was read from macmini's System Events login items on 2026-10-22.
# The first run asks to let the terminal control System Events.

set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "login-items.sh: macOS only" >&2
    exit 1
fi

apps=(
    "Syncthing"
    "Notion"
    "Morgen"
    "Caffeinated"
    "OmniWM"
    "CodexBar"
    "Wispr Flow"
    "Raycast"
    "BetterDisplay"
    "Granola"
    "Vorssaint"
    "Superlist"
    "Grok Bot"
    "ProtonVPN"
)

existing=$(osascript -e 'tell application "System Events" to get the name of every login item')

for app in "${apps[@]}"; do
    path=""
    for dir in /Applications "$HOME/Applications"; do
        if [[ -d "$dir/$app.app" ]]; then
            path="$dir/$app.app"
            break
        fi
    done
    if [[ -z "$path" ]]; then
        echo "skip $app: not installed"
    elif [[ ", $existing, " == *", $app, "* ]]; then
        echo "keep $app: already a login item"
    else
        osascript - "$path" <<'APPLESCRIPT' >/dev/null
on run argv
    tell application "System Events" to make login item at end with properties {path:item 1 of argv, hidden:false}
end run
APPLESCRIPT
        echo "add  $app: $path"
    fi
done

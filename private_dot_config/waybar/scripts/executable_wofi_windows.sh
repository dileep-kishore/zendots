#!/usr/bin/env bash
state="$(hyprctl -j clients)"
active_window="$(hyprctl -j activewindow)"
current_addr="$(echo "$active_window" | jq -r '.address')"

# Create display text and store with address
selection="$(echo "$state" |
    jq -r '.[] | select(.monitor != -1 ) | "\(.workspace.name) \(.title)\t\(.address)"' |
    sed "s|\t$current_addr|\t[FOCUSED]|" |
    sort -r |
    column -t -s $'\t' |
    wofi --dmenu)"

if [[ "$selection" =~ \[FOCUSED\] ]]; then
    echo 'already focused, exiting'
    exit 0
fi

if [[ "$selection" != "" ]]; then
    # Extract address from the selection (it's the last field)
    addr="$(echo "$selection" | awk '{print $NF}')"
    hyprctl dispatch focuswindow address:${addr}
fi

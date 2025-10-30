#!/usr/bin/env bash

# Get all windows and focused window info
windows="$(niri msg -j windows)"
focused_output="$(niri msg -j focused-window)"
focused_id="$(echo "$focused_output" | jq -r '.id // empty')"

# Create display text and store with window ID
selection="$(echo "$windows" |
    jq -r '.[] | "\(.workspace_id // "N/A") \(.title // .app_id)\t\(.id)"' |
    sed "s|\t$focused_id|\\t[FOCUSED]|" |
    sort -n |
    column -t -s $'\t' |
    wofi --dmenu --prompt "Switch Window")"

# Exit if already focused
if [[ "$selection" =~ \[FOCUSED\] ]]; then
    echo 'already focused, exiting'
    exit 0
fi

# Exit if no selection
if [[ -z "$selection" ]]; then
    exit 0
fi

# Extract window ID from the selection (it's the last field)
window_id="$(echo "$selection" | awk '{print $NF}')"

# Focus the selected window
niri msg action focus-window --id "$window_id"

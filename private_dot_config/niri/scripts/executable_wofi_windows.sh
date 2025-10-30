#!/usr/bin/env bash

# Get all windows and focused window info
windows="$(niri msg -j windows)"
focused_output="$(niri msg -j focused-window)"
focused_id="$(echo "$focused_output" | jq -r '.id // empty')"

# Create mapping of title to window ID (stored for lookup)
mapping="$(echo "$windows" | jq -r '.[] | "\(.title // .app_id)\t\(.id)"')"

# Create display text (only titles with FOCUSED marker, no IDs shown)
display="$(echo "$mapping" |
    awk -F'\t' -v focused="$focused_id" '{
        if ($2 == focused)
            print $1 "[FOCUSED]"
        else
            print $1
    }' | sort)"

# Show in wofi
selection="$(echo "$display" | wofi --dmenu --prompt "Switch Window")"

# Exit if already focused
if [[ "$selection" =~ \[FOCUSED\] ]]; then
    echo 'already focused, exiting'
    exit 0
fi

# Exit if no selection
if [[ -z "$selection" ]]; then
    exit 0
fi

# Look up window ID from mapping based on selected title
window_id="$(echo "$mapping" | grep -F "$selection" | head -1 | cut -f2)"

# Focus the selected window
if [[ -n "$window_id" ]]; then
    niri msg action focus-window --id "$window_id"
fi

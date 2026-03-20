#!/usr/bin/env bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
FIVE_HR=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty' | cut -d. -f1)
SEVEN_DAY=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty' | cut -d. -f1)

CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
DIM='\033[2m'
RESET='\033[0m'

usage_color() {
    local val=$1
    if [ -z "$val" ]; then echo "$DIM"; return; fi
    if [ "$val" -ge 90 ]; then echo "$RED"
    elif [ "$val" -ge 70 ]; then echo "$YELLOW"
    else echo "$GREEN"; fi
}

# --- Context bar ---
if [ "$PCT" -ge 90 ]; then BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10))
EMPTY=$((10 - FILLED))
BAR=$(printf "%${FILLED}s" '' | sed 's/ /▓/g')$(printf "%${EMPTY}s" '' | sed 's/ /░/g')

MINS=$((DURATION_MS / 60000))
SECS=$(((DURATION_MS % 60000) / 1000))

BRANCH=""
git rev-parse --git-dir >/dev/null 2>&1 && BRANCH=" | 🌿 $(git branch --show-current 2>/dev/null)"

# --- Output ---
echo -e "${CYAN}[$MODEL]${RESET} 📁 ${DIR##*/}$BRANCH"
COST_FMT=$(printf '$%.2f' "$COST")

USAGE_SEG=""
if [ -n "$FIVE_HR" ]; then
    USAGE_SEG=" | $(usage_color "$FIVE_HR")5h:${FIVE_HR}%${RESET}"
fi
if [ -n "$SEVEN_DAY" ]; then
    USAGE_SEG="${USAGE_SEG} $(usage_color "$SEVEN_DAY")7d:${SEVEN_DAY}%${RESET}"
fi

echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% | ${YELLOW}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s${USAGE_SEG}"

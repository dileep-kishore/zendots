#!/usr/bin/env bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')

CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
DIM='\033[2m'
RESET='\033[0m'

# --- Usage API (5-hour & weekly) with file-based cache ---
USAGE_CACHE="$HOME/.claude/.usage-cache.json"
CACHE_TTL=300 # 5 minutes

get_usage() {
    local now
    now=$(date +%s)

    # Check cache freshness
    if [ -f "$USAGE_CACHE" ]; then
        local cached_at
        cached_at=$(jq -r '.timestamp // 0' "$USAGE_CACHE" 2>/dev/null)
        if [ $((now - cached_at)) -lt $CACHE_TTL ]; then
            jq -r '.data' "$USAGE_CACHE" 2>/dev/null
            return
        fi
    fi

    # Read OAuth token from macOS Keychain
    local creds
    creds=$(/usr/bin/security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null) || return
    local token
    token=$(echo "$creds" | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null)
    [ -z "$token" ] && return

    # Fetch usage API
    local response
    response=$(curl -s --max-time 5 \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" \
        "https://api.anthropic.com/api/oauth/usage" 2>/dev/null)

    # Validate response has expected fields
    if echo "$response" | jq -e '.five_hour' >/dev/null 2>&1; then
        # Write cache
        jq -n --argjson data "$response" --arg ts "$now" \
            '{data: $data, timestamp: ($ts | tonumber)}' > "$USAGE_CACHE" 2>/dev/null
        echo "$response"
    elif [ -f "$USAGE_CACHE" ]; then
        # Fall back to stale cache on API failure
        jq -r '.data' "$USAGE_CACHE" 2>/dev/null
    fi
}

FIVE_HR=""
SEVEN_DAY=""
USAGE_JSON=$(get_usage 2>/dev/null)
if [ -n "$USAGE_JSON" ]; then
    FIVE_HR=$(echo "$USAGE_JSON" | jq -r '.five_hour.utilization // empty' 2>/dev/null)
    SEVEN_DAY=$(echo "$USAGE_JSON" | jq -r '.seven_day.utilization // empty' 2>/dev/null)
fi

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

# Build usage segment
USAGE_SEG=""
if [ -n "$FIVE_HR" ]; then
    USAGE_SEG=" | $(usage_color "$FIVE_HR")5h:${FIVE_HR}%${RESET}"
fi
if [ -n "$SEVEN_DAY" ]; then
    USAGE_SEG="${USAGE_SEG} $(usage_color "$SEVEN_DAY")7d:${SEVEN_DAY}%${RESET}"
fi

echo -e "${BAR_COLOR}${BAR}${RESET} ${PCT}% | ${YELLOW}${COST_FMT}${RESET} | ⏱️ ${MINS}m ${SECS}s${USAGE_SEG}"

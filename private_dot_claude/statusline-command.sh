#!/usr/bin/env bash
input=$(cat)

# "Opus 5 (1M context)" -> "Opus 5 (1M)"; the window size is what the context bar is a percentage of.
MODEL=$(echo "$input" | jq -r '.model.display_name' | sed 's/ context)/)/')
DIR=$(echo "$input" | jq -r '.workspace.current_dir')
COST=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
DURATION_MS=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
ADDED=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
REMOVED=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
WORKTREE=$(echo "$input" | jq -r '.worktree.name // empty')
EFFORT=$(echo "$input" | jq -r '.effort.level // empty')
# Only present when editorMode is vim.
VIM=$(echo "$input" | jq -r '.vim.mode // empty')
# Not every Claude Code build reports effort in the status payload; settings is authoritative.
[ -z "$EFFORT" ] && EFFORT=$(jq -r '.effortLevel // empty' ~/.claude/settings.json 2>/dev/null)

# --- Catppuccin Mocha ---
MAUVE='\033[38;2;203;166;247m'
BLUE='\033[38;2;137;180;250m'
PEACH='\033[38;2;250;179;135m'
LAVENDER='\033[38;2;180;190;254m'
TEAL='\033[38;2;148;226;213m'
SUBTEXT1='\033[38;2;186;194;222m'
GREEN='\033[38;2;166;227;161m'
YELLOW='\033[38;2;249;226;175m'
RED='\033[38;2;243;139;168m'
OVERLAY='\033[38;2;127;132;156m'
SURFACE='\033[38;2;88;91;112m'
RESET='\033[0m'

SEP="${SURFACE}|${RESET}"

# --- Context bar ---
if [ "$PCT" -ge 90 ]; then
    BAR_COLOR="$RED"
elif [ "$PCT" -ge 70 ]; then
    BAR_COLOR="$YELLOW"
else BAR_COLOR="$GREEN"; fi

FILLED=$((PCT / 10))
EMPTY=$((10 - FILLED))
BAR=$(printf "%${FILLED}s" '' | sed 's/ /▓/g')$(printf "%${EMPTY}s" '' | sed 's/ /░/g')

MINS=$((DURATION_MS / 60000))
SECS=$(((DURATION_MS % 60000) / 1000))

BRANCH=""
GIT_SEG=""
if git rev-parse --git-dir >/dev/null 2>&1; then
    BRANCH=" $SEP ${PEACH} $(git branch --show-current 2>/dev/null)${RESET}"
    # Uncommitted work vs HEAD: one call covers both staged and unstaged.
    read -r GIT_ADD GIT_DEL < <(git diff --numstat HEAD 2>/dev/null |
        awk '{a+=$1; d+=$2} END {print a+0, d+0}')
    if [ "${GIT_ADD:-0}" -gt 0 ] || [ "${GIT_DEL:-0}" -gt 0 ]; then
        GIT_SEG=" ${GREEN}+${GIT_ADD}${RESET} ${RED}-${GIT_DEL}${RESET}"
    fi
fi

# Worktree name is only worth a segment when it isn't already the branch or the dir.
WT_SEG=""
if [ -n "$WORKTREE" ]; then
    if [ "$WORKTREE" = "$(git branch --show-current 2>/dev/null)" ] || [ "$WORKTREE" = "${DIR##*/}" ]; then
        WT_SEG=" ${LAVENDER}󰙅${RESET}"
    else
        WT_SEG=" ${LAVENDER}󰙅 ${WORKTREE}${RESET}"
    fi
fi

EFFORT_SEG=""
[ -n "$EFFORT" ] && EFFORT_SEG=" ${SURFACE}·${RESET} ${TEAL}${EFFORT}${RESET}"

VIM_SEG=""
case "$VIM" in
    NORMAL) VIM_SEG="${BLUE}NOR${RESET} $SEP " ;;
    INSERT) VIM_SEG="${GREEN}INS${RESET} $SEP " ;;
    VISUAL) VIM_SEG="${MAUVE}VIS${RESET} $SEP " ;;
esac

DIFF_SEG=""
if [ "$ADDED" -gt 0 ] || [ "$REMOVED" -gt 0 ]; then
    DIFF_SEG=" ${SURFACE}·${RESET} ${GREEN}+${ADDED}${RESET} ${RED}-${REMOVED}${RESET}"
fi

# --- Output ---
COST_FMT=$(printf '$%.2f' "$COST")

echo -e "${VIM_SEG}${MAUVE}󰧑 $MODEL${RESET}$EFFORT_SEG $SEP ${BLUE} ${DIR##*/}${RESET}$BRANCH$GIT_SEG$WT_SEG"
echo -e "${BAR_COLOR}${BAR}${RESET} ${OVERLAY}${PCT}%${RESET} $SEP ${YELLOW}${COST_FMT}${RESET} $SEP ${SUBTEXT1}󱎫 ${MINS}m ${SECS}s${RESET}$DIFF_SEG"

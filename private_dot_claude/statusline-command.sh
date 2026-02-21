#!/usr/bin/env bash
# Claude Code status line script

input=$(cat)

project_dir=$(echo "$input" | jq -r '.workspace.project_dir // .cwd // ""')
project_name=$(basename "$project_dir")

model=$(echo "$input" | jq -r '.model.display_name // .model.id // "unknown"')

used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

# Get git branch from project_dir
git_branch=""
if [ -n "$project_dir" ] && [ -d "$project_dir/.git" ]; then
    git_branch=$(git -C "$project_dir" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null || git -C "$project_dir" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
fi

# Build status line segments
# Segment 1: project dir + git branch
if [ -n "$git_branch" ]; then
    printf '\033[34m%s\033[0m \033[90mgit:\033[36m%s\033[0m' "$project_name" "$git_branch"
else
    printf '\033[34m%s\033[0m' "$project_name"
fi

# Segment 2: model
printf ' \033[90m|\033[0m \033[35m%s\033[0m' "$model"

# Segment 3: token usage
if [ -n "$used_pct" ] && [ -n "$remaining_pct" ]; then
    # Color-code based on usage
    used_int=${used_pct%.*}
    if [ "$used_int" -ge 80 ] 2>/dev/null; then
        token_color='\033[31m'  # red
    elif [ "$used_int" -ge 50 ] 2>/dev/null; then
        token_color='\033[33m'  # yellow
    else
        token_color='\033[32m'  # green
    fi
    printf " \033[90m|\033[0m ${token_color}%.0f%%\033[0m \033[90mused\033[0m" "$used_pct"
fi

printf '\n'

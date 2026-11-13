#!/bin/bash
# SessionStart(compact) hook: stdout is added to the context after compaction.
# Prints pointers read from disk now, never claims carried over from the chat.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH-}"

cwd=$(head -c 65536 | jq -r '.cwd // empty' 2>/dev/null)
[ -d "$cwd" ] || cwd=$PWD

echo "Context was compacted. These pointers were read from disk just now;"
echo "anything else remembered from before compaction is unverified until rechecked."
echo "- cwd: $cwd"

top=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || exit 0
branch=$(git -C "$top" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "detached")
echo "- repo: $top"
echo "- branch: $branch"
echo "- HEAD: $(git -C "$top" log -1 --format='%h %s' 2>/dev/null)"
counts=$(git -C "$top" rev-list --left-right --count '@{upstream}...HEAD' 2>/dev/null) &&
  echo "- vs upstream: ${counts##*[[:space:]]} ahead, ${counts%%[[:space:]]*} behind"
echo "- uncommitted paths: $(git -C "$top" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"

# Decision logs and task files touched in the last two days, newest first.
logs=$(find "$top" -maxdepth 4 \( -name .git -o -name node_modules \) -prune -o \
  -type f \( -name decisions.tsv -o -path '*/.audit/*.tsv' -o -name tasks.md \) \
  -mtime -2 -exec ls -t {} + 2>/dev/null | head -5)
[ -n "$logs" ] && printf '%s\n' "$logs" | sed 's/^/- log: /'
exit 0

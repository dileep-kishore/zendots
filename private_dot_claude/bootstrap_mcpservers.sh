#!/usr/bin/env bash

# NOTE: You can manually run

# claude mcp add sequential-thinking \
#   --scope user \
#   -e DISABLE_THOUGHT_LOGGING=true \
#   -- npx -y @modelcontextprotocol/server-sequential-thinking

tmp="$(mktemp)"
jq -s '
  (.[0] // {}) as $current |
  (.[1].mcpServers // {}) as $newServers |
  $current + {mcpServers: (($current.mcpServers // {}) + $newServers)}
' ~/.claude.json ~/dotfiles/claude/mcpServers.json >"$tmp" &&
  mv "$tmp" ~/.claude.json

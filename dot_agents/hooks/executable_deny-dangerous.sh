#!/bin/bash
# Accident filter only: shell indirection, file tools, MCP, and interactive stdin
# are not contained. Never execute or evaluate the command received on stdin.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH-}"
export LC_ALL=C
set -o pipefail

block() {
  printf 'Agent command guard: %s. Stop and report this to the user.\n' "$1" >&2
  exit 2
}

for dependency in jq grep sed head; do
  command -v "$dependency" >/dev/null 2>&1 || block "missing dependency: $dependency"
done
guard_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || block 'cannot locate policy'
policy="$guard_dir/dangerous-patterns.txt"
exec 3< "$policy" || block 'cannot read policy'

# Bound input without interpreting it. Oversized or malformed payloads fail closed.
candidate=$(head -c 1048577 | jq -erRs '
  if utf8bytelength > 1048576 or index("\u0000") != null
  then error("invalid payload") else fromjson end
  | .tool_input.command | select(type == "string" and length > 0)
  | select(index("\u0000") == null)
' 2>/dev/null) || block 'invalid hook command input'

case "${HOME-}" in /*) ;; *) block 'HOME must be an absolute path' ;; esac
[ "$HOME" != / ] || block 'HOME must not be root'
escaped_home=$(printf '%s' "${HOME%/}" | sed 's/[][\\.^$*+?(){}|]/\\&/g') || block 'cannot encode home path'

line_number=0
rule_count=0
matched_line=
while IFS= read -r pattern <&3 || [ -n "$pattern" ]; do
  line_number=$((line_number + 1))
  case "$pattern" in ''|\#*) continue ;; esac
  rule_count=$((rule_count + 1))
  # At most one literal home placeholder per rule; never shell-expand the input.
  case "$pattern" in
    *@HOME@*) pattern="${pattern%%@HOME@*}${escaped_home}${pattern#*@HOME@}" ;;
  esac
  printf '%s\n' "$candidate" | grep -E -- "$pattern" >/dev/null 2>&1
  result=$?
  case "$result" in
    0) matched_line=$line_number ;;
    1) ;;
    *) block "invalid or unreadable policy at line $line_number" ;;
  esac
done
[ "$rule_count" -gt 0 ] || block 'policy has no rules'
[ -z "$matched_line" ] || block "blocked by policy line $matched_line"
exit 0

#!/usr/bin/env bash
# Link ~/.agents/skills into Claude Code, the one harness that cannot read it.
#
# Codex, OpenCode and the rest resolve ~/.agents/skills themselves -- `npx
# skills` reports them as "universal", and both binaries carry the path -- so
# linking into ~/.codex/skills or ~/.config/opencode/skills would make them load
# every skill twice. Claude Code only reads ~/.claude/skills, so it gets links.
#
# `npx skills` already writes these on install; this script covers the other
# direction, where chezmoi restores the store on a new machine and no installer
# ever ran.
set -euo pipefail

src="$HOME/.agents/skills"
dest="$HOME/.claude/skills"
[ -d "$src" ] || exit 0
mkdir -p "$dest"

# Drop links into .agents that no longer resolve, so removing a skill on one
# machine removes it everywhere instead of leaving a dangling entry.
for link in "$dest"/*; do
    [ -L "$link" ] || continue
    case "$(readlink "$link")" in
    *.agents/skills/*) [ -e "$link" ] || rm -f "$link" ;;
    esac
done

for skill in "$src"/*/; do
    skill="${skill%/}"
    target="$dest/$(basename "$skill")"
    if [ -L "$target" ]; then
        # `npx skills` writes these relative and this script writes them
        # absolute; -ef resolves both, so neither rewrites the other's links.
        [ "$target" -ef "$skill" ] || ln -sfn "$skill" "$target"
    elif [ -e "$target" ]; then
        printf 'link-agent-skills: %s is not a symlink, leaving it alone\n' "$target" >&2
    else
        ln -s "$skill" "$target"
    fi
done

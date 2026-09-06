# Shared at template-render time; no extra runtime import or installed helper.
GUARD_COMMAND = (
    'task_guard="$HOME/.agents/hooks/deny-dangerous.sh"; '
    'if [ ! -r "$task_guard" ]; then '
    "echo 'agent command guard unavailable' >&2; exit 2; fi; "
    'exec /bin/bash "$task_guard"'
)


def merge_command_guard(doc):
    hooks = doc.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        die("hooks is not a mapping")
    entries = hooks.setdefault("PreToolUse", [])
    if not isinstance(entries, list):
        die("hooks.PreToolUse is not an array")
    owned = {"type": "command", "command": GUARD_COMMAND, "timeout": 5}
    desired = {"matcher": "^Bash$", "hooks": [owned]}
    # A canonical entry is already correct wherever it sits. Avoid shifting
    # other entries (Codex hook trust includes indexes) on a semantic no-op.
    matches = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
            die("invalid PreToolUse entry")
        for hook in entry["hooks"]:
            if not isinstance(hook, dict):
                die("invalid PreToolUse hook")
            if hook.get("command") == GUARD_COMMAND:
                matches.append(entry)
    if len(matches) == 1 and matches[0] == desired:
        return
    if len(matches) == 1 and len(matches[0]["hooks"]) == 1:
        # Repair an existing standalone entry without shifting later indexes.
        entry = matches[0]
        entries[entries.index(entry)] = {
            **entry, "matcher": "^Bash$", "hooks": [{**entry["hooks"][0], **owned}]
        }
        return
    remaining = []
    for entry in entries:
        kept = [hook for hook in entry["hooks"] if hook.get("command") != GUARD_COMMAND]
        if len(kept) == len(entry["hooks"]):
            remaining.append(entry)
        elif kept:
            remaining.append({**entry, "hooks": kept})
    hooks["PreToolUse"] = [*remaining, desired]

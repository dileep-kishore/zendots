HINDSIGHT_MARKERS = ("/.hindsight/coding-agents/dist/", "hindsight-failure-hook")


def _is_hindsight(hook):
    return isinstance(hook, dict) and any(m in str(hook.get("command", "")) for m in HINDSIGHT_MARKERS)


def merge_hindsight_hooks(doc, desired):
    """Keep exactly our Hindsight entries, leaving every other tool's hooks alone.

    `desired` maps an event to the list of entries we own there. Correct entries
    are left in place, so another tool appending after them causes no churn.
    """
    hooks = doc.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        die("hooks is not a mapping")
    for event in sorted(set(hooks) | set(desired)):
        entries = hooks.get(event, [])
        if not isinstance(entries, list):
            die("hooks." + event + " is not an array")
        want = desired.get(event, [])
        ours = [e for e in entries if isinstance(e, dict) and any(_is_hindsight(h) for h in e.get("hooks") or [])]
        if ours == want and all(len(e.get("hooks") or []) == 1 for e in ours):
            continue
        remaining = []
        for entry in entries:
            inner = entry.get("hooks") if isinstance(entry, dict) else None
            if not isinstance(inner, list):
                remaining.append(entry)
                continue
            kept = [h for h in inner if not _is_hindsight(h)]
            if len(kept) == len(inner):
                remaining.append(entry)
            elif kept:
                remaining.append({**entry, "hooks": kept})
        merged = [*remaining, *want]
        if merged:
            hooks[event] = merged
        else:
            hooks.pop(event, None)

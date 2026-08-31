#!/usr/bin/env -S uv run --script --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["tomlkit==0.13.2", "ruamel.yaml==0.18.6"]
# ///
"""Capture managed keys from a live tool config back into its .chezmoidata fragment.

Usage: cfg-capture.py claude|codex|serena

The fragment defines the managed paths (see the design doc in
docs/superpowers/specs/). For each leaf path in the fragment, the live value
is read and written into the fragment. Fails without touching the fragment if
any managed path is missing from the live file.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import tomlkit
from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()

TOOLS = {
    "claude": (HOME / ".claude/settings.json", REPO / ".chezmoidata/claude_managed.json", "claude_managed", "json"),
    "codex": (HOME / ".codex/config.toml", REPO / ".chezmoidata/codex_managed.toml", "codex_managed", "toml"),
    "serena": (HOME / ".serena/serena_config.yml", REPO / ".chezmoidata/serena_managed.yaml", "serena_managed", "yaml"),
}

yaml = YAML()
yaml.preserve_quotes = True


def load(path, fmt):
    text = path.read_text()
    if fmt == "json":
        return json.loads(text)
    if fmt == "toml":
        return tomlkit.parse(text)
    return yaml.load(text)


def dump(doc, path, fmt):
    if fmt == "json":
        text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    elif fmt == "toml":
        text = tomlkit.dumps(doc)
    else:
        import io

        buf = io.StringIO()
        yaml.dump(doc, buf)
        text = buf.getvalue()
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def capture(fragment_node, live_node, path, missing, changed):
    for key in list(fragment_node.keys()):
        value = fragment_node[key]
        here = path + "." + key if path else key
        if key not in live_node:
            missing.append(here)
        elif isinstance(value, dict) and value:
            live_child = live_node[key]
            if not hasattr(live_child, "keys"):
                missing.append(here + " (live value is not a mapping)")
            else:
                capture(value, live_child, here, missing, changed)
        else:
            live_value = live_node[key]
            plain_live = live_value.unwrap() if hasattr(live_value, "unwrap") else live_value
            plain_frag = value.unwrap() if hasattr(value, "unwrap") else value
            if plain_frag != plain_live:
                fragment_node[key] = plain_live
                changed.append(here)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in TOOLS:
        print("usage: cfg-capture.py " + "|".join(TOOLS), file=sys.stderr)
        return 2
    live_path, fragment_path, wrapper, fmt = TOOLS[sys.argv[1]]
    live = load(live_path, fmt)
    fragment = load(fragment_path, fmt)
    missing, changed = [], []
    capture(fragment[wrapper], live, "", missing, changed)
    if missing:
        print("managed paths missing from " + str(live_path) + ":", file=sys.stderr)
        for p in missing:
            print("  " + p, file=sys.stderr)
        print("fragment left untouched", file=sys.stderr)
        return 1
    if not changed:
        print("fragment already matches " + str(live_path))
        return 0
    dump(fragment, fragment_path, fmt)
    print("captured from " + str(live_path) + ":")
    for p in changed:
        print("  " + p)
    print("review with: git -C " + str(REPO) + " diff .chezmoidata")
    return 0


if __name__ == "__main__":
    sys.exit(main())

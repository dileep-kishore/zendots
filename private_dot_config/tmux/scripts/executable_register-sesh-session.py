#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from typing import List, NoReturn, Optional

DEFAULT_CONFIG = """sort_order = ["tmux", "config", "zoxide"]

[default_session]
preview_command = "eza --all --git --icons --color=always {}"
"""


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def resolve_dir(raw_input: Optional[str]) -> str:
    candidate = os.path.expanduser(raw_input or os.getcwd())
    path = Path(candidate)

    if not path.is_dir():
        missing = raw_input if raw_input is not None else candidate
        fail("Directory not found: {}".format(missing))

    return str(path.resolve())


def escape_toml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def config_file() -> Path:
    config_root = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return config_root / "sesh" / "sesh.toml"


def ensure_config_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(DEFAULT_CONFIG)


def trim_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] == '"':
        return stripped[1:-1]
    return stripped


def find_session_path(path: Path, session_name: str) -> Optional[str]:
    in_session = False
    name = ""
    session_path = ""

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if line == "[[session]]":
            if in_session and name == session_name:
                return session_path
            in_session = True
            name = ""
            session_path = ""
            continue

        if not in_session or "=" not in line:
            continue

        key, value = [part.strip() for part in line.split("=", 1)]
        if key == "name":
            name = trim_quotes(value)
        elif key == "path":
            session_path = trim_quotes(value)

    if in_session and name == session_name:
        return session_path

    return None


def append_session(path: Path, session_name: str, root_dir: str) -> None:
    with path.open("a") as handle:
        handle.write(
            '\n[[session]]\nname = "{}"\npath = "{}"\n'.format(
                escape_toml(session_name),
                escape_toml(root_dir),
            )
        )


def main(argv: List[str]) -> None:
    session_name = argv[1] if len(argv) > 1 else ""
    root_dir = resolve_dir(argv[2] if len(argv) > 2 else os.getcwd())

    if not session_name:
        fail("Usage: {} <session-name> [directory]".format(Path(argv[0]).name))

    sesh_config = config_file()
    ensure_config_file(sesh_config)

    existing_path = find_session_path(sesh_config, session_name)
    if existing_path:
        normalized_existing = os.path.expanduser(existing_path)
        if normalized_existing != root_dir:
            fail(
                "Session '{}' already points to {}".format(
                    session_name, normalized_existing
                )
            )
        return

    append_session(sesh_config, session_name, root_dir)


if __name__ == "__main__":
    main(sys.argv)

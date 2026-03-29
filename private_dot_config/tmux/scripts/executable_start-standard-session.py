#!/usr/bin/env python3

import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, NoReturn, Optional


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def short_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "session"


def resolve_dir(raw_input: Optional[str]) -> str:
    candidate = os.path.expanduser(raw_input or os.getcwd())
    path = Path(candidate)

    if not path.is_dir():
        missing = raw_input if raw_input is not None else candidate
        fail(f"Directory not found: {missing}")

    return str(path.resolve())


def tmux_session_exists(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def existing_session_path(session_name: str) -> str:
    result = subprocess.run(
        ["tmux", "display-message", "-p", "-t", session_name, "#{session_path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def tmuxp_command() -> List[str]:
    if shutil.which("tmuxp"):
        return ["tmuxp"]

    if shutil.which("uv"):
        return ["uvx", "--from", "tmuxp", "tmuxp"]

    fail("tmuxp is not installed and uv is unavailable.")


def main(argv: List[str]) -> None:
    root_dir = resolve_dir(argv[1] if len(argv) > 1 else os.getcwd())
    explicit_name = argv[2] if len(argv) > 2 else ""
    workspace = Path.home() / ".config" / "tmuxp" / "standard.yaml"

    if not workspace.is_file():
        fail(f"Workspace file not found: {workspace}")

    if explicit_name:
        session_name = explicit_name
    else:
        session_name = short_name(Path(root_dir).name)
        if tmux_session_exists(session_name):
            current_path = existing_session_path(session_name)
            if current_path != root_dir:
                suffix = hashlib.md5(root_dir.encode("utf-8")).hexdigest()[:6]
                session_name = f"{session_name}-{suffix}"

    if not tmux_session_exists(session_name):
        env = os.environ.copy()
        env["PROJECT_ROOT"] = root_dir
        subprocess.run(
            [*tmuxp_command(), "load", "-d", "-y", "-s", session_name, str(workspace)],
            env=env,
            check=True,
        )

    if os.environ.get("TMUX"):
        os.execvp("tmux", ["tmux", "switch-client", "-t", session_name])

    os.execvp("tmux", ["tmux", "attach-session", "-t", session_name])


if __name__ == "__main__":
    try:
        main(sys.argv)
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None

#!/usr/bin/env python3

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NoReturn

SELF = str(Path.home() / ".config" / "tmux" / "scripts" / "sesh-session-picker.py")
STARTER = str(Path.home() / ".config" / "tmux" / "scripts" / "start-standard-session.py")
BLUE = "\033[34m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[39m"


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def shorten_home(value: str) -> str:
    if not value:
        return ""

    home = str(Path.home())
    if value == home or value.startswith(f"{home}/"):
        return value.replace(home, "~", 1)

    return value


def sesh_entries() -> List[Dict[str, object]]:
    result = subprocess.run(
        ["sesh", "list", "--json"],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    return data if isinstance(data, list) else []


def print_rows(rows: List[List[str]]) -> None:
    for row in rows:
        print("\t".join(row))


def print_list(mode: str = "all") -> None:
    if mode == "find":
        result = subprocess.run(
            ["fd", "-H", "-d", "2", "-t", "d", "-E", ".Trash", ".", str(Path.home())],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
        rows: List[List[str]] = []
        for raw_path in result.stdout.splitlines():
            pretty = shorten_home(raw_path)
            rows.append(
                [f"{MAGENTA}{RESET}", pretty, pretty, "find", pretty, raw_path]
            )
        print_rows(rows)
        return

    if mode == "all":
        wanted_sources = {"tmux"}
    elif mode in {"tmux", "config", "zoxide"}:
        wanted_sources = {mode}
    else:
        fail(f"Unknown mode: {mode}")

    icons = {
        "tmux": f"{BLUE}{RESET}",
        "config": f"{YELLOW}{RESET}",
        "zoxide": f"{CYAN}{RESET}",
    }

    rows = []
    for entry in sesh_entries():
        source = str(entry.get("Src", ""))
        if source not in wanted_sources:
            continue

        name = str(entry.get("Name", ""))
        path = str(entry.get("Path") or "")
        rows.append(
            [icons[source], name, shorten_home(path), source, name, path]
        )

    print_rows(rows)


def preview_entry(source: str, name: str, path: str = "") -> None:
    if source == "tmux":
        result = subprocess.run(
            ["tmux", "capture-pane", "-e", "-p", "-t", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            check=False,
        )
        lines = result.stdout.splitlines()[-200:]
        if lines:
            print("\n".join(lines))
        return

    if source in {"config", "zoxide", "find"}:
        if path and Path(path).is_dir():
            print(shorten_home(path))
            print()
            result = subprocess.run(
                ["eza", "--icons", "auto", "--git", "-la", path],
                stdout=subprocess.PIPE,
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            lines = result.stdout.splitlines()[:200]
            if lines:
                print("\n".join(lines))
            return

        print(path)
        return

    print(name)


def tmux_session_exists(session_name: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def exec_command(command: List[str]) -> NoReturn:
    os.execvp(command[0], command)


def connect_entry(args: List[str]) -> None:
    if len(args) == 1:
        target = os.path.expanduser(args[0])

        if Path(target).is_dir():
            exec_command([STARTER, target])

        if tmux_session_exists(target):
            if os.environ.get("TMUX"):
                exec_command(["tmux", "switch-client", "-t", target])
            exec_command(["tmux", "attach-session", "-t", target])

        for entry in sesh_entries():
            if str(entry.get("Src", "")) != "config":
                continue
            if str(entry.get("Name", "")) != target:
                continue

            path = str(entry.get("Path") or "")
            exec_command([STARTER, path, target])

        if shutil.which("zoxide"):
            result = subprocess.run(
                ["zoxide", "query", target],
                stdout=subprocess.PIPE,
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            path = result.stdout.strip()
            if result.returncode == 0 and path:
                exec_command([STARTER, path])

        fail(f"Unable to resolve session or path: {target}")

    source = args[0] if len(args) > 0 else ""
    name = args[1] if len(args) > 1 else ""
    path = args[2] if len(args) > 2 else ""

    if source == "tmux":
        if os.environ.get("TMUX"):
            exec_command(["tmux", "switch-client", "-t", name])
        exec_command(["tmux", "attach-session", "-t", name])

    if source == "config":
        exec_command([STARTER, path, name])

    if source in {"zoxide", "find"}:
        exec_command([STARTER, path])

    fail(f"Unable to connect to source: {source}")


def pick_entry() -> None:
    source_rows = subprocess.run(
        [sys.executable, __file__, "list", "all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    ).stdout

    self_quoted = shlex.quote(SELF)
    fzf_command = [
        "fzf-tmux",
        "-p",
        "50%,70%",
        "--layout=reverse",
        "--delimiter=\t",
        "--with-nth=1,2,3",
        "--no-sort",
        "--ansi",
        "--border-label",
        "  TMUX Session Manager (sesh) ",
        "--prompt",
        "  ",
        "--header",
        "  ^a tmux ^s tmux ^g config ^x zoxide ^f find ^d tmux kill",
        "--bind",
        "tab:down,btab:up",
        "--bind",
        f"ctrl-a:change-prompt(  )+reload({self_quoted} list all)",
        "--bind",
        f"ctrl-s:change-prompt(  )+reload({self_quoted} list tmux)",
        "--bind",
        f"ctrl-g:change-prompt(  )+reload({self_quoted} list config)",
        "--bind",
        f"ctrl-x:change-prompt(  )+reload({self_quoted} list zoxide)",
        "--bind",
        f"ctrl-f:change-prompt(  )+reload({self_quoted} list find)",
        "--bind",
        f"ctrl-d:execute(if [ {{4}} = tmux ]; then tmux kill-session -t {{5}}; fi)+reload({self_quoted} list all)",
        "--preview-window",
        "up:70%",
        "--preview",
        f"{self_quoted} preview {{4}} {{5}} {{6}}",
    ]
    selected = subprocess.run(
        fzf_command,
        input=source_rows,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
    )

    if selected.returncode != 0:
        raise SystemExit(0)

    fields = selected.stdout.rstrip("\n").split("\t")
    if len(fields) < 6:
        raise SystemExit(0)

    connect_entry(fields[3:6])


def main(argv: List[str]) -> None:
    command = argv[1] if len(argv) > 1 else "pick"

    if command == "list":
        print_list(argv[2] if len(argv) > 2 else "all")
        return

    if command == "preview":
        preview_entry(
            argv[2] if len(argv) > 2 else "",
            argv[3] if len(argv) > 3 else "",
            argv[4] if len(argv) > 4 else "",
        )
        return

    if command == "connect":
        connect_entry(argv[2:])
        return

    if command == "pick":
        pick_entry()
        return

    fail(f"Unknown command: {command}")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None

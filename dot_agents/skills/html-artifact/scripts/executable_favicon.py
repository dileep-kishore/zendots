#!/usr/bin/env python3
"""Print a project's favicon: a 3x3 dot grid on a Catppuccin Mocha tile.

The lit dots form a left-right mirrored pattern and take one Catppuccin accent. Both derive from a
hash of the project name, so every page from one project shares an icon and projects differ at a
glance. The project name defaults to the main repository's directory, so linked worktrees match
their main checkout.

To pin a repository's icon, store an accent, a pattern, or both in its shared git config, which
every worktree reads and Syncthing carries between machines:

    git config zendots.favicon "mauve 111101111"

Flags override the pin; --project skips it and hashes the given name.

Usage: favicon.py [--project NAME] [--color NAME|#hex] [--pattern 101010101] [--svg]
Prints a <link rel="icon"> tag with an inline SVG data URI, or the bare SVG with --svg.
"""
from __future__ import annotations  # macOS /usr/bin/python3 is 3.9, which cannot evaluate str | None

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

MOCHA = {
    "rosewater": "#f5e0dc", "flamingo": "#f2cdcd", "pink": "#f5c2e7", "mauve": "#cba6f7",
    "red": "#f38ba8", "maroon": "#eba0ac", "peach": "#fab387", "yellow": "#f9e2af",
    "green": "#a6e3a1", "teal": "#94e2d5", "sky": "#89dceb", "sapphire": "#74c7ec",
    "blue": "#89b4fa", "lavender": "#b4befe",
}
# Hashing picks only from accents that stay distinct from each other at 16 px.
HASHED = ["red", "peach", "yellow", "green", "teal", "sapphire", "blue", "mauve", "pink"]
TILE, UNLIT = "#1e1e2e", "#45475a"
CONFIG_KEY = "zendots.favicon"


def mirrored(bits: int) -> str:
    """Six bits (left and middle columns, top to bottom) as a nine-character row-major grid."""
    left, mid = [(bits >> i) & 1 for i in range(3)], [(bits >> i) & 1 for i in range(3, 6)]
    return "".join(f"{left[r]}{mid[r]}{left[r]}" for r in range(3))


# Three to seven lit dots: fewer reads as a blank tile at 16 px, more as a full one.
PATTERNS = [p for p in map(mirrored, range(64)) if 3 <= p.count("1") <= 7]


def git(start: Path, *args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(start), *args], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def project_name(start: Path) -> str:
    common = git(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common is None:
        return start.resolve().name
    common_dir = Path(common)
    # A bare repository kept as proj/.bare beside its worktrees is named for proj.
    if common_dir.name in {".git", ".bare"}:
        common_dir = common_dir.parent
    return common_dir.name.removesuffix(".git")


def parse_color(value: str, source: str) -> str:
    if value.lower() in MOCHA:
        return value.lower()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        return value
    sys.exit(f"favicon.py: {source} color {value!r} must be one of {', '.join(MOCHA)} or #rrggbb")


def parse_pattern(value: str, source: str) -> str:
    if not re.fullmatch(r"[01]{9}", value) or "1" not in value:
        sys.exit(f"favicon.py: {source} pattern {value!r} must be nine 0/1 digits with at least one 1")
    return value


def pinned(start: Path) -> tuple[str | None, str | None]:
    """The accent and pattern from the repository's shared config, either of which may be absent."""
    # --local reads the common .git/config shared by worktrees, never ~/.gitconfig.
    value = git(start, "config", "--local", "--get", CONFIG_KEY)
    color = pattern = None
    for token in (value or "").split():
        if re.fullmatch(r"[01]+", token):
            pattern = parse_pattern(token, CONFIG_KEY)
        else:
            color = parse_color(token, CONFIG_KEY)
    return color, pattern


def svg(pattern: str, color: str) -> str:
    dots = "".join(
        f"<circle cx='{9 + 7 * (i % 3)}' cy='{9 + 7 * (i // 3)}' r='3.4' fill='{color if bit == '1' else UNLIT}'/>"
        for i, bit in enumerate(pattern)
    )
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='{TILE}'/>{dots}</svg>"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="name to hash; defaults to the git repository containing --dir")
    ap.add_argument("--dir", type=Path, default=Path.cwd(), help="where to look for the repository (default: cwd)")
    ap.add_argument("--color", help=f"accent name ({', '.join(MOCHA)}) or #rrggbb; overrides the hashed accent")
    ap.add_argument("--pattern", help="nine 0/1 digits, row by row; overrides the hashed pattern")
    ap.add_argument("--svg", action="store_true", help="print the bare SVG instead of a <link> tag")
    args = ap.parse_args()

    name = args.project or project_name(args.dir)
    digest = int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], "big")
    pin_color, pin_pattern = (None, None) if args.project else pinned(args.dir)
    color_name = (
        parse_color(args.color, "--color") if args.color else pin_color or HASHED[digest % len(HASHED)]
    )
    pattern = (
        parse_pattern(args.pattern, "--pattern")
        if args.pattern
        else pin_pattern or PATTERNS[(digest // len(HASHED)) % len(PATTERNS)]
    )

    icon = svg(pattern, MOCHA.get(color_name, color_name))
    if args.svg:
        print(icon)
    else:
        href = "data:image/svg+xml," + quote(icon, safe=" =:/'")
        print(f'<link rel="icon" type="image/svg+xml" href="{href}">')
    used_pin = (pin_color and not args.color) or (pin_pattern and not args.pattern)
    pin = f" ({CONFIG_KEY} pinned)" if used_pin else ""
    print(f"favicon.py: {name}: {color_name}, pattern {pattern[:3]}/{pattern[3:6]}/{pattern[6:]}{pin}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

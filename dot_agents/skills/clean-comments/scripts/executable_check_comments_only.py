#!/usr/bin/env python3
"""Report Python files whose code, not just comments, differs from a git revision.

Usage:
    check_comments_only.py [--base REV] [PATH ...]

Compares each changed, added, deleted, renamed, or untracked .py file under
PATH (default: the whole repository) with REV (default: HEAD). Tokens are
compared exactly, ignoring only ordinary comments and blank lines, so a
changed docstring, literal spelling, indentation, encoding, or tool pragma
(`# type:`, `# noqa`, ...) counts as code. Prints one line per offending
file (CODE CHANGED, NEW FILE, DELETED, or UNCHECKED when a version cannot be
tokenized) and exits 1 if there is any.

Examples:
    check_comments_only.py
    check_comments_only.py src/app.py tests/
    check_comments_only.py --base main
"""

import argparse
import io
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

PRAGMA = re.compile(rb"#\s*(type:|noqa|pragma|pylint:|pyright:|mypy:|ruff:|fmt:|isort:)")


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


def code_tokens(source):
    tokens = []
    for tok in tokenize.tokenize(io.BytesIO(source).readline):
        if tok.type == tokenize.NL:
            continue
        if tok.type == tokenize.COMMENT and not PRAGMA.match(tok.string.encode()):
            continue
        tokens.append((tok.type, tok.string))
    return tokens


def changed_pairs(root, base, paths):
    """Yield (old_path or None, new_path or None) for every changed .py file."""
    out = git(root, "diff", "--name-status", "-z", "-M", base, "--", *paths).split(b"\0")
    i = 0
    while i < len(out) - 1:
        status = out[i][:1]
        if status in (b"R", b"C"):
            old, new, i = out[i + 1], out[i + 2], i + 3
        else:
            old = new = out[i + 1]
            i += 2
        if status in (b"A", b"C"):
            old = None
        if status == b"D":
            new = None
        yield old, new
    untracked = git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", *paths)
    for new in untracked.split(b"\0"):
        if new:
            yield None, new


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="HEAD", help="git revision to compare against")
    parser.add_argument("paths", nargs="*", help="limit to these files or directories")
    args = parser.parse_args()

    root = Path(git(".", "rev-parse", "--show-toplevel").decode().strip())
    paths = [str(Path(p).resolve()) for p in args.paths] or ["."]
    failed = False
    for old, new in changed_pairs(root, args.base, paths):
        if not (old or new).endswith(b".py"):
            continue
        name = os.fsdecode(new or old)
        try:
            before = git(root, "cat-file", "blob", f"{args.base}:".encode() + old) if old else b""
            after = (root / os.fsdecode(new)).read_bytes() if new else b""
            same = code_tokens(before) == code_tokens(after)
        except (tokenize.TokenError, SyntaxError, OSError, subprocess.CalledProcessError) as exc:
            print(f"UNCHECKED: {name}: {exc}")
            failed = True
            continue
        if not same:
            label = "NEW FILE" if old is None else "DELETED" if new is None else "CODE CHANGED"
            print(f"{label}: {name}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

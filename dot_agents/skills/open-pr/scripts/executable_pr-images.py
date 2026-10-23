#!/usr/bin/env python3
"""Upload images for a PR description to the repository's pr-assets branch.

GitHub has no API for PR-description attachments, so images live on one orphan
branch, `pr-assets`, under `<name>/`. Each run adds a commit on top of that
branch without touching the working tree or the current branch, pushes it
without force, and prints Markdown image lines pinned to that commit. Pinned
links keep rendering after later uploads replace a file, so retakes are safe.

Refuses to run while per-PR branches `pr-assets/<x>` exist on the remote: git
cannot hold both, and deleting them would break the PRs that link to them.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

BRANCH = "pr-assets"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
EXAMPLES = """examples:
  pr-images.py --name chat-widgets shots/cutoff.png shots/replay.png
  pr-images.py --name chat-widgets --dry-run shots/*.png
  pr-images.py --repo ~/code/app --name login-form login.png
"""


def run(args: list[str], cwd: Path, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False, env=env)
    if check and result.returncode != 0:
        raise SystemExit(f"error: {' '.join(args)}: {result.stderr.strip() or result.stdout.strip()}")
    return result


def git(cwd: Path, *args: str, check: bool = True, env: dict[str, str] | None = None) -> str:
    return run(["git", *args], cwd, check, env).stdout.strip()


def web_base(root: Path, remote: str, push_url: str) -> str:
    # The rewritten push URL first, then the configured ones, which a rewrite to a local mirror hides.
    configured = [git(root, "config", "--get", f"remote.{remote}.{key}", check=False) for key in ("pushurl", "url")]
    urls = [push_url, *configured]
    for url in urls:
        match = re.match(r"^(?:[\w+]+://)?(?:[^@/]+@)?([^:/]+)(?::\d+)?[:/](.+?)(?:\.git)?/?$", url)
        if match:
            return f"https://{match.group(1)}/{match.group(2)}"
    raise SystemExit(f"error: cannot parse a host and owner/repo from {remote} URL {urls[0]}")


def remote_tip(root: Path, remote: str, push_url: str) -> str:
    """Return the remote pr-assets tip, or "" when the branch does not exist yet."""
    tip = ""
    nested = []
    for line in git(root, "ls-remote", push_url, f"refs/heads/{BRANCH}", f"refs/heads/{BRANCH}/*").splitlines():
        sha, _, ref = line.partition("\t")
        if ref == f"refs/heads/{BRANCH}":
            tip = sha
        elif ref.startswith(f"refs/heads/{BRANCH}/"):
            nested.append(ref.removeprefix("refs/heads/"))
    if nested:
        guide = Path(__file__).resolve().parent.parent / "references" / "pr-images.md"
        raise SystemExit(
            f"error: {remote} has per-PR image branches ({', '.join(nested)}); consolidate them into {BRANCH} first, as {guide} describes"
        )
    return tip


def build_commit(root: Path, push_url: str, tip: str, name: str, files: list[Path], dry_run: bool) -> tuple[str, list[str]]:
    """Return the commit holding the images (tip when nothing changed) and one status line per file."""
    if tip:
        # Objects only; an empty refmap skips the tracking ref, which a stale <remote>/pr-assets/<x> would block.
        git(root, "fetch", "--quiet", "--no-write-fetch-head", "--refmap=", push_url, f"refs/heads/{BRANCH}")
    statuses, updates = [], []
    for path in files:
        target = f"{name}/{path.name}"
        hash_args = ["hash-object", str(path)] if dry_run else ["hash-object", "-w", str(path)]
        blob = git(root, *hash_args)
        existing = git(root, "ls-tree", tip, "--", target).split() if tip else []
        if existing and existing[2] == blob:
            statuses.append(f"unchanged {target}")
            continue
        statuses.append(f"{'replaced' if existing else 'added'} {target}")
        updates.append((blob, target))
    if not updates or dry_run:
        return tip, statuses

    with tempfile.TemporaryDirectory() as scratch:
        # A private index keeps the user's staging area and working tree untouched.
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        git(root, "read-tree", tip if tip else "--empty", env=env)
        for blob, target in updates:
            git(root, "update-index", "--add", "--cacheinfo", f"100644,{blob},{target}", env=env)
        tree = git(root, "write-tree", env=env)
    parents = ["-p", tip] if tip else []
    commit = git(root, "commit-tree", tree, *parents, "-m", f"chore: add {name} PR images")
    return commit, statuses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", type=Path, help="image files (png, jpg, gif, webp)")
    parser.add_argument("--name", required=True, help="folder for this PR's images, usually the head branch without its type/ prefix")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="any checkout of the repository (default: cwd)")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--dry-run", action="store_true", help="report what would change; commits and pushes nothing")
    opts = parser.parse_args()

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", opts.name):
        raise SystemExit(f"error: --name {opts.name!r} must be one path segment of letters, digits, '.', '_' or '-'")
    files = [path.expanduser().resolve() for path in opts.files]
    for path in files:
        if not path.is_file():
            raise SystemExit(f"error: {path} is not a file")
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise SystemExit(f"error: {path.name} is not one of {', '.join(sorted(IMAGE_SUFFIXES))}")
    names = [path.name for path in files]
    if len(set(names)) != len(names):
        raise SystemExit("error: two files share a name; rename one so each gets its own link")

    root = Path(git(opts.repo.expanduser().resolve(), "rev-parse", "--show-toplevel"))
    # Reads, the push and the links all use the push repository, which a pushurl can point away from the fetch URL.
    push_url = git(root, "remote", "get-url", "--push", opts.remote)
    base = web_base(root, opts.remote, push_url)

    # One retry covers another upload landing between the read and the push.
    for attempt in (1, 2):
        tip = remote_tip(root, opts.remote, push_url)
        commit, statuses = build_commit(root, push_url, tip, opts.name, files, opts.dry_run)
        if opts.dry_run or commit == tip:
            break
        pushed = run(["git", "push", "--quiet", push_url, f"{commit}:refs/heads/{BRANCH}"], root, check=False)
        if pushed.returncode == 0:
            break
        if attempt == 2 or remote_tip(root, opts.remote, push_url) == tip:
            raise SystemExit(f"error: push to {opts.remote}/{BRANCH} failed: {pushed.stderr.strip()}")

    print(*statuses, sep="\n")
    if opts.dry_run:
        if all(status.startswith("unchanged ") for status in statuses):
            print(f"dry-run: already uploaded at {opts.remote}/{BRANCH} {tip[:9]}")
        else:
            print(f"dry-run: would commit on {opts.remote}/{BRANCH} at {tip[:9] or '(new orphan branch)'} and push")
        return 0
    print(f"commit {commit}")
    print(f"branch {opts.remote}/{BRANCH}")
    for path in files:
        # macOS screenshot names carry spaces, which end a Markdown link destination.
        alt = re.sub(r"([\\\[\]])", r"\\\1", path.stem)
        print(f"![{alt}]({base}/blob/{commit}/{opts.name}/{quote(path.name)}?raw=true)")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
    sys.exit(main())

"""Safe handling for Syncthing conflict copies."""

from __future__ import annotations

import filecmp
import hashlib
import os
import re
import shutil
import subprocess
import zlib
from dataclasses import dataclass
from pathlib import Path

from .manifest import UsageError

CONFLICT_RE = re.compile(
    r"^(?P<stem>.+)\.sync-conflict-\d{8}-\d{6}-[A-Za-z0-9]+"
    r"(?P<suffix>(?:\..*)?)$"
)


@dataclass(frozen=True)
class Conflict:
    """One conflict copy and the canonical path it shadows."""

    path: Path
    original: Path
    git_dir: Path | None
    action: str


@dataclass(frozen=True)
class ConflictReport:
    """Result of scanning or applying conflict recovery."""

    total: int
    quarantined: int
    restored: int
    unresolved: int
    recovery_root: Path | None


def _git_dir(path: Path) -> Path | None:
    parts = path.parts
    try:
        index = parts.index(".git")
    except ValueError:
        return None
    return Path(*parts[: index + 1])


def _original(path: Path) -> Path | None:
    match = CONFLICT_RE.match(path.name)
    if not match:
        return None
    return path.with_name(match.group("stem") + match.group("suffix"))


def _valid_loose_object(path: Path, expected: str) -> bool:
    if not path.is_file():
        return False
    algorithm = "sha1" if len(expected) == 40 else "sha256"
    try:
        raw = zlib.decompress(path.read_bytes())
    except (OSError, zlib.error):
        return False
    return hashlib.new(algorithm, raw).hexdigest() == expected


def _object_action(conflict: Path, original: Path, git_dir: Path) -> str | None:
    try:
        relative = original.relative_to(git_dir / "objects")
    except ValueError:
        return None
    if len(relative.parts) != 2:
        return None
    expected = "".join(relative.parts)
    if len(expected) not in {40, 64} or not all(
        character in "0123456789abcdef" for character in expected
    ):
        return None
    if _valid_loose_object(original, expected):
        return "quarantine"
    if _valid_loose_object(conflict, expected):
        return "restore-object"
    return "unresolved"


def _index_action(conflict: Path, original: Path, git_dir: Path) -> str | None:
    if original != git_dir / "index":
        return None

    def matches_head(index: Path) -> bool:
        if not index.is_file():
            return False
        result = subprocess.run(
            [
                "git",
                "-C",
                str(git_dir.parent),
                "diff-index",
                "--cached",
                "--quiet",
                "HEAD",
                "--",
            ],
            env={**os.environ, "GIT_INDEX_FILE": str(index)},
            capture_output=True,
            check=False,
        )
        return result.returncode == 0

    if matches_head(original):
        return "quarantine"
    if matches_head(conflict):
        return "restore-index"
    return "unresolved"


def scan_conflicts(root: Path) -> tuple[Conflict, ...]:
    """Classify every Syncthing conflict beneath root without changing files."""
    if not root.is_dir():
        raise UsageError(f"conflict scan path is not a directory: {root}")
    conflicts: list[Conflict] = []
    for path in sorted(root.rglob("*.sync-conflict-*")):
        if not path.is_file():
            continue
        original = _original(path)
        if original is None:
            continue
        git_dir = _git_dir(path)
        special_action = None
        if git_dir:
            special_action = _index_action(path, original, git_dir)
            special_action = special_action or _object_action(
                path, original, git_dir
            )
        if special_action:
            action = special_action
        elif git_dir or (
            original.is_file() and filecmp.cmp(path, original, shallow=False)
        ):
            action = "quarantine"
        else:
            action = "unresolved"
        conflicts.append(Conflict(path, original, git_dir, action))
    return tuple(conflicts)


def _backup(root: Path, recovery_root: Path, path: Path) -> Path:
    relative = path.relative_to(root)
    target = recovery_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return target


def _fsck(repo: Path) -> None:
    try:
        subprocess.run(
            ["git", "-C", str(repo), "fsck", "--connectivity-only", "--no-dangling"],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        message = (error.stderr or error.stdout).strip()
        raise UsageError(f"git fsck failed for {repo}: {message}") from error


def apply_conflicts(root: Path, recovery_root: Path) -> ConflictReport:
    """Recover valid objects and quarantine only conflicts safe to remove."""
    root = root.resolve()
    recovery_root = recovery_root.resolve()
    if recovery_root == root or root in recovery_root.parents:
        raise UsageError("recovery directory must be outside the scanned folder")
    conflicts = scan_conflicts(root)
    restored = 0
    quarantined = 0
    touched_repos: set[Path] = set()
    git_repos = {
        conflict.git_dir.parent
        for conflict in conflicts
        if conflict.git_dir and conflict.action == "quarantine"
    }

    for conflict in conflicts:
        if conflict.action not in {"restore-object", "restore-index"}:
            continue
        _backup(root, recovery_root, conflict.path)
        if conflict.original.exists():
            canonical_backup = _backup(root, recovery_root, conflict.original)
            canonical_backup.rename(
                canonical_backup.with_name(canonical_backup.name + ".canonical")
            )
        os.replace(conflict.path, conflict.original)
        restored += 1
        assert conflict.git_dir is not None
        touched_repos.add(conflict.git_dir.parent)

    for repo in touched_repos | git_repos:
        _fsck(repo)

    for conflict in conflicts:
        if conflict.action != "quarantine":
            continue
        _backup(root, recovery_root, conflict.path)
        conflict.path.unlink()
        quarantined += 1
        if conflict.git_dir:
            touched_repos.add(conflict.git_dir.parent)

    for repo in touched_repos:
        _fsck(repo)

    unresolved = sum(conflict.action == "unresolved" for conflict in conflicts)
    return ConflictReport(
        len(conflicts),
        quarantined,
        restored,
        unresolved,
        recovery_root if quarantined or restored else None,
    )

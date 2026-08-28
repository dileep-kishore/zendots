from __future__ import annotations

import hashlib
import subprocess
import zlib
from pathlib import Path

from typer.testing import CliRunner

from work_sync.cli import app


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def init_repo(path: Path) -> None:
    path.mkdir()
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Work Sync Test")
    git(path, "config", "user.email", "work-sync@example.test")
    (path / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-m", "base")


def test_conflicts_scan_reports_without_deleting(tmp_path: Path) -> None:
    original = tmp_path / "notes.txt"
    conflict = tmp_path / "notes.sync-conflict-20260828-120000-DEVICE.txt"
    original.write_text("current\n", encoding="utf-8")
    conflict.write_text("other\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["conflicts", str(tmp_path)])

    assert result.exit_code == 1
    assert "unresolved" in result.stdout.lower()
    assert original.exists()
    assert conflict.exists()


def test_conflicts_scan_reports_safe_actions(tmp_path: Path) -> None:
    original = tmp_path / "notes.txt"
    conflict = tmp_path / "notes.sync-conflict-20260828-120000-DEVICE.txt"
    original.write_text("same\n", encoding="utf-8")
    conflict.write_text("same\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["conflicts", str(tmp_path)])

    assert result.exit_code == 1
    assert "quarantinable 1" in result.stdout.lower()
    assert "unresolved 0" in result.stdout.lower()
    assert conflict.exists()


def test_conflicts_apply_quarantines_identical_copy(tmp_path: Path) -> None:
    root = tmp_path / "root"
    recovery = tmp_path / "recovery"
    root.mkdir()
    original = root / "notes.txt"
    conflict = root / "notes.sync-conflict-20260828-120000-DEVICE.txt"
    original.write_text("same\n", encoding="utf-8")
    conflict.write_text("same\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["conflicts", str(root), "--apply", "--recovery-root", str(recovery)],
    )

    assert result.exit_code == 0
    assert original.read_text(encoding="utf-8") == "same\n"
    assert not conflict.exists()
    assert any(path.name == conflict.name for path in recovery.rglob("*"))


def test_conflicts_apply_restores_valid_missing_git_object(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    recovery = tmp_path / "recovery"
    init_repo(repo)
    raw = b"blob 6\x00hello\n"
    object_id = hashlib.sha1(raw).hexdigest()
    directory = repo / ".git/objects" / object_id[:2]
    directory.mkdir(exist_ok=True)
    canonical = directory / object_id[2:]
    conflict = canonical.with_name(
        canonical.name + ".sync-conflict-20260828-120000-DEVICE"
    )
    conflict.write_bytes(zlib.compress(raw))

    result = CliRunner().invoke(
        app,
        ["conflicts", str(repo), "--apply", "--recovery-root", str(recovery)],
    )

    assert result.exit_code == 0
    assert canonical.exists()
    assert not conflict.exists()
    assert git(repo, "cat-file", "-p", object_id) == "hello"


def test_conflicts_apply_quarantines_git_metadata_after_fsck(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    recovery = tmp_path / "recovery"
    init_repo(repo)
    conflict = repo / ".git/FETCH_HEAD.sync-conflict-20260828-120000-DEVICE"
    conflict.write_text("stale\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["conflicts", str(repo), "--apply", "--recovery-root", str(recovery)],
    )

    assert result.exit_code == 0
    assert not conflict.exists()
    assert any(path.name == conflict.name for path in recovery.rglob("*"))
    git(repo, "fsck", "--connectivity-only", "--no-dangling")


def test_conflicts_apply_restores_index_matching_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    recovery = tmp_path / "recovery"
    init_repo(repo)
    stale_index = (repo / ".git/index").read_bytes()
    (repo / "tracked.txt").write_text("committed\n", encoding="utf-8")
    git(repo, "commit", "-am", "update")
    current_index = (repo / ".git/index").read_bytes()
    conflict = repo / ".git/index.sync-conflict-20260828-120000-DEVICE"
    conflict.write_bytes(current_index)
    (repo / ".git/index").write_bytes(stale_index)

    result = CliRunner().invoke(
        app,
        ["conflicts", str(repo), "--apply", "--recovery-root", str(recovery)],
    )

    assert result.exit_code == 0
    assert not conflict.exists()
    assert git(repo, "write-tree") == git(repo, "rev-parse", "HEAD^{tree}")
    assert git(repo, "status", "--short") == ""


def test_conflicts_apply_leaves_different_project_file_unresolved(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    recovery = tmp_path / "recovery"
    root.mkdir()
    original = root / "notes.txt"
    conflict = root / "notes.sync-conflict-20260828-120000-DEVICE.txt"
    original.write_text("current\n", encoding="utf-8")
    conflict.write_text("other\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["conflicts", str(root), "--apply", "--recovery-root", str(recovery)],
    )

    assert result.exit_code == 1
    assert original.exists()
    assert conflict.exists()


def test_conflicts_apply_checks_fsck_before_quarantining_git_metadata(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    recovery = tmp_path / "recovery"
    init_repo(repo)
    blob = git(repo, "rev-parse", "HEAD:tracked.txt")
    object_path = repo / ".git/objects" / blob[:2] / blob[2:]
    object_path.unlink()
    conflict = repo / ".git/FETCH_HEAD.sync-conflict-20260828-120000-DEVICE"
    conflict.write_text("stale\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["conflicts", str(repo), "--apply", "--recovery-root", str(recovery)],
    )

    assert result.exit_code == 1
    assert conflict.exists()


def test_conflicts_rejects_recovery_inside_synced_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    original = root / "notes.txt"
    conflict = root / "notes.sync-conflict-20260828-120000-DEVICE.txt"
    original.write_text("same\n", encoding="utf-8")
    conflict.write_text("same\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "conflicts",
            str(root),
            "--apply",
            "--recovery-root",
            str(root / "recovery"),
        ],
    )

    assert result.exit_code == 1
    assert conflict.exists()

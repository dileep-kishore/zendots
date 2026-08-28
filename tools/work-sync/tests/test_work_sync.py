from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from work_sync.handoff import (
    canonical_origin,
    preflight_repository,
    transfer_git_state,
)
from work_sync.manifest import UsageError, detect_host, load_manifest
from work_sync.syncthing import folder_payload, managed_patterns
from work_sync.system import Runner

ENTRY: dict[str, object] = {
    "id": "qbio",
    "label": "QBio_perspective",
    "mac": "/Volumes/WorkSSD/Work/Manuscripts/QBio_perspective",
    "tsuki": "/home/dileep/Documents/Work/Manuscripts/QBio_perspective",
    "class": "git",
    "git": "local",
    "ignore": [".git"],
}


def write_manifest(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text(json.dumps(entries), encoding="utf-8")


def git(repo: Path, *args: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def test_load_manifest_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY, ENTRY])

    with pytest.raises(UsageError, match="duplicate folder id"):
        load_manifest(path)


def test_manifest_selects_by_id_or_label(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY])
    manifest = load_manifest(path)

    assert manifest.select("qbio").label == "QBio_perspective"
    assert manifest.select("QBio_perspective").id == "qbio"


def test_detect_host_rejects_unknown_platform() -> None:
    assert detect_host("Darwin") == "mac"
    assert detect_host("Linux") == "tsuki"
    with pytest.raises(UsageError, match="unsupported host"):
        detect_host("Plan9")


def test_runner_wraps_remote_arguments() -> None:
    calls: list[tuple[list[str], str | None]] = []

    def execute(argv: list[str], input_text: str | None) -> str:
        calls.append((argv, input_text))
        return "ok"

    runner = Runner(local_host="mac", execute=execute)

    assert runner.run("tsuki", ["git", "status", "--short"]) == "ok"
    assert calls == [
        (
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "tsuki",
                "git status --short",
            ],
            None,
        )
    ]


def test_folder_payload_disables_metadata_sync(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY])
    folder = load_manifest(path).select("qbio")

    payload = folder_payload({}, folder, "MAC-ID", "TSUKI-ID", "mac")

    assert payload["ignorePerms"] is False
    assert payload["syncOwnership"] is False
    assert payload["sendOwnership"] is False
    assert payload["syncXattrs"] is False
    assert payload["sendXattrs"] is False


def test_sensitive_project_files_are_not_default_ignores(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY])
    patterns = managed_patterns(load_manifest(path).select("qbio"))

    assert ".env" not in patterns
    assert ".claude/settings.json" not in patterns
    assert ".codex/config.toml" not in patterns
    assert ".pi/settings.json" not in patterns


def test_git_handoff_reproduces_branch_index_and_worktree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.name", "Work Sync Test")
    git(source, "config", "user.email", "work-sync@example.test")
    git(source, "remote", "add", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("base\n", encoding="utf-8")
    (source / "delete-me.txt").write_text("delete me\n", encoding="utf-8")
    (source / "script.sh").write_text("#!/bin/sh\necho base\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "base")

    git(tmp_path, "clone", str(source), str(target))
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    git(target, "config", "work-sync.marker", "target-local")

    (source / "committed.txt").write_text("committed\n", encoding="utf-8")
    git(source, "add", "committed.txt")
    git(source, "commit", "-m", "source ahead")
    (source / "tracked.txt").write_text("staged\n", encoding="utf-8")
    git(source, "add", "tracked.txt")
    (source / "tracked.txt").write_text("unstaged\n", encoding="utf-8")
    (source / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    (source / "delete-me.txt").unlink()
    (source / "script.sh").chmod(0o755)
    git(source, "add", "script.sh")

    subprocess.run(
        [
            "rsync",
            "-r",
            "--delete",
            "--executability",
            "--exclude=.git/",
            f"{source}/",
            f"{target}/",
        ],
        check=True,
    )
    runner = Runner(local_host="mac")

    plan = preflight_repository(runner, "mac", source, "mac", target)
    transfer_git_state(runner, plan)

    assert git(target, "rev-parse", "HEAD") == git(source, "rev-parse", "HEAD")
    assert git(target, "diff", "--cached", "--binary") == git(
        source, "diff", "--cached", "--binary"
    )
    assert git(target, "diff", "--binary") == git(source, "diff", "--binary")
    assert git(target, "status", "--short") == git(source, "status", "--short")
    assert (target / "script.sh").stat().st_mode & 0o111
    assert git(target, "config", "work-sync.marker") == "target-local"
    assert canonical_origin(runner, "mac", target) == "github.com/example/project"


def test_git_handoff_rejects_target_only_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.name", "Work Sync Test")
    git(source, "config", "user.email", "work-sync@example.test")
    git(source, "remote", "add", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("same\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "base")
    git(tmp_path, "clone", str(source), str(target))
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    (target / "target-only.txt").write_text("do not delete\n", encoding="utf-8")

    with pytest.raises(UsageError, match="target files differ"):
        preflight_repository(Runner(local_host="mac"), "mac", source, "mac", target)


def test_git_handoff_rejects_divergence_without_changing_refs(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    git(source, "init", "-b", "main")
    git(source, "config", "user.name", "Work Sync Test")
    git(source, "config", "user.email", "work-sync@example.test")
    git(source, "remote", "add", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "base")
    git(tmp_path, "clone", str(source), str(target))
    git(target, "config", "user.name", "Work Sync Test")
    git(target, "config", "user.email", "work-sync@example.test")
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("source\n", encoding="utf-8")
    git(source, "commit", "-am", "source")
    (target / "tracked.txt").write_text("target\n", encoding="utf-8")
    git(target, "commit", "-am", "target")
    before = git(target, "show-ref")

    with pytest.raises(UsageError, match="diverged branch"):
        preflight_repository(Runner(local_host="mac"), "mac", source, "mac", target)

    assert git(target, "show-ref") == before

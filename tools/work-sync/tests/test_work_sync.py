from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from work_sync.cli import app
from work_sync.handoff import (
    Orca,
    OrcaRepo,
    OrcaWorktree,
    canonical_origin,
    pair_worktrees,
    parse_orca_inventory,
    preflight_repository,
    sync_worktree_files,
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


def test_manifest_git_folders_filters_non_git_defaults(tmp_path: Path) -> None:
    plain = {
        **ENTRY,
        "id": "presentations",
        "label": "Presentations",
        "class": "plain",
        "git": "none",
    }
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY, plain])
    manifest = load_manifest(path)

    assert [folder.id for folder in manifest.git_folders()] == ["qbio"]
    with pytest.raises(UsageError, match="Git folders only"):
        manifest.git_folders(("Presentations",))


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


def test_runner_replaces_undecodable_command_output() -> None:
    output = Runner(local_host="mac").run(
        "mac",
        [sys.executable, "-c", "import os; os.write(1, b'\\xef')"],
    )

    assert output == "�"


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


def test_external_handoff_allows_overwriting_a_clean_target(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    git(source, "init", "-b", "feat/a")
    git(source, "config", "user.name", "Work Sync Test")
    git(source, "config", "user.email", "work-sync@example.test")
    git(source, "remote", "add", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "base")
    git(tmp_path, "clone", str(source), str(target))
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("source work\n", encoding="utf-8")

    plan = preflight_repository(
        Runner(local_host="mac"),
        "mac",
        source,
        "mac",
        target,
        allow_clean_target_difference=True,
    )

    assert plan.target.path == target


def test_external_handoff_allows_source_additions_with_shared_target_dirt(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    git(source, "init", "-b", "feat/a")
    git(source, "config", "user.name", "Work Sync Test")
    git(source, "config", "user.email", "work-sync@example.test")
    git(source, "remote", "add", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "base")
    git(tmp_path, "clone", str(source), str(target))
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    for repo in (source, target):
        (repo / "shared-untracked.txt").write_text("shared\n", encoding="utf-8")
    (source / "source-only.txt").write_text("new\n", encoding="utf-8")

    plan = preflight_repository(
        Runner(local_host="mac"),
        "mac",
        source,
        "mac",
        target,
        allow_clean_target_difference=True,
    )

    assert plan.target.path == target


def test_external_handoff_rejects_target_only_dirty_content(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    git(source, "init", "-b", "feat/a")
    git(source, "config", "user.name", "Work Sync Test")
    git(source, "config", "user.email", "work-sync@example.test")
    git(source, "remote", "add", "origin", "git@github.com:example/project.git")
    (source / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(source, "add", ".")
    git(source, "commit", "-m", "base")
    git(tmp_path, "clone", str(source), str(target))
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    (target / "target-only.txt").write_text("unique\n", encoding="utf-8")

    with pytest.raises(UsageError, match="target files differ"):
        preflight_repository(
            Runner(local_host="mac"),
            "mac",
            source,
            "mac",
            target,
            allow_clean_target_difference=True,
        )


def test_orca_pairing_keeps_target_paths_and_finds_missing_branch() -> None:
    repos = {
        "ok": True,
        "result": {
            "repos": [
                {
                    "id": "repo-1",
                    "path": "/Volumes/WorkSSD/Work/project",
                    "displayName": "project",
                    "gitRemoteIdentity": {
                        "canonicalKey": "github.com/example/project"
                    },
                }
            ]
        },
    }
    source_worktrees = {
        "ok": True,
        "result": {
            "worktrees": [
                {
                    "worktreeId": "repo-1::/Volumes/WorkSSD/Work/project",
                    "repoId": "repo-1",
                    "path": "/Volumes/WorkSSD/Work/project",
                    "branch": "refs/heads/main",
                    "displayName": "main",
                    "isMainWorktree": True,
                    "agents": [],
                },
                {
                    "worktreeId": "repo-1::/Volumes/WorkSSD/superset/worktrees/project/feat/a",
                    "repoId": "repo-1",
                    "path": "/Volumes/WorkSSD/superset/worktrees/project/feat/a",
                    "branch": "refs/heads/feat/a",
                    "displayName": "feat/a",
                    "isMainWorktree": False,
                    "agents": [],
                },
                {
                    "worktreeId": "repo-1::/Volumes/WorkSSD/orca/workspaces/project/feat-b",
                    "repoId": "repo-1",
                    "path": "/Volumes/WorkSSD/orca/workspaces/project/feat-b",
                    "branch": "refs/heads/feat/b",
                    "displayName": "feat/b",
                    "isMainWorktree": False,
                    "agents": [],
                },
            ]
        },
    }
    target_worktrees = {
        "ok": True,
        "result": {
            "worktrees": [
                {
                    "worktreeId": "repo-1::/home/dileep/Documents/Work/project",
                    "repoId": "repo-1",
                    "path": "/home/dileep/Documents/Work/project",
                    "branch": "refs/heads/main",
                    "displayName": "main",
                    "isMainWorktree": True,
                    "agents": [],
                },
                {
                    "worktreeId": "repo-1::/home/dileep/.superset/worktrees/project/feat/a",
                    "repoId": "repo-1",
                    "path": "/home/dileep/.superset/worktrees/project/feat/a",
                    "branch": "refs/heads/feat/a",
                    "displayName": "feat/a",
                    "isMainWorktree": False,
                    "agents": [],
                },
            ]
        },
    }
    source = parse_orca_inventory(repos, source_worktrees).repos[0]
    target = parse_orca_inventory(repos, target_worktrees).repos[0]

    pairs = pair_worktrees(source, target)

    assert pairs[0].target is not None
    assert pairs[0].target.path == Path(
        "/home/dileep/.superset/worktrees/project/feat/a"
    )
    assert pairs[0].target.id.endswith("/home/dileep/.superset/worktrees/project/feat/a")
    assert pairs[1].source.branch == "feat/b"
    assert pairs[1].target is None


def test_orca_pairing_rejects_an_active_agent() -> None:
    source_worktree = OrcaWorktree(
        id="source::/source/feat/a",
        repo_id="source",
        path=Path("/source/feat/a"),
        branch="feat/a",
        display_name="feat/a",
        is_main=False,
        active_agents=("claude",),
    )
    target_worktree = OrcaWorktree(
        id="target::/target/feat/a",
        repo_id="target",
        path=Path("/target/feat/a"),
        branch="feat/a",
        display_name="feat/a",
        is_main=False,
        active_agents=(),
    )
    source = OrcaRepo(
        "source",
        Path("/source"),
        "project",
        "github.com/example/project",
        (source_worktree,),
    )
    target = OrcaRepo(
        "target",
        Path("/target"),
        "project",
        "github.com/example/project",
        (target_worktree,),
    )

    with pytest.raises(UsageError, match="active agent"):
        pair_worktrees(source, target)


def test_rsync_mirrors_worktree_and_keeps_recovery_copy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    recovery = tmp_path / "recovery"
    source.mkdir()
    target.mkdir()
    (source / "changed.txt").write_text("source\n", encoding="utf-8")
    (source / "script.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (source / "script.sh").chmod(0o755)
    (target / "changed.txt").write_text("target\n", encoding="utf-8")
    (target / "target-only.txt").write_text("keep me\n", encoding="utf-8")
    (target / ".git").write_text("gitdir: target-local\n", encoding="utf-8")
    (source / ".stfolder").mkdir()
    (target / ".stfolder").mkdir()
    (source / ".stfolder/marker").write_text("source\n", encoding="utf-8")
    (target / ".stfolder/marker").write_text("target\n", encoding="utf-8")
    (source / ".serena").mkdir()
    (target / ".serena").mkdir()
    (source / ".serena/project.yml").write_text("source\n", encoding="utf-8")
    (target / ".serena/project.yml").write_text("target\n", encoding="utf-8")

    changes = sync_worktree_files(
        Runner(local_host="mac"),
        "mac",
        source,
        "mac",
        target,
        recovery,
        excludes=(),
        dry_run=True,
    )
    assert changes
    assert (target / "changed.txt").read_text(encoding="utf-8") == "target\n"

    sync_worktree_files(
        Runner(local_host="mac"),
        "mac",
        source,
        "mac",
        target,
        recovery,
        excludes=(),
        dry_run=False,
    )

    assert (target / "changed.txt").read_text(encoding="utf-8") == "source\n"
    assert not (target / "target-only.txt").exists()
    assert (target / ".git").read_text(encoding="utf-8") == "gitdir: target-local\n"
    assert (target / ".stfolder/marker").read_text(encoding="utf-8") == "target\n"
    assert (target / ".serena/project.yml").read_text(encoding="utf-8") == "target\n"
    assert (target / "script.sh").stat().st_mode & 0o111
    assert (recovery / "changed.txt").read_text(encoding="utf-8") == "target\n"
    assert (recovery / "target-only.txt").read_text(encoding="utf-8") == "keep me\n"


def test_rsync_honors_manifest_reincludes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    recovery = tmp_path / "recovery"
    (source / "build").mkdir(parents=True)
    target.mkdir()
    (source / "build/main.pdf").write_bytes(b"main")
    (source / "build/supplement.pdf").write_bytes(b"supplement")
    (source / "build/disposable.log").write_text("ignore\n", encoding="utf-8")

    sync_worktree_files(
        Runner(local_host="mac"),
        "mac",
        source,
        "mac",
        target,
        recovery,
        excludes=("!/build/main.pdf", "!/build/supplement.pdf", "/build"),
        dry_run=False,
    )

    assert (target / "build/main.pdf").read_bytes() == b"main"
    assert (target / "build/supplement.pdf").read_bytes() == b"supplement"
    assert not (target / "build/disposable.log").exists()


def test_reverse_rsync_uses_the_mac_client() -> None:
    calls: list[list[str]] = []

    def execute(argv: list[str], input_text: str | None) -> str:
        calls.append(argv)
        return ""

    sync_worktree_files(
        Runner(local_host="tsuki", execute=execute),
        "tsuki",
        Path("/tmp/source"),
        "mac",
        Path("/private/tmp/target"),
        Path("/private/tmp/recovery"),
        excludes=(),
        dry_run=True,
    )

    assert calls[0][:5] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
    ]
    assert "rsync " in calls[0][-1]
    assert "tsuki:/tmp/source/ /private/tmp/target/" in calls[0][-1]


def test_orca_create_uses_linux_cli_and_skips_setup() -> None:
    calls: list[list[str]] = []

    def execute(argv: list[str], input_text: str | None) -> str:
        calls.append(argv)
        return json.dumps(
            {
                "ok": True,
                "result": {
                    "worktree": {
                        "id": "target::/home/dileep/orca/workspaces/project/feat-a",
                        "repoId": "target",
                        "path": "/home/dileep/orca/workspaces/project/feat-a",
                        "branch": "refs/heads/feat/a",
                        "displayName": "feat/a",
                        "isMainWorktree": False,
                        "agents": [],
                    }
                },
            }
        )

    runner = Runner(local_host="mac", execute=execute)
    source = OrcaWorktree(
        "source::/source/feat-a",
        "source",
        Path("/source/feat-a"),
        "feat/a",
        "feat/a",
        False,
        (),
    )
    target_repo = OrcaRepo(
        "target",
        Path("/target"),
        "project",
        "github.com/example/project",
        (),
    )

    created = Orca(runner).create_worktree("tsuki", target_repo, source, "main")

    assert created.branch == "feat/a"
    assert calls == [
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            "tsuki",
            (
                "orca-ide worktree create --repo id:target --name feat/a "
                "--base-branch main --setup skip --no-parent --json"
            ),
        ]
    ]


def test_orca_create_renames_version_normalized_branch() -> None:
    calls: list[list[str]] = []

    def execute(argv: list[str], input_text: str | None) -> str:
        calls.append(argv)
        if "worktree create" not in argv[-1]:
            return json.dumps({"ok": True, "result": {}})
        return json.dumps(
            {
                "ok": True,
                "result": {
                    "worktree": {
                        "id": "target::/target/worktree",
                        "repoId": "target",
                        "path": "/target/worktree",
                        "branch": "refs/heads/feat/feat-a",
                        "displayName": "feat/a",
                        "isMainWorktree": False,
                        "agents": [],
                    }
                },
            }
        )

    runner = Runner(local_host="mac", execute=execute)
    source = OrcaWorktree(
        "source::/source/feat-a",
        "source",
        Path("/source/feat-a"),
        "feat/a",
        "feat/a",
        False,
        (),
    )
    target_repo = OrcaRepo(
        "target",
        Path("/target"),
        "project",
        "github.com/example/project",
        (),
    )

    created = Orca(runner).create_worktree("tsuki", target_repo, source, "main")

    assert created.branch == "feat/a"
    assert calls[-2][-1] == "git -C /target/worktree branch -m feat/a"
    assert calls[-1][-1] == (
        "orca-ide worktree set --worktree path:/target/worktree "
        "--display-name feat/a --json"
    )


def test_root_help_contains_handoff_examples() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "target means the receiving machine" in result.stdout.lower()
    assert "work-sync handoff tsuki --dry-run" in result.stdout


def test_no_arguments_show_help() -> None:
    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert "bootstrap" in result.stdout
    assert "handoff" in result.stdout


def test_handoff_help_documents_repeatable_folder_and_confirmation() -> None:
    result = CliRunner().invoke(app, ["handoff", "--help"])

    assert result.exit_code == 0
    assert "--folder" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--yes" in result.stdout
    assert "work-sync handoff macmini --folder LifeOS" in result.stdout


def test_handoff_rejects_current_machine_as_target() -> None:
    result = CliRunner().invoke(app, ["handoff", "macmini", "--dry-run"])

    assert result.exit_code == 2
    assert "target is the current host" in result.output

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

import work_sync.add as add_module
from work_sync.add import (
    folder_id,
    infer_destination,
    install_manifest,
    manifest_with_folder,
    source_folder,
)
from work_sync.cli import app
from work_sync.coordinator import FolderHandoff, Handoff, HandoffPlan
from work_sync.handoff import (
    Orca,
    OrcaInventory,
    OrcaRepo,
    OrcaWorktree,
    RepositoryPlan,
    RepoState,
    pair_worktrees,
    parse_orca_inventory,
    preflight_repository,
    sync_worktree_files,
)
from work_sync.manifest import Folder, UsageError, detect_host, load_manifest
from work_sync.syncthing import (
    Syncthing,
    folder_payload,
    managed_patterns,
    reconcile_ignore_text,
    statuses_converged,
)
from work_sync.system import Runner

ENTRY: dict[str, object] = {
    "id": "qbio",
    "label": "QBio_perspective",
    "mac": "/Volumes/WorkSSD/Work/Manuscripts/QBio_perspective",
    "tsuki": "/home/dileep/Documents/Work/Manuscripts/QBio_perspective",
    "class": "git",
    "git": "local",
    "ignore": [],
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


def test_manifest_rejects_mismatched_cross_machine_relative_paths(
    tmp_path: Path,
) -> None:
    path = tmp_path / "folders.json"
    write_manifest(
        path,
        [
            {
                **ENTRY,
                "tsuki": "/home/dileep/Documents/Personal/QBio_perspective",
            }
        ],
    )

    with pytest.raises(UsageError, match="relative paths differ"):
        load_manifest(path)


def test_manifest_selects_by_id_or_label(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY])
    manifest = load_manifest(path)

    assert manifest.select("qbio").label == "QBio_perspective"
    assert manifest.select("QBio_perspective").id == "qbio"


def test_manifest_supports_worktree_only_ignores(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [{**ENTRY, "worktree_ignore": ["/data"]}])

    folder = load_manifest(path).select("qbio")

    assert folder.worktree_ignore == ("/data",)


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


def test_add_infers_the_same_relative_path_in_both_directions() -> None:
    mac = Path("/Volumes/WorkSSD/Work/Collaborations/new-project")
    tsuki = Path("/home/dileep/Documents/Work/Collaborations/new-project")

    assert infer_destination("mac", mac) == tsuki
    assert infer_destination("tsuki", tsuki) == mac


def test_add_rejects_a_source_outside_the_shared_roots() -> None:
    with pytest.raises(UsageError, match="outside /Volumes/WorkSSD"):
        infer_destination("mac", Path("/Users/dkishore/project"))


def test_add_detects_root_git_repository_and_plain_folder(tmp_path: Path) -> None:
    repo = tmp_path / "project"
    plain = tmp_path / "notes"
    repo.mkdir()
    plain.mkdir()
    git(repo, "init", "-b", "main")

    assert (
        source_folder("mac", repo, Path("/home/dileep/Documents/project")).folder_class
        == "git"
    )
    assert (
        source_folder(
            "mac", plain, Path("/home/dileep/Documents/notes")
        ).folder_class
        == "plain"
    )


def test_add_uses_a_stable_id_from_the_relative_path() -> None:
    relative = Path("Work/Collaborations/new-project")

    assert folder_id(relative) == folder_id(relative)
    assert folder_id(relative).startswith("new-project-")


def test_add_appends_only_the_new_manifest_entry(tmp_path: Path) -> None:
    path = tmp_path / "folders.json"
    original = json.dumps([ENTRY], indent=2) + "\n"
    path.write_text(original, encoding="utf-8")
    folder = source_folder(
        "mac",
        tmp_path,
        Path("/home/dileep/Documents/Work/new-project"),
        folder_class="plain",
    )

    updated = manifest_with_folder(original, folder)
    entries = json.loads(updated)

    assert entries[0] == ENTRY
    assert entries[1] == {
        "id": folder.id,
        "label": tmp_path.name,
        "mac": str(tmp_path),
        "tsuki": "/home/dileep/Documents/Work/new-project",
        "class": "plain",
        "git": "none",
        "ignore": [],
    }
    assert manifest_with_folder(updated, folder) == updated


def test_add_preserves_existing_manifest_formatting(tmp_path: Path) -> None:
    original = '[\n  {"id": "existing", "ignore": ["/one"]}\n]\n'
    folder = source_folder(
        "mac",
        tmp_path,
        Path("/home/dileep/Documents/Work/new-project"),
        folder_class="plain",
    )

    updated = manifest_with_folder(original, folder)

    assert updated.startswith(original[:-3] + ",\n")


def test_manifest_install_writes_directly_without_chezmoi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = {
        "mac": (tmp_path / "mac-source", tmp_path / "mac-applied"),
        "tsuki": (tmp_path / "tsuki-source", tmp_path / "tsuki-applied"),
    }
    files = {str(path): "old\n" for pair in paths.values() for path in pair}
    calls: list[list[str]] = []

    def execute(argv: list[str], input_text: str | None) -> str:
        command = shlex.split(argv[-1]) if argv and argv[0] == "ssh" else argv
        calls.append(command)
        if command[0] == "cat":
            return files[command[1]].strip()
        if command[0] == "tee":
            files[command[1]] = input_text or ""
        return ""

    class FakeSyncthing:
        def scan(self, host: str, folder_id: str) -> None:
            pass

        def wait_idle(self, folder_id: str, timeout: int) -> None:
            files[str(paths["tsuki"][0])] = files[str(paths["mac"][0])]

    monkeypatch.setattr(add_module, "MANIFEST_PATHS", paths)
    monkeypatch.setattr(add_module, "verify_manifest_copies", lambda runner: "ok")

    install_manifest(
        Runner(local_host="mac", execute=execute),
        FakeSyncthing(),  # type: ignore[arg-type]
        "old\n",
        "new\n",
        timeout=10,
    )

    assert all(
        files[str(path)] == "new\n" for pair in paths.values() for path in pair
    )
    assert not any(command[0] == "chezmoi" for command in calls)


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
    assert ".pixi" in patterns
    assert ".git" not in patterns
    assert ".git/worktrees" in patterns
    assert ".git/config.worktree" in patterns
    assert ".git/**.lock" in patterns


def test_ignore_reconciliation_replaces_legacy_git_rule_and_keeps_local_rules(
    tmp_path: Path,
) -> None:
    path = tmp_path / "folders.json"
    write_manifest(path, [ENTRY])
    folder = load_manifest(path).select("qbio")

    updated = reconcile_ignore_text(".git\n/local-only\n", folder)

    assert ".git\n" not in updated
    assert ".git/worktrees\n" in updated
    assert "/local-only\n" in updated


def test_git_filesystem_settings_move_to_machine_local_config(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "core.filemode", "false")
    git(repo, "config", "core.ignorecase", "true")

    Syncthing(Runner(local_host="mac"))._migrate_git_config("mac", repo)

    shared = (repo / ".git/config").read_text(encoding="utf-8")
    local = (repo / ".git/config.worktree").read_text(encoding="utf-8")
    assert "worktreeConfig = true" in shared
    assert "filemode" not in shared
    assert "ignorecase" not in shared
    assert "filemode = false" in local
    assert "ignorecase = true" in local


def test_syncthing_control_files_are_locally_git_ignored(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")

    Syncthing(Runner(local_host="mac"))._add_local_git_exclude("mac", repo)

    excludes = (repo / ".git/info/exclude").read_text(encoding="utf-8").splitlines()
    assert ".stignore" in excludes
    assert ".stfolder" in excludes


def test_syncthing_idle_status_requires_cross_device_sequence_convergence() -> None:
    statuses = {
        "mac": {
            "state": "idle",
            "sequence": 10,
            "remoteSequence": {"tsuki": 8},
        },
        "tsuki": {
            "state": "idle",
            "sequence": 12,
            "remoteSequence": {"mac": 8},
        },
    }

    assert not statuses_converged(statuses)
    statuses["mac"]["remoteSequence"] = {"tsuki": 12}
    statuses["tsuki"]["remoteSequence"] = {"mac": 10}
    assert statuses_converged(statuses)


def test_syncthing_scan_uses_authenticated_rest_post() -> None:
    calls: list[tuple[list[str], str | None]] = []

    def execute(argv: list[str], input_text: str | None) -> str:
        calls.append((argv, input_text))
        if "apikey" in argv:
            return "secret"
        if "raw-address" in argv:
            return "127.0.0.1:8384"
        return ""

    Syncthing(Runner(local_host="mac", execute=execute)).scan("mac", "folder-id")

    assert calls[-1] == (
        [
            "curl",
            "-fsS",
            "-X",
            "POST",
            "-H",
            "@-",
            "http://127.0.0.1:8384/rest/db/scan?folder=folder-id",
        ],
        "X-API-Key: secret\n",
    )


def test_new_folder_target_must_be_missing_or_empty(tmp_path: Path) -> None:
    service = Syncthing(Runner(local_host="mac"))
    target = tmp_path / "target"

    assert service._target_state("mac", target) == "missing"
    target.mkdir()
    assert service._target_state("mac", target) == "empty"
    (target / "existing.txt").write_text("keep\n", encoding="utf-8")
    assert service._target_state("mac", target) == "nonempty"


def test_handoff_with_no_external_worktrees_does_not_touch_main_git_state() -> None:
    class NoMainMutationRunner:
        local_host = "mac"

        def run(self, *args: object, **kwargs: object) -> str:
            raise AssertionError("main Git state must be left to Syncthing")

    folder = Folder(
        "project",
        "project",
        Path("/Volumes/WorkSSD/Work/project"),
        Path("/home/dileep/Documents/Work/project"),
        "git",
        "local",
        (),
    )
    state = RepoState(
        "mac",
        folder.mac,
        "github.com/example/project",
        "main",
        "a" * 40,
        {"main": "a" * 40},
        "",
        "",
    )
    repository = RepositoryPlan(
        NoMainMutationRunner(), state, replace(state, host="tsuki", path=folder.tsuki)
    )  # type: ignore[arg-type]
    plan = HandoffPlan(
        "mac",
        "tsuki",
        (FolderHandoff(folder, repository, None, None, (), ()),),
        Path("/tmp/recovery"),
    )

    results = Handoff(NoMainMutationRunner(), None, None).execute(plan)  # type: ignore[arg-type]

    assert results[0].worktrees == 0


def test_preflight_ignores_unrelated_lock_but_rejects_index_lock(
    tmp_path: Path,
) -> None:
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
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    git_dir = Path(git(source, "rev-parse", "--absolute-git-dir"))
    (git_dir / "project.lock").touch()

    assert preflight_repository(
        Runner(local_host="mac"), "mac", source, "mac", target
    )

    (git_dir / "index.lock").touch()
    with pytest.raises(UsageError, match="index.lock"):
        preflight_repository(
            Runner(local_host="mac"), "mac", source, "mac", target
        )


def test_preflight_rejects_syncthing_conflict_copies(tmp_path: Path) -> None:
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
    git(target, "remote", "set-url", "origin", "git@github.com:example/project.git")
    conflict = source / "notes.sync-conflict-20260828-120000-DEVICE.txt"
    conflict.write_text("unresolved\n", encoding="utf-8")

    with pytest.raises(UsageError, match="Syncthing conflict"):
        preflight_repository(
            Runner(local_host="mac"), "mac", source, "mac", target
        )


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
    target = replace(target, identity="github.com/example/upstream")

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


def test_orca_pairing_rejects_a_target_only_active_worktree() -> None:
    source = OrcaRepo(
        "source",
        Path("/source"),
        "project",
        "github.com/example/project",
        (),
    )
    target = OrcaRepo(
        "target",
        Path("/target"),
        "project",
        "github.com/example/project",
        (
            OrcaWorktree(
                id="target::/target/feat/a",
                repo_id="target",
                path=Path("/target/feat/a"),
                branch="feat/a",
                display_name="feat/a",
                is_main=False,
                active_agents=("codex",),
            ),
        ),
    )

    with pytest.raises(UsageError, match="active agent"):
        pair_worktrees(source, target)


def test_rsync_mirrors_worktree_and_keeps_recovery_copy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    target = tmp_path / "target"
    recovery = tmp_path / "recovery"
    source.mkdir()
    target.mkdir()
    external = tmp_path / "external-data"
    external.mkdir()
    (target / "data").symlink_to(external, target_is_directory=True)
    (source / "changed.txt").write_text("source\n", encoding="utf-8")
    (source / "script.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (source / "script.sh").chmod(0o755)
    (target / "changed.txt").write_text("target\n", encoding="utf-8")
    (target / "target-only.txt").write_text("keep me\n", encoding="utf-8")
    (target / ".git").write_text("gitdir: target-local\n", encoding="utf-8")
    (source / "nested/.git").mkdir(parents=True)
    (target / "nested/.git").mkdir(parents=True)
    (source / "nested/.git/index").write_text("source\n", encoding="utf-8")
    (target / "nested/.git/index").write_text("target\n", encoding="utf-8")
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
    assert (target / "nested/.git/index").read_text(encoding="utf-8") == "target\n"
    assert (target / ".stfolder/marker").read_text(encoding="utf-8") == "target\n"
    assert (target / ".serena/project.yml").read_text(encoding="utf-8") == "target\n"
    assert (target / "data").readlink() == external
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

    rsync_call = next(call for call in calls if "rsync " in call[-1])
    assert rsync_call[:5] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
    ]
    assert "tsuki:/tmp/source/ /private/tmp/target/" in rsync_call[-1]


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


def test_orca_verification_uses_stable_path_and_branch() -> None:
    path = Path("/target/worktree")
    current = OrcaWorktree(
        "inventory-id", "repo", path, "feat/a", "feat/a", False, ()
    )
    repo = OrcaRepo(
        "repo",
        Path("/target"),
        "project",
        "github.com/example/project",
        (current,),
    )

    class InventoryOrca(Orca):
        def inventory(self, host: str) -> OrcaInventory:  # type: ignore[override]
            return OrcaInventory((repo,))

    created = OrcaWorktree(
        "create-response-id", "repo", path, "feat/a", "feat/a", False, ()
    )

    InventoryOrca(Runner(local_host="mac")).verify_worktree(
        "mac", repo.path, created
    )


def test_root_help_contains_handoff_examples() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "target means the receiving machine" in result.stdout.lower()
    assert "orca worktrees" in result.stdout.lower()
    assert "work-sync handoff tsuki --dry-run" in result.stdout


def test_no_arguments_show_help() -> None:
    result = CliRunner().invoke(app, [])

    assert result.exit_code == 0
    assert "add" in result.stdout
    assert "bootstrap" in result.stdout
    assert "conflicts" in result.stdout
    assert "handoff" in result.stdout


def test_add_help_documents_smart_destination_and_confirmation() -> None:
    result = CliRunner().invoke(app, ["add", "--help"])

    assert result.exit_code == 0
    assert "--destination" in result.stdout
    assert "--yes" in result.stdout
    assert "work-sync add" in result.stdout


def test_handoff_help_documents_repeatable_folder_and_confirmation() -> None:
    result = CliRunner().invoke(app, ["handoff", "--help"])

    assert result.exit_code == 0
    assert "--folder" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--yes" in result.stdout
    assert "work-sync handoff macmini --folder LifeOS" in result.stdout


def test_handoff_rejects_current_machine_as_target() -> None:
    target = "macmini" if detect_host() == "mac" else "tsuki"
    result = CliRunner().invoke(app, ["handoff", target, "--dry-run"])

    assert result.exit_code == 2
    assert "target is the current host" in result.output

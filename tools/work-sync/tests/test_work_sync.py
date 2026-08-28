from __future__ import annotations

import json
from pathlib import Path

import pytest

from work_sync.manifest import UsageError, detect_host, load_manifest
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

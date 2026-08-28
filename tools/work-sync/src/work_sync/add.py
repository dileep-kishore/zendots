"""Plan a new folder shared between macmini and tsuki."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from .coordinator import MANIFEST_PATHS, verify_manifest_copies
from .manifest import Folder, FolderClass, GitPolicy, Host, UsageError
from .syncthing import Syncthing
from .system import Runner

SYNC_ROOTS: dict[Host, Path] = {
    "mac": Path("/Volumes/WorkSSD"),
    "tsuki": Path("/home/dileep/Documents"),
}


def _normalized(path: Path) -> Path:
    return Path(os.path.normpath(path.expanduser()))


def infer_destination(source_host: Host, source: Path) -> Path:
    """Mirror a source's relative path beneath the other machine's root."""
    source = _normalized(source)
    root = SYNC_ROOTS[source_host]
    try:
        relative = source.relative_to(root)
    except ValueError as error:
        raise UsageError(f"source is outside {root}: {source}") from error
    if relative == Path("."):
        raise UsageError(f"refusing to sync the whole root: {root}")
    target: Host = "tsuki" if source_host == "mac" else "mac"
    return SYNC_ROOTS[target] / relative


def folder_id(relative: Path) -> str:
    """Create a repeatable Syncthing ID from a shared relative path."""
    slug = re.sub(r"[^a-z0-9]+", "-", relative.name.lower()).strip("-")
    digest = hashlib.sha256(relative.as_posix().encode()).hexdigest()[:8]
    return f"{slug or 'folder'}-{digest}"


def _detect_class(source: Path) -> FolderClass:
    result = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if (
        result.returncode == 0
        and Path(result.stdout.strip()).resolve() == source.resolve()
    ):
        return "git"
    return "plain"


def source_folder(
    source_host: Host,
    source: Path,
    destination: Path,
    *,
    folder_class: FolderClass | None = None,
) -> Folder:
    """Build a manifest folder from one local source and target path."""
    source = _normalized(source)
    destination = _normalized(destination)
    target_host: Host = "tsuki" if source_host == "mac" else "mac"
    try:
        relative = destination.relative_to(SYNC_ROOTS[target_host])
    except ValueError as error:
        raise UsageError(
            f"destination is outside {SYNC_ROOTS[target_host]}: {destination}"
        ) from error
    kind = folder_class or _detect_class(source)
    policy: dict[FolderClass, GitPolicy] = {
        "git": "local",
        "plain": "none",
        "container": "nested-local",
    }
    paths = {source_host: source, target_host: destination}
    return Folder(
        id=folder_id(relative),
        label=source.name,
        mac=paths["mac"],
        tsuki=paths["tsuki"],
        folder_class=kind,
        git=policy[kind],
        ignore=(),
    )


def manifest_with_folder(current: str, folder: Folder) -> str:
    """Append one folder without rewriting existing manifest entries."""
    try:
        entries = json.loads(current)
    except json.JSONDecodeError as error:
        raise UsageError(f"cannot parse private manifest: {error}") from error
    if not isinstance(entries, list):
        raise UsageError("manifest must contain a JSON list")
    new_entry = {
        "id": folder.id,
        "label": folder.label,
        "mac": str(folder.mac),
        "tsuki": str(folder.tsuki),
        "class": folder.folder_class,
        "git": folder.git,
        "ignore": [],
    }
    if new_entry in entries:
        return current
    if any(
        isinstance(entry, dict)
        and (
            entry.get("id") == folder.id
            or entry.get("label") == folder.label
            or entry.get("mac") == str(folder.mac)
            or entry.get("tsuki") == str(folder.tsuki)
        )
        for entry in entries
    ):
        raise UsageError(f"folder is already present in the manifest: {folder.label}")
    serialized = "\n".join(
        f"  {line}" for line in json.dumps(new_entry, indent=2).splitlines()
    )
    body = current.rstrip()
    separator = ",\n" if entries else "\n"
    return body[:-1].rstrip() + separator + serialized + "\n]\n"


def _write(runner: Runner, host: Host, path: Path, text: str) -> None:
    runner.run(host, ["mkdir", "-p", str(path.parent)])
    runner.run(host, ["tee", str(path)], input_text=text)
    runner.run(host, ["chmod", "0600", str(path)])


def install_manifest(
    runner: Runner,
    syncthing: Syncthing,
    current: str,
    updated: str,
    *,
    timeout: int,
) -> None:
    """Propagate one approved manifest update through the Zendots folder."""
    if current == updated:
        return
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    for host, paths in MANIFEST_PATHS.items():
        home = Path("/Users/dkishore" if host == "mac" else "/home/dileep")
        for index, path in enumerate(paths):
            backup = (
                home
                / ".local/state/work-sync/manifest"
                / stamp
                / f"{index}-folders.json"
            )
            _write(runner, host, backup, runner.run(host, ["cat", str(path)]) + "\n")

    source, applied = MANIFEST_PATHS[runner.local_host]
    _write(runner, runner.local_host, source, updated)
    _write(runner, runner.local_host, applied, updated)
    for host in ("mac", "tsuki"):
        syncthing.scan(host, "zendots")
    syncthing.wait_idle("zendots", timeout)

    target: Host = "tsuki" if runner.local_host == "mac" else "mac"
    remote_source, remote_applied = MANIFEST_PATHS[target]
    if runner.run(target, ["cat", str(remote_source)]) + "\n" != updated:
        raise UsageError("Zendots synchronized without the new manifest entry")
    _write(runner, target, remote_applied, updated)
    verify_manifest_copies(runner)

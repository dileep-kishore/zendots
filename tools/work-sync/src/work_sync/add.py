"""Plan a new folder shared between the configured machines."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from .coordinator import MANIFEST_PATHS, verify_manifest_copies
from .manifest import (
    HOSTS,
    Folder,
    FolderClass,
    GitPolicy,
    Host,
    PathKey,
    UsageError,
)
from .syncthing import Syncthing
from .system import Runner

SYNC_ROOTS: dict[PathKey, Path] = {
    "mac": Path("/Volumes/WorkSSD"),
    "tsuki": Path("/home/dileep/Documents"),
}


def _normalized(path: Path) -> Path:
    return Path(os.path.normpath(path.expanduser()))


def _other_key(host: Host) -> PathKey:
    return "tsuki" if HOSTS[host].path_key == "mac" else "mac"


def infer_destination(source_host: Host, source: Path) -> Path:
    """Mirror a source's relative path beneath the other platform's root."""
    source = _normalized(source)
    root = SYNC_ROOTS[HOSTS[source_host].path_key]
    try:
        relative = source.relative_to(root)
    except ValueError as error:
        raise UsageError(f"source is outside {root}: {source}") from error
    if relative == Path("."):
        raise UsageError(f"refusing to sync the whole root: {root}")
    return SYNC_ROOTS[_other_key(source_host)] / relative


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
    target_key = _other_key(source_host)
    try:
        relative = destination.relative_to(SYNC_ROOTS[target_key])
    except ValueError as error:
        raise UsageError(
            f"destination is outside {SYNC_ROOTS[target_key]}: {destination}"
        ) from error
    kind = folder_class or _detect_class(source)
    policy: dict[FolderClass, GitPolicy] = {
        "git": "local",
        "plain": "none",
        "container": "nested-local",
    }
    paths = {HOSTS[source_host].path_key: source, target_key: destination}
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
    hosts: Sequence[Host],
) -> None:
    """Propagate one approved manifest update to the given reachable hosts."""
    if current == updated:
        return
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    for host in hosts:
        for index, path in enumerate(MANIFEST_PATHS[host]):
            backup = (
                HOSTS[host].home
                / ".local/state/work-sync/manifest"
                / stamp
                / f"{index}-folders.json"
            )
            _write(runner, host, backup, runner.run(host, ["cat", str(path)]) + "\n")

    source, applied = MANIFEST_PATHS[runner.local_host]
    _write(runner, runner.local_host, source, updated)
    _write(runner, runner.local_host, applied, updated)
    for host in hosts:
        syncthing.scan(host, "zendots")
    syncthing.wait_idle("zendots", timeout, syncthing.device_ids(hosts))

    for target in hosts:
        if target == runner.local_host:
            continue
        remote_source, remote_applied = MANIFEST_PATHS[target]
        if runner.run(target, ["cat", str(remote_source)]) + "\n" != updated:
            raise UsageError(
                f"Zendots synchronized to {target} without the new manifest entry"
            )
        _write(runner, target, remote_applied, updated)
    verify_manifest_copies(runner, hosts)

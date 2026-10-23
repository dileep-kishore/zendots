"""Private folder manifest loading and validation."""

from __future__ import annotations

import json
import os
import platform
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

Host = Literal["mac", "macbook", "tsuki"]
PathKey = Literal["mac", "tsuki"]
Platform = Literal["darwin", "linux"]
FolderClass = Literal["git", "plain", "container"]
GitPolicy = Literal["local", "nested-local", "none"]


@dataclass(frozen=True)
class HostInfo:
    """Fixed facts about one machine."""

    path_key: PathKey
    alias: str
    platform: Platform
    home: Path


# The MacBook mounts /Volumes/WorkSSD under the same account, so it reuses the
# Mac Mini's manifest paths.
HOSTS: dict[Host, HostInfo] = {
    "mac": HostInfo("mac", "macmini", "darwin", Path("/Users/dkishore")),
    "macbook": HostInfo("mac", "macbook", "darwin", Path("/Users/dkishore")),
    "tsuki": HostInfo("tsuki", "tsuki", "linux", Path("/home/dileep")),
}
HOST_NAMES: tuple[Host, ...] = tuple(HOSTS)
HOST_ENV = "WORK_SYNC_HOST"
HOST_FILE = Path(".config/work-sync/host")

MAC_ROOTS = (
    "/Volumes/WorkSSD/Work",
    "/Volumes/WorkSSD/Personal",
    "/Volumes/WorkSSD/LifeOS",
    "/Volumes/WorkSSD/Ideaverse",
    "/Users/dkishore/zendots",
)
TSUKI_ROOTS = (
    "/home/dileep/Documents/Work",
    "/home/dileep/Documents/Personal",
    "/home/dileep/Documents/LifeOS",
    "/home/dileep/Documents/Ideaverse",
    "/home/dileep/zendots",
)
MAC_SYNC_ROOT = Path("/Volumes/WorkSSD")
TSUKI_SYNC_ROOT = Path("/home/dileep/Documents")
ZENDOTS_PATHS = (Path("/Users/dkishore/zendots"), Path("/home/dileep/zendots"))


def alias(host: Host) -> str:
    """Return the SSH alias, which is also the user-facing machine name."""
    return HOSTS[host].alias


def host_for_alias(name: str) -> Host:
    """Return the host whose SSH alias is the given machine name."""
    for host, info in HOSTS.items():
        if info.alias == name:
            return host
    raise UsageError(f"unknown machine: {name}")


class UsageError(ValueError):
    """Raised when user-controlled configuration is unsafe or invalid."""


@dataclass(frozen=True)
class Folder:
    """One folder shared between the configured machines."""

    id: str
    label: str
    mac: Path
    tsuki: Path
    folder_class: FolderClass
    git: GitPolicy
    ignore: tuple[str, ...]
    worktree_ignore: tuple[str, ...] = ()

    def path(self, host: Host) -> Path:
        """Return this folder's path on a host."""
        return self.mac if HOSTS[host].path_key == "mac" else self.tsuki


@dataclass(frozen=True)
class Manifest:
    """Validated collection of shared folders."""

    folders: tuple[Folder, ...]

    def select(self, selector: str) -> Folder:
        """Select exactly one folder by ID or label."""
        matches = [
            folder for folder in self.folders if selector in {folder.id, folder.label}
        ]
        if len(matches) != 1:
            raise UsageError(
                f"folder selector must match exactly one entry: {selector}"
            )
        return matches[0]

    def git_folders(self, selectors: tuple[str, ...] = ()) -> tuple[Folder, ...]:
        """Return selected Git folders, or every Git folder when none are named."""
        folders = (
            tuple(self.select(selector) for selector in selectors)
            if selectors
            else tuple(
                folder for folder in self.folders if folder.folder_class == "git"
            )
        )
        non_git = [folder.label for folder in folders if folder.folder_class != "git"]
        if non_git:
            raise UsageError("handoff accepts Git folders only: " + ", ".join(non_git))
        return tuple(dict.fromkeys(folders))


def _within(path: str, roots: tuple[str, ...]) -> bool:
    normalized = os.path.normpath(path)
    if not os.path.isabs(normalized):
        return False
    return any(os.path.commonpath((normalized, root)) == root for root in roots)


def _folder(raw: object) -> Folder:
    if not isinstance(raw, dict):
        raise UsageError(f"invalid manifest entry: {raw!r}")
    required = {"id", "label", "mac", "tsuki", "class", "git", "ignore"}
    if not required <= raw.keys():
        missing = ", ".join(sorted(required - raw.keys()))
        raise UsageError(f"manifest entry is missing: {missing}")
    strings = ("id", "label", "mac", "tsuki", "class", "git")
    if any(not isinstance(raw[key], str) or not raw[key] for key in strings):
        raise UsageError(f"manifest entry has an invalid string field: {raw!r}")
    if raw["class"] not in {"git", "plain", "container"}:
        raise UsageError(f"invalid folder class: {raw['class']}")
    if raw["git"] not in {"local", "nested-local", "none"}:
        raise UsageError(f"invalid Git policy: {raw['git']}")
    expected_git = {"git": "local", "plain": "none", "container": "nested-local"}
    if raw["git"] != expected_git[raw["class"]]:
        raise UsageError(
            f"inconsistent class and Git policy: {raw['class']}/{raw['git']}"
        )
    if not _within(raw["mac"], MAC_ROOTS):
        raise UsageError(f"unsafe Mac path: {raw['mac']}")
    if not _within(raw["tsuki"], TSUKI_ROOTS):
        raise UsageError(f"unsafe tsuki path: {raw['tsuki']}")
    mac_path = Path(raw["mac"])
    tsuki_path = Path(raw["tsuki"])
    if (mac_path, tsuki_path) != ZENDOTS_PATHS:
        try:
            paths_match = mac_path.relative_to(MAC_SYNC_ROOT) == tsuki_path.relative_to(
                TSUKI_SYNC_ROOT
            )
        except ValueError:
            paths_match = False
        if not paths_match:
            raise UsageError(
                f"cross-machine relative paths differ: {mac_path} and {tsuki_path}"
            )
    ignores = raw["ignore"]
    if not isinstance(ignores, list) or any(
        not isinstance(pattern, str) or not pattern for pattern in ignores
    ):
        raise UsageError(f"invalid ignore patterns for {raw['label']}")
    worktree_ignores = raw.get("worktree_ignore", [])
    if not isinstance(worktree_ignores, list) or any(
        not isinstance(pattern, str) or not pattern for pattern in worktree_ignores
    ):
        raise UsageError(f"invalid worktree ignore patterns for {raw['label']}")
    return Folder(
        id=raw["id"],
        label=raw["label"],
        mac=Path(raw["mac"]),
        tsuki=Path(raw["tsuki"]),
        folder_class=cast(FolderClass, raw["class"]),
        git=cast(GitPolicy, raw["git"]),
        ignore=tuple(ignores),
        worktree_ignore=tuple(worktree_ignores),
    )


def load_manifest(path: Path) -> Manifest:
    """Load and validate a private folder manifest."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise UsageError(f"cannot read manifest {path}: {error}") from error
    return parse_manifest(text, f"manifest {path}")


def parse_manifest(text: str, source: str = "manifest") -> Manifest:
    """Validate manifest JSON text."""
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise UsageError(f"cannot read {source}: {error}") from error
    if not isinstance(raw, list):
        raise UsageError("manifest must contain a JSON list")
    folders = tuple(_folder(entry) for entry in raw)
    ids = [folder.id for folder in folders]
    labels = [folder.label for folder in folders]
    for value, name in ((ids, "folder id"), (labels, "folder label")):
        duplicates = sorted(item for item in set(value) if value.count(item) > 1)
        if duplicates:
            raise UsageError(f"duplicate {name}: {duplicates[0]}")
    return Manifest(folders)


def _parse_host(value: str, source: str) -> Host:
    name = value.strip()
    if name not in HOSTS:
        raise UsageError(
            f"invalid host {name!r} in {source}; expected one of "
            + ", ".join(HOST_NAMES)
        )
    return name


def detect_host(
    system_name: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    host_file: Path | None = None,
) -> Host:
    """Return the local host from WORK_SYNC_HOST, the host file, or the OS."""
    env = os.environ if environ is None else environ
    if HOST_ENV in env:
        return _parse_host(env[HOST_ENV], HOST_ENV)
    path = host_file or Path.home() / HOST_FILE
    try:
        return _parse_host(path.read_text(encoding="utf-8"), str(path))
    except FileNotFoundError:
        pass
    except OSError as error:
        raise UsageError(f"cannot read host file {path}: {error}") from error
    current = system_name or platform.system()
    if current == "Darwin":
        return "mac"
    if current == "Linux":
        return "tsuki"
    raise UsageError(f"unsupported host: {current}")

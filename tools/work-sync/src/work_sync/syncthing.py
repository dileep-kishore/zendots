"""Syncthing folder bootstrap behavior."""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .manifest import Folder, Host, UsageError
from .system import Runner

MAC_SYNCTHING = "/Applications/Syncthing.app/Contents/Resources/syncthing/syncthing"
LOCAL_STATE_IGNORES = (
    ".DS_Store",
    "._*",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".pixi",
    ".venv",
    "node_modules",
    ".claude/settings.local.json",
    ".claude/worktrees",
    ".serena/cache",
    ".serena/project.yml",
    ".serena/project.local.yml",
)


@dataclass(frozen=True)
class BootstrapPlan:
    """Validated Syncthing configuration for one folder."""

    folder: Folder
    configs: dict[Host, dict[str, Any]]
    expected: dict[Host, dict[str, Any]]
    repository_managed_ignore: bool


def paths_overlap(left: Path, right: Path) -> bool:
    """Return whether either normalized path contains the other."""
    try:
        common = Path(os.path.commonpath((left, right)))
    except ValueError:
        return False
    return common in {Path(os.path.normpath(left)), Path(os.path.normpath(right))}


def folder_payload(
    template: dict[str, Any],
    folder: Folder,
    mac_id: str,
    tsuki_id: str,
    host: Host,
) -> dict[str, Any]:
    """Build a safe Syncthing folder record."""
    payload = dict(template)
    payload.update(
        {
            "id": folder.id,
            "label": folder.label,
            "path": str(folder.path(host)),
            "type": "sendreceive",
            "paused": True,
            "ignorePerms": False,
            "syncOwnership": False,
            "sendOwnership": False,
            "syncXattrs": False,
            "sendXattrs": False,
            "copyOwnershipFromParent": False,
            "devices": [
                {"deviceID": mac_id, "introducedBy": "", "encryptionPassword": ""},
                {
                    "deviceID": tsuki_id,
                    "introducedBy": "",
                    "encryptionPassword": "",
                },
            ],
        }
    )
    return payload


def managed_patterns(folder: Folder) -> tuple[str, ...]:
    """Return manifest and shared ignore patterns without duplicates."""
    return tuple(dict.fromkeys((*folder.ignore, *LOCAL_STATE_IGNORES)))


class Syncthing:
    """Inspect and configure matching Syncthing folders on both hosts."""

    def __init__(
        self,
        runner: Runner,
        *,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.runner = runner
        self.sleep = sleep
        self.monotonic = monotonic

    @staticmethod
    def _binary(host: Host) -> str:
        return MAC_SYNCTHING if host == "mac" else "syncthing"

    @staticmethod
    def _home(host: Host) -> Path:
        return Path("/Users/dkishore" if host == "mac" else "/home/dileep")

    def st(self, host: Host, *args: str) -> str:
        """Run the Syncthing CLI on one host."""
        return self.runner.run(host, [self._binary(host), "cli", *args])

    def config(self, host: Host) -> dict[str, Any]:
        """Return the complete Syncthing configuration."""
        return json.loads(self.st(host, "config", "dump-json"))

    def _check_directory(self, host: Host, path: Path) -> None:
        try:
            self.runner.run(host, ["test", "-d", str(path)])
        except subprocess.CalledProcessError as error:
            raise UsageError(f"missing {host} directory: {path}") from error

    def _git_preflight(self, folder: Folder) -> None:
        if folder.folder_class != "git":
            return
        heads: list[str] = []
        diffs: list[str] = []
        for host in ("mac", "tsuki"):
            repo = str(folder.path(host))
            heads.append(
                self.runner.run(host, ["git", "-C", repo, "rev-parse", "HEAD"])
            )
            diffs.append(
                self.runner.run(
                    host, ["git", "-C", repo, "diff", "--binary", "HEAD", "--"]
                )
            )
        if heads[0] != heads[1]:
            raise UsageError(
                f"refusing different Git heads: {heads[0][:12]} != {heads[1][:12]}"
            )
        if diffs[0] != diffs[1]:
            raise UsageError(
                "refusing different tracked changes between mac and tsuki"
            )

    def _overlap_preflight(
        self,
        host: Host,
        folder: Folder,
        config: dict[str, Any],
    ) -> None:
        target = folder.path(host)
        for current in config.get("folders", []):
            if current.get("id") == folder.id:
                continue
            path = Path(str(current.get("path", "")))
            if paths_overlap(target, path):
                raise UsageError(
                    f"refusing overlapping {host} folders: {target} and {path}"
                )

    @staticmethod
    def _validate_existing(
        current: dict[str, Any],
        expected: dict[str, Any],
    ) -> None:
        keys = (
            "id",
            "label",
            "path",
            "type",
            "ignorePerms",
            "syncOwnership",
            "sendOwnership",
            "syncXattrs",
            "sendXattrs",
            "copyOwnershipFromParent",
        )
        if any(current.get(key) != expected.get(key) for key in keys):
            raise UsageError(
                f"existing folder differs from manifest: {current.get('id')}"
            )
        actual_devices = {
            item.get("deviceID") for item in current.get("devices", [])
        }
        expected_devices = {
            item.get("deviceID") for item in expected.get("devices", [])
        }
        if actual_devices != expected_devices:
            raise UsageError(
                f"existing folder has different devices: {current.get('id')}"
            )

    def _read_text(self, host: Host, path: Path) -> str:
        try:
            return self.runner.run(host, ["cat", str(path)])
        except subprocess.CalledProcessError:
            return ""

    def _write_text(self, host: Host, path: Path, text: str, mode: str) -> None:
        self.runner.run(host, ["mkdir", "-p", str(path.parent)])
        self.runner.run(host, ["tee", str(path)], input_text=text)
        self.runner.run(host, ["chmod", mode, str(path)])

    def _tracked_stignore(self, host: Host, repo: Path) -> bool:
        try:
            self.runner.run(
                host,
                [
                    "git",
                    "-C",
                    str(repo),
                    "ls-files",
                    "--error-unmatch",
                    ".stignore",
                ],
            )
        except subprocess.CalledProcessError:
            return False
        return True

    def _stignore_preflight(self, folder: Folder) -> bool:
        if folder.folder_class != "git":
            return False
        states = {
            host: self._tracked_stignore(host, folder.path(host))
            for host in ("mac", "tsuki")
        }
        if len(set(states.values())) != 1:
            raise UsageError("refusing inconsistent tracked .stignore state")
        if not states["mac"]:
            return False
        required = set(folder.ignore)
        for host in ("mac", "tsuki"):
            current = self._read_text(host, folder.path(host) / ".stignore")
            missing = required - set(current.splitlines())
            if missing:
                raise UsageError(
                    f"tracked .stignore in {host} is missing manifest patterns: "
                    + ", ".join(sorted(missing))
                )
        return True

    def _add_local_git_exclude(self, host: Host, repo: Path) -> None:
        raw_path = self.runner.run(
            host,
            ["git", "-C", str(repo), "rev-parse", "--git-path", "info/exclude"],
        )
        exclude_path = Path(raw_path)
        if not exclude_path.is_absolute():
            exclude_path = repo / exclude_path
        current = self._read_text(host, exclude_path)
        if ".stignore" in current.splitlines():
            return
        updated = current.rstrip() + "\n.stignore\n"
        self._write_text(host, exclude_path, updated.lstrip("\n"), "0644")

    def _install_ignores(
        self,
        folder: Folder,
        repository_managed: bool,
    ) -> None:
        if repository_managed:
            return
        patterns = managed_patterns(folder)
        for host in ("mac", "tsuki"):
            ignore_path = folder.path(host) / ".stignore"
            current = self._read_text(host, ignore_path)
            lines = current.splitlines()
            lines.extend(pattern for pattern in patterns if pattern not in lines)
            updated = "\n".join(lines).rstrip() + "\n"
            if updated != current:
                self._write_text(host, ignore_path, updated, "0644")
            if folder.folder_class == "git":
                self._add_local_git_exclude(host, folder.path(host))

    def _backup_configs(self) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        for host in ("mac", "tsuki"):
            path = (
                self._home(host)
                / ".local/state/work-sync/backups"
                / f"{stamp}-{host}.json"
            )
            self._write_text(
                host,
                path,
                self.st(host, "config", "dump-json") + "\n",
                "0600",
            )

    def _add_or_pause(
        self,
        host: Host,
        config: dict[str, Any],
        expected: dict[str, Any],
    ) -> None:
        current = next(
            (
                item
                for item in config.get("folders", [])
                if item.get("id") == expected["id"]
            ),
            None,
        )
        if current is None:
            payload = json.dumps(expected, separators=(",", ":"))
            self.st(host, "config", "folders", "add-json", payload)
        else:
            self._validate_existing(current, expected)
        self.st(
            host,
            "config",
            "folders",
            str(expected["id"]),
            "paused",
            "set",
            "true",
        )

    def plan(self, folder: Folder) -> BootstrapPlan:
        """Validate a folder and return its expected Syncthing state."""
        for host in ("mac", "tsuki"):
            self._check_directory(host, folder.path(host))
        self._git_preflight(folder)
        repository_managed = self._stignore_preflight(folder)
        configs: dict[Host, dict[str, Any]] = {
            host: self.config(host) for host in ("mac", "tsuki")
        }
        for host in ("mac", "tsuki"):
            self._overlap_preflight(host, folder, configs[host])
        mac_id = self.runner.run("mac", [MAC_SYNCTHING, "device-id"])
        tsuki_id = self.runner.run("tsuki", ["syncthing", "device-id"])
        expected: dict[Host, dict[str, Any]] = {
            host: folder_payload(
                json.loads(
                    self.st(host, "config", "defaults", "folder", "dump-json")
                ),
                folder,
                mac_id,
                tsuki_id,
                host,
            )
            for host in ("mac", "tsuki")
        }
        for host in ("mac", "tsuki"):
            current = next(
                (
                    item
                    for item in configs[host].get("folders", [])
                    if item.get("id") == folder.id
                ),
                None,
            )
            if current is not None:
                self._validate_existing(current, expected[host])
        return BootstrapPlan(folder, configs, expected, repository_managed)

    def bootstrap(
        self,
        folder: Folder,
        *,
        apply: bool,
        timeout: int,
    ) -> BootstrapPlan:
        """Validate and optionally install one folder on both hosts."""
        plan = self.plan(folder)
        if not apply:
            return plan
        self._backup_configs()
        for host in ("mac", "tsuki"):
            self._add_or_pause(host, plan.configs[host], plan.expected[host])
        self._install_ignores(folder, plan.repository_managed_ignore)
        for host in ("mac", "tsuki"):
            self.st(
                host,
                "config",
                "folders",
                folder.id,
                "paused",
                "set",
                "false",
            )
        self.wait_idle(folder.id, timeout)
        return plan

    def status(self, host: Host, folder_id: str) -> dict[str, Any]:
        """Read one folder status through Syncthing's local REST endpoint."""
        key = self.st(host, "config", "gui", "apikey", "get")
        address = self.st(host, "config", "gui", "raw-address", "get")
        header = f"X-API-Key: {key}\n"
        output = self.runner.run(
            host,
            [
                "curl",
                "-fsS",
                "-H",
                "@-",
                f"http://{address}/rest/db/status?folder={folder_id}",
            ],
            input_text=header,
        )
        return json.loads(output)

    def wait_idle(self, folder_id: str, timeout: int) -> dict[Host, dict[str, Any]]:
        """Wait until both hosts report an idle and complete folder."""
        deadline = self.monotonic() + timeout
        while True:
            statuses: dict[Host, dict[str, Any]] = {
                host: self.status(host, folder_id) for host in ("mac", "tsuki")
            }
            if all(
                status.get("state") == "idle"
                and sum(
                    int(status.get(key, 0))
                    for key in (
                        "needFiles",
                        "needDirectories",
                        "needDeletes",
                        "needBytes",
                    )
                )
                == 0
                and not status.get("errors")
                and not status.get("invalid")
                for status in statuses.values()
            ):
                return statuses
            if self.monotonic() >= deadline:
                raise UsageError(
                    f"timed out waiting for {folder_id}; "
                    "folder remains configured for inspection"
                )
            self.sleep(2)

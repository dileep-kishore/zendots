"""Syncthing folder bootstrap behavior."""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from itertools import permutations
from pathlib import Path
from typing import Any, Literal

from .manifest import HOST_NAMES, HOSTS, Folder, Host, UsageError, alias
from .system import Runner

MAC_SYNCTHING = "/Applications/Syncthing.app/Contents/Resources/syncthing/syncthing"
# (?d) lets Syncthing delete this leftover state when the containing directory
# is removed on the other host; without it the pull fails on that directory.
LOCAL_STATE_IGNORES = (
    "(?d).DS_Store",
    "(?d)._*",
    "(?d)__pycache__",
    "(?d).pytest_cache",
    "(?d).ruff_cache",
    "(?d).uv-cache",
    "(?d).pixi",
    "(?d).venv",
    "(?d)node_modules",
    "(?d).claude/settings.local.json",
    "(?d).claude/worktrees",
    "(?d).serena/cache",
    "(?d).serena/project.yml",
    "(?d).serena/project.local.yml",
)
MACHINE_LOCAL_GIT_KEYS = (
    "core.filemode",
    "core.ignorecase",
    "core.precomposeunicode",
    "core.symlinks",
)
# Synchronized macOS checkouts need these in config.worktree, which never
# syncs; Git otherwise assumes a case-sensitive volume.
FILESYSTEM_GIT_KEYS = ("core.ignorecase", "core.precomposeunicode")
GIT_PROBE_PREFIX = ".work-sync-git-probe."
FOLDER_KEYS = (
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
StepStatus = Literal["change", "ok", "skip"]


@dataclass(frozen=True)
class BootstrapPlan:
    """Validated Syncthing configuration for one folder."""

    folder: Folder
    configs: dict[Host, dict[str, Any]]
    expected: dict[Host, dict[str, Any]]
    repository_managed_ignore: bool
    device_ids: dict[Host, str] = field(default_factory=dict)
    skipped: tuple[Host, ...] = ()

    @property
    def hosts(self) -> tuple[Host, ...]:
        """Return the reachable hosts this plan configures."""
        return tuple(self.expected)


@dataclass(frozen=True)
class DeviceStep:
    """One add-device check and the change it makes, if any."""

    host: Host
    subject: str
    description: str
    status: StepStatus
    apply: Callable[[], object] | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class DevicePlan:
    """Ordered catch-up steps for one host."""

    target: Host
    hosts: tuple[Host, ...]
    skipped: tuple[Host, ...]
    steps: tuple[DeviceStep, ...]

    @property
    def changes(self) -> tuple[DeviceStep, ...]:
        """Return the steps that change Syncthing or files."""
        return tuple(step for step in self.steps if step.status == "change")


@dataclass(frozen=True)
class FolderState:
    """One folder's Syncthing state on one host."""

    state: str
    completion: int | None = None
    error: str | None = None


@dataclass(frozen=True)
class StatusReport:
    """Folder states for every manifest folder on every host."""

    reachable: tuple[Host, ...]
    unreachable: tuple[Host, ...]
    states: dict[str, dict[Host, FolderState]]

    @property
    def failed(self) -> bool:
        """Return whether any reachable host could not be read."""
        return any(
            state.error is not None
            for by_host in self.states.values()
            for state in by_host.values()
        )


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
    device_ids: Sequence[str],
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
                {"deviceID": device_id, "introducedBy": "", "encryptionPassword": ""}
                for device_id in device_ids
            ],
        }
    )
    return payload


def find_folder(config: Mapping[str, Any], folder_id: str) -> dict[str, Any] | None:
    """Return a folder record from a Syncthing configuration."""
    return next(
        (item for item in config.get("folders", []) if item.get("id") == folder_id),
        None,
    )


def _folder_devices(record: Mapping[str, Any]) -> set[str]:
    return {str(item.get("deviceID")) for item in record.get("devices", [])}


def _known_devices(config: Mapping[str, Any]) -> set[str]:
    return {str(item.get("deviceID")) for item in config.get("devices", [])}


def managed_patterns(folder: Folder) -> tuple[str, ...]:
    """Return manifest and shared ignore patterns without duplicates."""
    git_state = (
        (".git/worktrees", ".git/config.worktree", ".git/**.lock", ".git/FETCH_HEAD")
        if folder.git != "none"
        else ()
    )
    return tuple(dict.fromkeys((*folder.ignore, *git_state, *LOCAL_STATE_IGNORES)))


def reconcile_ignore_text(current: str, folder: Folder) -> str:
    """Replace superseded managed rules while preserving local rules."""
    patterns = managed_patterns(folder)
    # An unprefixed copy earlier in the file would win over its (?d) form.
    superseded = {".git", "/.git"} | {
        pattern.removeprefix("(?d)")
        for pattern in patterns
        if pattern.startswith("(?d)")
    }
    lines = [line for line in current.splitlines() if line not in superseded]
    lines.extend(pattern for pattern in patterns if pattern not in lines)
    return "\n".join(lines).rstrip() + "\n"


def statuses_converged(
    statuses: Mapping[Host, Mapping[str, Any]],
    ids: Mapping[Host, str],
) -> bool:
    """Return whether every listed device is idle, complete, and current."""
    if not all(
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
        return False
    for host, other in permutations(statuses, 2):
        seen = statuses[host].get("remoteSequence", {}).get(ids[other])
        if seen is None or int(seen) != int(statuses[other].get("sequence", -1)):
            return False
    return True


def completion(status: Mapping[str, Any]) -> int:
    """Return the whole-number percentage of global bytes held locally."""
    total = int(status.get("globalBytes", 0))
    need = int(status.get("needBytes", 0))
    if total <= 0:
        return 100
    return max(0, min(100, (total - need) * 100 // total))


def _error_text(error: Exception) -> str:
    if isinstance(error, subprocess.CalledProcessError):
        return (error.stderr or error.stdout or str(error)).strip()
    return str(error)


class Syncthing:
    """Inspect and configure matching Syncthing folders on reachable hosts."""

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
        self._gui: dict[Host, tuple[str, str]] = {}

    @staticmethod
    def _binary(host: Host) -> str:
        return MAC_SYNCTHING if HOSTS[host].platform == "darwin" else "syncthing"

    @staticmethod
    def _home(host: Host) -> Path:
        return HOSTS[host].home

    def st(self, host: Host, *args: str) -> str:
        """Run the Syncthing CLI on one host."""
        return self.runner.run(host, [self._binary(host), "cli", *args])

    def config(self, host: Host) -> dict[str, Any]:
        """Return the complete Syncthing configuration."""
        return json.loads(self.st(host, "config", "dump-json"))

    def reachable_hosts(self) -> tuple[tuple[Host, ...], tuple[Host, ...]]:
        """Return reachable and skipped hosts; at least one peer must answer."""
        hosts, skipped = self.runner.split_reachable(HOST_NAMES)
        if len(hosts) < 2:
            raise UsageError(
                "no other machine is reachable over SSH: "
                + ", ".join(self.runner.describe(host) for host in skipped)
            )
        return hosts, skipped

    def device_ids(self, hosts: Iterable[Host]) -> dict[Host, str]:
        """Read each host's own Syncthing device ID."""
        ids = {
            host: self.runner.run(host, [self._binary(host), "device-id"])
            for host in hosts
        }
        if len(set(ids.values())) != len(ids):
            raise UsageError(
                "two hosts report the same Syncthing device ID; set "
                "WORK_SYNC_HOST or ~/.config/work-sync/host on this machine"
            )
        return ids

    @staticmethod
    def _require_paired(
        configs: Mapping[Host, Mapping[str, Any]],
        ids: Mapping[Host, str],
    ) -> None:
        for host, config in configs.items():
            known = _known_devices(config)
            for other, device_id in ids.items():
                if other != host and device_id not in known:
                    raise UsageError(
                        f"{alias(host)} does not know the {alias(other)} device; "
                        f"run work-sync add-device {alias(other)}"
                    )

    def _check_directory(self, host: Host, path: Path) -> None:
        try:
            self.runner.run(host, ["test", "-d", str(path)])
        except subprocess.CalledProcessError as error:
            raise UsageError(f"missing {host} directory: {path}") from error

    def _exists(self, host: Host, path: Path) -> bool:
        try:
            self.runner.run(host, ["test", "-e", str(path)])
        except subprocess.CalledProcessError as error:
            # Only test's own false result means absent; ssh failures exit 255.
            if error.returncode != 1:
                raise
            return False
        return True

    def _target_state(
        self,
        host: Host,
        path: Path,
        *,
        allow_stignore: bool = False,
    ) -> str:
        """Return whether a prospective target is missing, empty, or nonempty."""
        if not self._exists(host, path):
            return "missing"
        try:
            self.runner.run(host, ["test", "-d", str(path)])
        except subprocess.CalledProcessError as error:
            raise UsageError(f"destination is not a directory: {path}") from error
        skip = ["!", "-name", ".stignore"] if allow_stignore else []
        output = self.runner.run(
            host,
            [
                "find",
                str(path),
                "-mindepth",
                "1",
                "-maxdepth",
                "1",
                *skip,
                "-print",
                "-quit",
            ],
        )
        return "nonempty" if output else "empty"

    def _git_preflight(self, folder: Folder, hosts: Sequence[Host]) -> None:
        if folder.folder_class != "git":
            return
        heads: dict[Host, str] = {}
        diffs: dict[Host, str] = {}
        for host in hosts:
            repo = str(folder.path(host))
            heads[host] = self.runner.run(
                host, ["git", "-C", repo, "rev-parse", "HEAD"]
            )
            diffs[host] = self.runner.run(
                host, ["git", "-C", repo, "diff", "--binary", "HEAD", "--"]
            )
        first = hosts[0]
        for host in hosts[1:]:
            if heads[host] != heads[first]:
                raise UsageError(
                    "refusing different Git heads: "
                    f"{heads[first][:12]} != {heads[host][:12]}"
                )
            if diffs[host] != diffs[first]:
                raise UsageError(
                    f"refusing different tracked changes between {first} and {host}"
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
    def _validate_fields(
        current: Mapping[str, Any], expected: Mapping[str, Any]
    ) -> None:
        if any(current.get(key) != expected.get(key) for key in FOLDER_KEYS):
            raise UsageError(
                f"existing folder differs from manifest: {current.get('id')}"
            )

    @classmethod
    def _validate_existing(
        cls,
        host: Host,
        current: dict[str, Any],
        expected: dict[str, Any],
        ids: Mapping[Host, str],
        unreachable: int = 0,
    ) -> None:
        cls._validate_fields(current, expected)
        actual = _folder_devices(current)
        wanted = _folder_devices(expected)
        missing = [other for other, device in ids.items() if device in wanted - actual]
        if missing:
            raise UsageError(
                f"existing {alias(host)} folder {current.get('id')} does not list "
                + ", ".join(alias(other) for other in missing)
                + "; run "
                + " and ".join(f"work-sync add-device {alias(o)}" for o in missing)
            )
        # Devices of skipped hosts cannot be read, so allow that many extras.
        if len(actual - wanted) > unreachable:
            raise UsageError(
                f"existing folder has different devices: {current.get('id')}"
            )

    def _read_text(self, host: Host, path: Path) -> str:
        if not self._exists(host, path):
            return ""
        return self.runner.run(host, ["cat", str(path)])

    def _managed_text(self, host: Host, folder: Folder) -> str:
        """Return a tracked .stignore with the newline the runner strips."""
        text = self._read_text(host, folder.path(host) / ".stignore")
        return text + "\n" if text else ""

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
        except subprocess.CalledProcessError as error:
            # --error-unmatch exits 1 for an untracked path.
            if error.returncode != 1:
                raise
            return False
        return True

    def _stignore_preflight(self, folder: Folder, hosts: Sequence[Host]) -> bool:
        if folder.folder_class != "git":
            return False
        states = {
            host: self._tracked_stignore(host, folder.path(host)) for host in hosts
        }
        if len(set(states.values())) != 1:
            raise UsageError("refusing inconsistent tracked .stignore state")
        if not states[hosts[0]]:
            return False
        required = set(folder.ignore)
        for host in hosts:
            current = self._read_text(host, folder.path(host) / ".stignore")
            missing = required - set(current.splitlines())
            if missing:
                raise UsageError(
                    f"tracked .stignore in {host} is missing manifest patterns: "
                    + ", ".join(sorted(missing))
                )
        return True

    def _stignore_preflight_new(self, folder: Folder, source: Host) -> bool:
        if folder.folder_class != "git" or not self._tracked_stignore(
            source, folder.path(source)
        ):
            return False
        required = set(folder.ignore) | {
            ".git/worktrees",
            ".git/config.worktree",
            ".git/**.lock",
        }
        current = self._read_text(source, folder.path(source) / ".stignore")
        missing = required - set(current.splitlines())
        if missing:
            raise UsageError(
                "tracked .stignore is missing required Git patterns: "
                + ", ".join(sorted(missing))
            )
        return True

    def _exclude_path(self, host: Host, repo: Path) -> Path:
        raw_path = self.runner.run(
            host,
            ["git", "-C", str(repo), "rev-parse", "--git-path", "info/exclude"],
        )
        exclude_path = Path(raw_path)
        return exclude_path if exclude_path.is_absolute() else repo / exclude_path

    def _add_local_git_exclude(self, host: Host, repo: Path) -> None:
        exclude_path = self._exclude_path(host, repo)
        current = self._read_text(host, exclude_path)
        lines = current.splitlines()
        missing = [name for name in (".stignore", ".stfolder") if name not in lines]
        if not missing:
            return
        updated = current.rstrip() + "\n" + "\n".join(missing) + "\n"
        self._write_text(host, exclude_path, updated.lstrip("\n"), "0644")

    def _is_repository(self, host: Host, repo: Path) -> bool:
        """Report whether Git accepts the checkout; a .git still syncing does not."""
        try:
            self.runner.run(host, ["git", "-C", str(repo), "rev-parse", "--git-dir"])
        except subprocess.CalledProcessError as error:
            # 128 is git's "not a git repository"; ssh failures exit 255.
            if error.returncode != 128:
                raise
            return False
        return True

    def _git_config(self, host: Host, repo: Path, scope: str, key: str) -> str | None:
        """Read one Git config value; only exit 1 means the key is unset."""
        try:
            return self.runner.run(
                host,
                ["git", "-C", str(repo), "config", f"--{scope}", "--get", key],
            )
        except subprocess.CalledProcessError as error:
            if error.returncode != 1:
                raise
            return None

    def _local_git_config(self, host: Host, repo: Path, key: str) -> str | None:
        return self._git_config(host, repo, "local", key)

    def _migrate_git_config(self, host: Host, repo: Path) -> None:
        values: dict[str, str] = {}
        for key in MACHINE_LOCAL_GIT_KEYS:
            value = self._local_git_config(host, repo, key)
            if value is not None:
                values[key] = value
        self.runner.run(
            host,
            [
                "git",
                "-C",
                str(repo),
                "config",
                "--local",
                "extensions.worktreeConfig",
                "true",
            ],
        )
        for key, value in values.items():
            self.runner.run(
                host,
                ["git", "-C", str(repo), "config", "--local", "--unset-all", key],
            )
            self.runner.run(
                host,
                ["git", "-C", str(repo), "config", "--worktree", key, value],
            )

    def _folder_repositories(self, host: Host, folder: Folder) -> tuple[Path, ...]:
        if folder.folder_class == "git":
            return (folder.path(host),)
        output = self.runner.run(
            host,
            [
                "find",
                str(folder.path(host)),
                "-type",
                "d",
                "-name",
                ".git",
                "-prune",
                "-print",
            ],
        )
        return tuple(Path(line).parent for line in output.splitlines())

    def _git_state_current(
        self,
        host: Host,
        folder: Folder,
        repos: tuple[Path, ...],
        repository_managed: bool,
    ) -> bool:
        for repo in repos:
            if self._local_git_config(host, repo, "extensions.worktreeConfig") != (
                "true"
            ):
                return False
            if any(
                self._local_git_config(host, repo, key) is not None
                for key in MACHINE_LOCAL_GIT_KEYS
            ):
                return False
            if self._missing_filesystem_keys(host, repo):
                return False
        if folder.folder_class == "git" and not repository_managed:
            exclude = self._exclude_path(host, folder.path(host))
            lines = self._read_text(host, exclude).splitlines()
            return ".stignore" in lines and ".stfolder" in lines
        return True

    def _install_ignore_file(
        self,
        host: Host,
        folder: Folder,
        repository_managed: bool,
        managed_text: str | None = None,
    ) -> None:
        ignore_path = folder.path(host) / ".stignore"
        if repository_managed:
            if managed_text is not None:
                self._write_text(host, ignore_path, managed_text, "0644")
            return
        current = self._read_text(host, ignore_path)
        updated = reconcile_ignore_text(current, folder)
        if updated != current:
            self._write_text(host, ignore_path, updated, "0644")

    def _missing_filesystem_keys(self, host: Host, repo: Path) -> tuple[str, ...]:
        """Return filesystem Git keys a macOS checkout lacks in config.worktree."""
        if HOSTS[host].platform != "darwin":
            return ()
        return tuple(
            key
            for key in FILESYSTEM_GIT_KEYS
            if self._git_config(host, repo, "worktree", key) is None
        )

    def _probe_filesystem_keys(self, host: Host, folder: Folder) -> dict[str, str]:
        """Read the values git init chooses on the folder's volume."""
        parent = folder.path(host).parent
        probe = Path(
            self.runner.run(
                host, ["mktemp", "-d", str(parent / f"{GIT_PROBE_PREFIX}XXXXXX")]
            )
        )
        # Never rm -rf a path mktemp did not just create under the parent.
        if probe.parent != parent or not probe.name.startswith(GIT_PROBE_PREFIX):
            raise UsageError(f"unexpected mktemp result on {host}: {probe}")
        try:
            self.runner.run(host, ["git", "init", "-q", str(probe)])
            values: dict[str, str] = {}
            for key in FILESYSTEM_GIT_KEYS:
                value = self._local_git_config(host, probe, key)
                # Git writes these keys only when the filesystem needs them.
                values[key] = "false" if value is None else value
            return values
        finally:
            self.runner.run(host, ["rm", "-rf", str(probe)])

    def _install_filesystem_keys(self, host: Host, folder: Folder, repo: Path) -> None:
        missing = self._missing_filesystem_keys(host, repo)
        if not missing:
            return
        values = self._probe_filesystem_keys(host, folder)
        for key in missing:
            self.runner.run(
                host,
                ["git", "-C", str(repo), "config", "--worktree", key, values[key]],
            )

    def _install_git_state(
        self,
        host: Host,
        folder: Folder,
        repository_managed: bool,
        *,
        filesystem: bool = False,
    ) -> None:
        for repo in self._folder_repositories(host, folder):
            self._migrate_git_config(host, repo)
            if filesystem:
                self._install_filesystem_keys(host, folder, repo)
        if folder.folder_class == "git" and not repository_managed:
            self._add_local_git_exclude(host, folder.path(host))

    def _install_ignores(
        self,
        folder: Folder,
        repository_managed: bool,
        hosts: Sequence[Host],
    ) -> None:
        for host in hosts:
            self._install_ignore_file(host, folder, repository_managed)
            self._install_git_state(host, folder, repository_managed)

    def _backup_configs(self, hosts: Sequence[Host]) -> None:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        for host in hosts:
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

    def _resume(self, host: Host, folder_id: str) -> None:
        self.st(host, "config", "folders", folder_id, "paused", "set", "false")
        self.scan(host, folder_id)

    def _add_or_pause(self, host: Host, plan: BootstrapPlan) -> None:
        expected = plan.expected[host]
        current = find_folder(plan.configs[host], str(expected["id"]))
        if current is None:
            payload = json.dumps(expected, separators=(",", ":"))
            self.st(host, "config", "folders", "add-json", payload)
        else:
            self._validate_existing(
                host, current, expected, plan.device_ids, len(plan.skipped)
            )
        self.st(
            host,
            "config",
            "folders",
            str(expected["id"]),
            "paused",
            "set",
            "true",
        )

    def _expected(
        self,
        folder: Folder,
        hosts: Sequence[Host],
        ids: Mapping[Host, str],
    ) -> dict[Host, dict[str, Any]]:
        device_list = [ids[host] for host in hosts]
        return {
            host: folder_payload(
                json.loads(self.st(host, "config", "defaults", "folder", "dump-json")),
                folder,
                device_list,
                host,
            )
            for host in hosts
        }

    def _finish_plan(
        self,
        folder: Folder,
        hosts: tuple[Host, ...],
        skipped: tuple[Host, ...],
        configs: dict[Host, dict[str, Any]],
        repository_managed: bool,
    ) -> BootstrapPlan:
        for host in hosts:
            self._overlap_preflight(host, folder, configs[host])
        ids = self.device_ids(hosts)
        self._require_paired(configs, ids)
        expected = self._expected(folder, hosts, ids)
        for host in hosts:
            current = find_folder(configs[host], folder.id)
            if current is not None:
                self._validate_existing(
                    host, current, expected[host], ids, len(skipped)
                )
        return BootstrapPlan(
            folder, configs, expected, repository_managed, ids, skipped
        )

    def plan(self, folder: Folder) -> BootstrapPlan:
        """Validate a folder on reachable hosts and return its expected state."""
        hosts, skipped = self.reachable_hosts()
        for host in hosts:
            self._check_directory(host, folder.path(host))
        self._git_preflight(folder, hosts)
        repository_managed = self._stignore_preflight(folder, hosts)
        configs = {host: self.config(host) for host in hosts}
        return self._finish_plan(folder, hosts, skipped, configs, repository_managed)

    def plan_new(self, folder: Folder, source: Host) -> BootstrapPlan:
        """Validate a one-sided folder before its first synchronization."""
        hosts, skipped = self.reachable_hosts()
        self._check_directory(source, folder.path(source))
        configs = {host: self.config(host) for host in hosts}
        for target in hosts:
            if target == source:
                continue
            path = folder.path(target)
            if (
                self._target_state(target, path) == "nonempty"
                and find_folder(configs[target], folder.id) is None
            ):
                raise UsageError(f"refusing nonempty destination: {path}")
        repository_managed = self._stignore_preflight_new(folder, source)
        return self._finish_plan(folder, hosts, skipped, configs, repository_managed)

    def apply_new(
        self,
        plan: BootstrapPlan,
        source: Host,
        *,
        timeout: int,
    ) -> None:
        """Install and synchronize a folder that exists on only one host."""
        folder = plan.folder
        managed = plan.repository_managed_ignore
        targets = tuple(host for host in plan.hosts if host != source)
        self._backup_configs(plan.hosts)
        for target in targets:
            self.runner.run(target, ["mkdir", "-p", str(folder.path(target))])
        managed_text = self._managed_text(source, folder) if managed else None
        self._install_ignore_file(source, folder, managed)
        for target in targets:
            self._install_ignore_file(target, folder, managed, managed_text)
        self._install_git_state(source, folder, managed)
        for host in plan.hosts:
            self._add_or_pause(host, plan)
            self._resume(host, folder.id)
        self.wait_idle(folder.id, timeout, plan.device_ids)
        for target in targets:
            self._install_git_state(target, folder, managed, filesystem=True)
        for host in plan.hosts:
            self.scan(host, folder.id)
        self.wait_idle(folder.id, timeout, plan.device_ids)

    def bootstrap(
        self,
        folder: Folder,
        *,
        apply: bool,
        timeout: int,
    ) -> BootstrapPlan:
        """Validate and optionally install one folder on reachable hosts."""
        plan = self.plan(folder)
        if not apply:
            return plan
        self._backup_configs(plan.hosts)
        for host in plan.hosts:
            self._add_or_pause(host, plan)
        self._install_ignores(folder, plan.repository_managed_ignore, plan.hosts)
        for host in plan.hosts:
            self._resume(host, folder.id)
        self.wait_idle(folder.id, timeout, plan.device_ids)
        return plan

    def _add_device(self, host: Host, device_id: str, name: str) -> None:
        payload = json.loads(self.st(host, "config", "defaults", "device", "dump-json"))
        payload.update({"deviceID": device_id, "name": name})
        self.st(
            host,
            "config",
            "devices",
            "add-json",
            json.dumps(payload, separators=(",", ":")),
        )

    def _add_folder(self, host: Host, payload: dict[str, Any]) -> None:
        self.st(
            host,
            "config",
            "folders",
            "add-json",
            json.dumps(payload, separators=(",", ":")),
        )
        self._resume(host, str(payload["id"]))

    def _pairing_steps(
        self,
        hosts: Sequence[Host],
        ids: Mapping[Host, str],
        configs: Mapping[Host, Mapping[str, Any]],
    ) -> list[DeviceStep]:
        steps: list[DeviceStep] = []
        for host in hosts:
            known = _known_devices(configs[host])
            for other in hosts:
                if other == host:
                    continue
                description = f"knows device {alias(other)}"
                if ids[other] in known:
                    steps.append(DeviceStep(host, "devices", description, "ok"))
                    continue
                steps.append(
                    DeviceStep(
                        host,
                        "devices",
                        description,
                        "change",
                        partial(self._add_device, host, ids[other], alias(other)),
                    )
                )
        return steps

    def _share_step(
        self,
        host: Host,
        folder: Folder,
        record: Mapping[str, Any],
        other: Host,
        device_id: str,
    ) -> DeviceStep:
        description = f"folder lists {alias(other)}"
        if device_id in _folder_devices(record):
            return DeviceStep(host, folder.label, description, "ok")
        return DeviceStep(
            host,
            folder.label,
            description,
            "change",
            partial(
                self.st,
                host,
                "config",
                "folders",
                folder.id,
                "devices",
                "add",
                "--device-id",
                device_id,
            ),
        )

    def _ignore_step(
        self,
        target: Host,
        folder: Folder,
        peer: Host,
        *,
        exists: bool,
        fresh: bool,
    ) -> DeviceStep:
        ignore_path = folder.path(target) / ".stignore"
        current = self._read_text(target, ignore_path) if exists else ""
        tracked = folder.folder_class == "git" and self._tracked_stignore(
            peer, folder.path(peer)
        )
        if tracked and not fresh:
            missing = set(folder.ignore) - set(current.splitlines())
            if missing:
                raise UsageError(
                    f"tracked .stignore on {alias(target)} is missing manifest "
                    "patterns: "
                    + ", ".join(sorted(missing))
                    + "; add them to the repository's .stignore"
                )
            return DeviceStep(
                target, folder.label, "repository .stignore has manifest patterns", "ok"
            )
        if tracked:
            wanted = self._managed_text(peer, folder)
            description = f"repository .stignore copied from {alias(peer)}"
        else:
            wanted = reconcile_ignore_text(current, folder)
            description = "managed .stignore"
        # The runner strips output, so a read-back file lacks its final newline.
        if wanted.strip() == current.strip():
            return DeviceStep(target, folder.label, description, "ok")
        return DeviceStep(
            target,
            folder.label,
            description,
            "change",
            partial(self._write_text, target, ignore_path, wanted, "0644"),
        )

    def _git_step(
        self,
        target: Host,
        folder: Folder,
        peer: Host,
    ) -> DeviceStep:
        if folder.folder_class == "plain":
            return DeviceStep(target, folder.label, "no Git state", "ok")
        description = "machine-local Git state"
        path = folder.path(target)
        if folder.folder_class == "git":
            repos = (path,) if self._exists(target, path / ".git") else ()
        else:
            repos = (
                self._folder_repositories(target, folder)
                if self._exists(target, path)
                else ()
            )
        if not repos or not all(self._is_repository(target, repo) for repo in repos):
            return DeviceStep(
                target,
                folder.label,
                description + " waits for synchronization; rerun add-device",
                "skip",
            )
        managed = folder.folder_class == "git" and self._tracked_stignore(
            peer, folder.path(peer)
        )
        if self._git_state_current(target, folder, repos, managed):
            return DeviceStep(target, folder.label, description, "ok")
        return DeviceStep(
            target,
            folder.label,
            description,
            "change",
            partial(self._install_git_state, target, folder, managed, filesystem=True),
        )

    def _folder_steps(
        self,
        folder: Folder,
        target: Host,
        hosts: Sequence[Host],
        ids: Mapping[Host, str],
        configs: dict[Host, dict[str, Any]],
        blocked: list[str],
    ) -> list[DeviceStep]:
        records = {host: find_folder(configs[host], folder.id) for host in hosts}
        peers = tuple(
            host for host in hosts if host != target and records[host] is not None
        )
        if not peers:
            return [
                DeviceStep(
                    target,
                    folder.label,
                    "not configured on a reachable peer; run work-sync bootstrap",
                    "skip",
                )
            ]
        steps: list[DeviceStep] = []
        for peer in peers:
            record = records[peer]
            assert record is not None
            self._validate_fields(record, folder_payload({}, folder, (), peer))
            steps.append(self._share_step(peer, folder, record, target, ids[target]))
        record = records[target]
        path = folder.path(target)
        if record is not None:
            self._validate_fields(record, folder_payload({}, folder, (), target))
            steps.extend(
                self._share_step(target, folder, record, peer, ids[peer])
                for peer in peers
            )
            steps.append(
                self._ignore_step(target, folder, peers[0], exists=True, fresh=False)
            )
            if record.get("paused"):
                steps.append(
                    DeviceStep(
                        target,
                        folder.label,
                        "folder is running",
                        "change",
                        partial(self._resume, target, folder.id),
                    )
                )
            else:
                steps.append(
                    DeviceStep(target, folder.label, "folder is running", "ok")
                )
            steps.append(self._git_step(target, folder, peers[0]))
            return steps
        self._overlap_preflight(target, folder, configs[target])
        # A lone .stignore is what an interrupted earlier run leaves behind.
        state = self._target_state(target, path, allow_stignore=True)
        if state == "nonempty":
            blocked.append(str(path))
            return steps
        if state == "missing":
            steps.append(
                DeviceStep(
                    target,
                    folder.label,
                    f"directory {path}",
                    "change",
                    partial(self.runner.run, target, ["mkdir", "-p", str(path)]),
                )
            )
        else:
            steps.append(DeviceStep(target, folder.label, f"directory {path}", "ok"))
        steps.append(
            self._ignore_step(
                target, folder, peers[0], exists=state != "missing", fresh=True
            )
        )
        members = [host for host in hosts if host == target or host in peers]
        payload = folder_payload(
            json.loads(self.st(target, "config", "defaults", "folder", "dump-json")),
            folder,
            [ids[host] for host in members],
            target,
        )
        steps.append(
            DeviceStep(
                target,
                folder.label,
                "add folder shared with "
                + ", ".join(alias(host) for host in members if host != target),
                "change",
                partial(self._add_folder, target, payload),
            )
        )
        steps.append(
            DeviceStep(
                target,
                folder.label,
                "machine-local Git state waits for synchronization; rerun add-device",
                "skip",
            )
            if folder.folder_class != "plain"
            else DeviceStep(target, folder.label, "no Git state", "ok")
        )
        return steps

    def plan_device(self, folders: Sequence[Folder], target: Host) -> DevicePlan:
        """Plan an idempotent catch-up of one host for every given folder."""
        hosts, skipped = self.runner.split_reachable(HOST_NAMES)
        if target not in hosts:
            raise UsageError(
                f"{self.runner.describe(target)} is unreachable over SSH; wake it first"
            )
        if len(hosts) < 2:
            raise UsageError(
                f"no machine other than {alias(target)} is reachable over SSH"
            )
        ids = self.device_ids(hosts)
        configs = {host: self.config(host) for host in hosts}
        steps = self._pairing_steps(hosts, ids, configs)
        blocked: list[str] = []
        for folder in folders:
            steps.extend(
                self._folder_steps(folder, target, hosts, ids, configs, blocked)
            )
        if blocked:
            raise UsageError(
                f"refusing nonempty destinations on {alias(target)}; "
                "move them aside first: " + ", ".join(blocked)
            )
        return DevicePlan(target, hosts, skipped, tuple(steps))

    def apply_device(self, plan: DevicePlan) -> None:
        """Back up changed hosts, then apply the planned steps in order."""
        changes = plan.changes
        if not changes:
            return
        self._backup_configs(tuple(dict.fromkeys(step.host for step in changes)))
        for step in changes:
            assert step.apply is not None
            step.apply()

    def _gui_access(self, host: Host) -> tuple[str, str]:
        if host not in self._gui:
            self._gui[host] = (
                self.st(host, "config", "gui", "apikey", "get"),
                self.st(host, "config", "gui", "raw-address", "get"),
            )
        return self._gui[host]

    def scan(self, host: Host, folder_id: str) -> None:
        """Request an immediate authenticated folder scan."""
        key, address = self._gui_access(host)
        self.runner.run(
            host,
            [
                "curl",
                "-fsS",
                "-X",
                "POST",
                "-H",
                "@-",
                f"http://{address}/rest/db/scan?folder={folder_id}",
            ],
            input_text=f"X-API-Key: {key}\n",
        )

    def status(self, host: Host, folder_id: str) -> dict[str, Any]:
        """Read one folder status through Syncthing's local REST endpoint."""
        key, address = self._gui_access(host)
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

    def _folder_state(
        self,
        host: Host,
        folder: Folder,
        config: Mapping[str, Any],
    ) -> FolderState:
        if find_folder(config, folder.id) is None:
            return FolderState("not configured")
        try:
            status = self.status(host, folder.id)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
            return FolderState("error", error=_error_text(error))
        state = str(status.get("state") or "unknown")
        if status.get("errors"):
            state += f", {status['errors']} errors"
        return FolderState(state, completion(status))

    def overview(self, folders: Sequence[Folder]) -> StatusReport:
        """Read every folder's state on every reachable host."""
        reachable, unreachable = self.runner.split_reachable(HOST_NAMES)
        states: dict[str, dict[Host, FolderState]] = {
            folder.id: {} for folder in folders
        }
        for host in HOST_NAMES:
            if host in unreachable:
                for folder in folders:
                    states[folder.id][host] = FolderState("unreachable")
                continue
            try:
                config = self.config(host)
            except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
                for folder in folders:
                    states[folder.id][host] = FolderState(
                        "error", error=_error_text(error)
                    )
                continue
            for folder in folders:
                states[folder.id][host] = self._folder_state(host, folder, config)
        return StatusReport(reachable, unreachable, states)

    def wait_idle(
        self,
        folder_id: str,
        timeout: int,
        ids: Mapping[Host, str],
    ) -> dict[Host, dict[str, Any]]:
        """Wait until the hosts in ids report an idle, mutually current folder."""
        deadline = self.monotonic() + timeout
        while True:
            statuses: dict[Host, dict[str, Any]] = {
                host: self.status(host, folder_id) for host in ids
            }
            if statuses_converged(statuses, ids):
                return statuses
            if self.monotonic() >= deadline:
                raise UsageError(
                    f"timed out waiting for {folder_id}; "
                    "folder remains configured for inspection"
                )
            self.sleep(2)

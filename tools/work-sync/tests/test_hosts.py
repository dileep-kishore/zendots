from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

import work_sync.cli as cli_module
from work_sync.add import infer_destination
from work_sync.cli import Target, app
from work_sync.coordinator import (
    MANIFEST_PATHS,
    Handoff,
    verify_manifest_copies,
    verify_manifest_for_device,
)
from work_sync.handoff import Orca, OrcaInventory, _rsync_endpoints
from work_sync.manifest import (
    HOST_NAMES,
    HOSTS,
    Folder,
    Host,
    UsageError,
    detect_host,
    load_manifest,
)
from work_sync.syncthing import (
    GIT_PROBE_PREFIX,
    Syncthing,
    folder_payload,
    reconcile_ignore_text,
    statuses_converged,
)
from work_sync.system import Runner

ALIASES = {info.alias: host for host, info in HOSTS.items()}
PLAIN = Folder(
    "notes",
    "Notes",
    Path("/Volumes/WorkSSD/Personal/Notes"),
    Path("/home/dileep/Documents/Personal/Notes"),
    "plain",
    "none",
    (),
)
REPO = Folder(
    "zendots",
    "Zendots",
    Path("/Users/dkishore/zendots"),
    Path("/home/dileep/zendots"),
    "git",
    "local",
    (),
)


def _fail(command: list[str], code: int = 1) -> subprocess.CalledProcessError:
    return subprocess.CalledProcessError(code, command, stderr="failed")


def _entry(folder: Folder) -> dict[str, object]:
    return {
        "id": folder.id,
        "label": folder.label,
        "mac": str(folder.mac),
        "tsuki": str(folder.tsuki),
        "class": folder.folder_class,
        "git": folder.git,
        "ignore": list(folder.ignore),
    }


class FakeHosts:
    """Three in-memory machines reached through a fake SSH executor."""

    def __init__(self, local: Host = "mac", unreachable: Iterable[Host] = ()) -> None:
        self.local = local
        self.unreachable = set(unreachable)
        self.configs: dict[Host, dict[str, Any]] = {
            host: {"devices": [{"deviceID": f"ID-{host}"}], "folders": []}
            for host in HOST_NAMES
        }
        self.files: dict[Host, dict[str, str]] = {host: {} for host in HOST_NAMES}
        self.dirs: dict[Host, set[str]] = {host: set() for host in HOST_NAMES}
        self.statuses: dict[tuple[Host, str], dict[str, Any]] = {}
        self.broken: set[Host] = set()
        self.calls: list[tuple[Host, list[str]]] = []
        self.git_config: dict[Host, dict[tuple[str, str, str], str]] = {
            host: {} for host in HOST_NAMES
        }
        self.tracked: set[tuple[Host, str]] = set()
        self.incomplete: set[tuple[Host, str]] = set()
        self.fail_add_json = 0
        self.drops: list[tuple[Host, str]] = []

    def runner(self) -> Runner:
        return Runner(self.local, execute=self.execute)

    def pair(self, *hosts: Host) -> None:
        for host in hosts:
            for other in hosts:
                if other != host:
                    self.configs[host]["devices"].append({"deviceID": f"ID-{other}"})

    def share(self, folder: Folder, *hosts: Host, devices: Iterable[Host] = ()) -> None:
        members = tuple(dict.fromkeys((*hosts, *devices)))
        for host in hosts:
            payload = folder_payload({}, folder, [f"ID-{h}" for h in members], host)
            payload["paused"] = False
            self.configs[host]["folders"].append(payload)
            self.dirs[host].add(str(folder.path(host)))

    def manifests(self, text: str = "[]\n") -> None:
        for host in HOST_NAMES:
            for path in MANIFEST_PATHS[host]:
                self.files[host][str(path)] = text

    def commands(self, host: Host) -> list[list[str]]:
        return [command for current, command in self.calls if current == host]

    def execute(self, argv: list[str], input_text: str | None) -> str:
        if argv[0] == "ssh":
            host = ALIASES[argv[-2]]
            command = shlex.split(argv[-1])
            if host in self.unreachable:
                error = _fail(argv, 255)
                error.stderr = f"ssh: connect to host {argv[-2]} port 22: timed out\n"
                raise error
        else:
            host, command = self.local, argv
        self.calls.append((host, command))
        joined = shlex.join(command)
        for drop in self.drops:
            if drop[0] == host and drop[1] in joined:
                self.drops.remove(drop)
                raise _fail(argv, 255)
        return self._handle(host, command, input_text)

    def _folder(self, host: Host, folder_id: str) -> dict[str, Any]:
        return next(
            item for item in self.configs[host]["folders"] if item["id"] == folder_id
        )

    def _syncthing(self, host: Host, args: list[str]) -> str:
        if args == ["device-id"]:
            return f"ID-{host}"
        config = self.configs[host]
        match args[1:]:
            case ["config", "dump-json"]:
                if host in self.broken:
                    raise _fail(args)
                return json.dumps(config)
            case ["config", "defaults", _, "dump-json"]:
                return "{}"
            case ["config", "gui", "apikey", "get"]:
                return "key"
            case ["config", "gui", "raw-address", "get"]:
                return "127.0.0.1:8384"
            case ["config", "folders", "add-json", payload]:
                if self.fail_add_json:
                    self.fail_add_json -= 1
                    raise _fail(args)
                config["folders"].append(json.loads(payload))
            case ["config", "devices", "add-json", payload]:
                config["devices"].append(json.loads(payload))
            case ["config", "folders", folder_id, "devices", "add", "--device-id", d]:
                self._folder(host, folder_id)["devices"].append({"deviceID": d})
            case ["config", "folders", folder_id, "paused", "set", value]:
                self._folder(host, folder_id)["paused"] = value == "true"
            case _:
                raise AssertionError(args)
        return ""

    def _git(self, host: Host, command: list[str]) -> str:
        store = self.git_config[host]
        if command[1] == "init":
            probe = command[-1]
            self.dirs[host].add(probe)
            for key in ("core.ignorecase", "core.precomposeunicode"):
                store[(probe, "local", key)] = "true"
            return ""
        repo, args = command[2], command[3:]
        if (host, repo) in self.incomplete:
            raise _fail(command, 128)
        if args[:2] == ["rev-parse", "--git-dir"]:
            return ".git"
        if args[:2] == ["rev-parse", "HEAD"]:
            return "a" * 40
        if args[:2] == ["rev-parse", "--git-path"]:
            return ".git/info/exclude"
        if args[0] == "ls-files":
            if (host, repo) not in self.tracked:
                raise _fail(command)
            return ".stignore"
        if args[0] == "config":
            scope = args[1].removeprefix("--")
            match args[2:]:
                case ["--get", key]:
                    if (repo, scope, key) not in store:
                        raise _fail(command)
                    return store[(repo, scope, key)]
                case ["--unset-all", key]:
                    store.pop((repo, scope, key), None)
                case [key, value]:
                    store[(repo, scope, key)] = value
        return ""

    def _handle(self, host: Host, command: list[str], input_text: str | None) -> str:
        name = Path(command[0]).name
        files, dirs = self.files[host], self.dirs[host]
        if name == "true" or name == "chmod":
            return ""
        if name == "syncthing":
            return self._syncthing(host, command[1:])
        if name == "git":
            return self._git(host, command)
        if name == "test":
            path = command[2]
            found = path in dirs if command[1] == "-d" else path in dirs | set(files)
            if not found:
                raise _fail(command)
            return ""
        if name == "find":
            children = [
                item
                for item in (*dirs, *files)
                if Path(item).parent == Path(command[1])
                and not ("!" in command and Path(item).name == ".stignore")
            ]
            return children[0] if children and "-quit" in command else ""
        if name == "mkdir":
            dirs.add(command[-1])
            return ""
        if name == "mktemp":
            created = command[-1].replace("XXXXXX", "abc123")
            dirs.add(created)
            return created
        if name == "rm":
            removed = Path(command[-1])
            dirs.difference_update(
                {item for item in dirs if Path(item).is_relative_to(removed)}
            )
            return ""
        if name == "cat":
            if command[1] not in files:
                raise _fail(command)
            return files[command[1]].strip()
        if name == "tee":
            files[command[1]] = input_text or ""
            return ""
        if name in {"shasum", "sha256sum"}:
            if command[-1] not in files:
                raise _fail(command)
            digest = hashlib.sha256(files[command[-1]].encode()).hexdigest()
            return f"{digest}  {command[-1]}"
        if name == "curl":
            folder_id = command[-1].split("folder=")[1]
            if "/rest/db/scan" in command[-1]:
                return ""
            default = {
                "state": "idle",
                "sequence": 5,
                "remoteSequence": {f"ID-{other}": 5 for other in HOST_NAMES},
                "globalBytes": 100,
                "needBytes": 0,
            }
            return json.dumps(self.statuses.get((host, folder_id), default))
        raise AssertionError(command)


def _service(fake: FakeHosts) -> Syncthing:
    return Syncthing(fake.runner(), sleep=lambda seconds: None)


def _probe_only(fake: FakeHosts, host: Host) -> bool:
    return all(command == ["true"] for command in fake.commands(host))


def _devices(fake: FakeHosts, host: Host, folder_id: str) -> list[str]:
    return [item["deviceID"] for item in fake._folder(host, folder_id)["devices"]]


def test_host_detection_prefers_environment_then_host_file_then_platform(
    tmp_path: Path,
) -> None:
    host_file = tmp_path / "host"
    host_file.write_text("macbook\n", encoding="utf-8")
    environ = {"WORK_SYNC_HOST": "tsuki"}

    assert detect_host("Darwin", environ=environ, host_file=host_file) == "tsuki"
    assert detect_host("Darwin", environ={}, host_file=host_file) == "macbook"
    assert detect_host("Darwin", environ={}, host_file=tmp_path / "none") == "mac"
    with pytest.raises(UsageError, match="invalid host 'laptop' in WORK_SYNC_HOST"):
        detect_host(environ={"WORK_SYNC_HOST": "laptop"}, host_file=host_file)
    host_file.write_text("macmini\n", encoding="utf-8")
    with pytest.raises(UsageError, match="invalid host 'macmini'"):
        detect_host(environ={}, host_file=host_file)


def test_macbook_uses_mac_paths_and_its_own_ssh_alias() -> None:
    assert PLAIN.path("macbook") == PLAIN.path("mac") == PLAIN.mac
    assert Runner("mac").command("macbook", ["true"])[-2:] == ["macbook", "true"]
    assert Runner("macbook").command("mac", ["true"])[-2:] == ["macmini", "true"]
    assert Runner("macbook").command("macbook", ["true"]) == ["true"]
    assert infer_destination("macbook", PLAIN.mac) == PLAIN.tsuki


def test_manifest_allows_sync_root_vault_but_not_other_root_folders(
    tmp_path: Path,
) -> None:
    path = tmp_path / "folders.json"
    vault = {
        **_entry(PLAIN),
        "id": "ideaverse",
        "label": "Ideaverse",
        "mac": "/Volumes/WorkSSD/Ideaverse",
        "tsuki": "/home/dileep/Documents/Ideaverse",
    }
    path.write_text(json.dumps([vault]), encoding="utf-8")
    assert load_manifest(path).select("Ideaverse").path("macbook") == Path(
        "/Volumes/WorkSSD/Ideaverse"
    )

    other = {
        **vault,
        "mac": "/Volumes/WorkSSD/orca",
        "tsuki": "/home/dileep/Documents/orca",
    }
    path.write_text(json.dumps([other]), encoding="utf-8")
    with pytest.raises(UsageError, match="unsafe Mac path"):
        load_manifest(path)


def test_folder_payload_lists_every_device() -> None:
    payload = folder_payload({}, PLAIN, ("ID-mac", "ID-macbook", "ID-tsuki"), "tsuki")

    assert [item["deviceID"] for item in payload["devices"]] == [
        "ID-mac",
        "ID-macbook",
        "ID-tsuki",
    ]
    assert payload["path"] == str(PLAIN.tsuki)


def test_convergence_matches_each_peer_by_device_id() -> None:
    ids: dict[Host, str] = {host: f"ID-{host}" for host in HOST_NAMES}
    statuses: dict[Host, dict[str, Any]] = {
        host: {
            "state": "idle",
            "sequence": 30,
            "remoteSequence": {ids[other]: 30 for other in HOST_NAMES if other != host},
        }
        for host in HOST_NAMES
    }
    assert statuses_converged(statuses, ids)
    for host in ("mac", "tsuki"):
        statuses[host]["remoteSequence"]["ID-macbook"] = 10
    # Every local sequence is 30, so a value-only match would pass here.
    assert not statuses_converged(statuses, ids)
    del statuses["macbook"]
    del ids["macbook"]
    assert statuses_converged(statuses, ids)
    statuses["mac"]["remoteSequence"] = {"ID-macbook": 30}
    assert not statuses_converged(statuses, ids)


def test_wait_idle_contacts_only_the_listed_hosts() -> None:
    fake = FakeHosts(unreachable={"macbook"})
    _service(fake).wait_idle("notes", 5, {"mac": "ID-mac", "tsuki": "ID-tsuki"})
    assert not fake.commands("macbook")


def test_bootstrap_skips_an_unreachable_host() -> None:
    fake = FakeHosts(unreachable={"macbook"})
    fake.pair("mac", "tsuki")
    fake.dirs["mac"].add(str(PLAIN.mac))
    fake.dirs["tsuki"].add(str(PLAIN.tsuki))

    plan = _service(fake).bootstrap(PLAIN, apply=True, timeout=5)

    assert plan.hosts == ("mac", "tsuki")
    assert plan.skipped == ("macbook",)
    for host in ("mac", "tsuki"):
        assert _devices(fake, host, "notes") == ["ID-mac", "ID-tsuki"]
        assert str(PLAIN.path(host) / ".stignore") in fake.files[host]
    assert _probe_only(fake, "macbook")


def test_bootstrap_cli_names_the_skipped_host(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeHosts(unreachable={"macbook"})
    fake.pair("mac", "tsuki")
    fake.manifests()
    fake.dirs["mac"].add(str(PLAIN.mac))
    fake.dirs["tsuki"].add(str(PLAIN.tsuki))
    manifest = tmp_path / "folders.json"
    manifest.write_text(json.dumps([_entry(PLAIN)]), encoding="utf-8")
    monkeypatch.setattr(cli_module, "_runner", fake.runner)

    result = CliRunner().invoke(
        app,
        ["bootstrap", "Notes", "--manifest", str(manifest)],
        env={"COLUMNS": "400"},
    )

    assert result.exit_code == 0, result.output
    assert "Skipped macbook (ssh: connect to host macbook port 22: timed out)" in (
        result.output
    )
    assert (
        "run chezmoi apply ~/.config/work-sync/folders.json there, "
        "then work-sync add-device macbook." in result.output
    )


def test_bootstrap_tolerates_an_offline_member_but_flags_a_missing_one() -> None:
    fake = FakeHosts(unreachable={"macbook"})
    fake.pair("mac", "tsuki")
    fake.share(PLAIN, "mac", "tsuki", devices=("macbook",))

    assert _service(fake).plan(PLAIN).skipped == ("macbook",)

    fake = FakeHosts()
    fake.pair("mac", "macbook", "tsuki")
    fake.share(PLAIN, "mac", "tsuki")
    fake.dirs["macbook"].add(str(PLAIN.mac))
    with pytest.raises(UsageError, match="work-sync add-device macbook"):
        _service(fake).plan(PLAIN)


def test_add_configures_reachable_targets_and_skips_the_rest() -> None:
    fake = FakeHosts(unreachable={"tsuki"})
    fake.pair("mac", "macbook")
    fake.dirs["mac"].add(str(PLAIN.mac))
    service = _service(fake)

    plan = service.plan_new(PLAIN, "mac")
    service.apply_new(plan, "mac", timeout=5)

    assert plan.skipped == ("tsuki",)
    assert str(PLAIN.mac) in fake.dirs["macbook"]
    assert str(PLAIN.mac / ".stignore") in fake.files["macbook"]
    assert _devices(fake, "macbook", "notes") == ["ID-mac", "ID-macbook"]
    assert _probe_only(fake, "tsuki")


def test_add_requires_a_reachable_peer() -> None:
    fake = FakeHosts(unreachable={"macbook", "tsuki"})
    fake.dirs["mac"].add(str(PLAIN.mac))

    with pytest.raises(UsageError, match="no other machine is reachable"):
        _service(fake).plan_new(PLAIN, "mac")


def test_manifest_check_skips_offline_hosts_and_rejects_reachable_mismatch() -> None:
    fake = FakeHosts(unreachable={"macbook"})
    fake.manifests('[{"id": "a"}]\n')

    check = verify_manifest_copies(fake.runner())

    assert check.unreachable == ("macbook",)
    assert _probe_only(fake, "macbook")
    fake.files["tsuki"][str(MANIFEST_PATHS["tsuki"][1])] = "[]\n"
    with pytest.raises(UsageError, match="private manifests differ"):
        verify_manifest_copies(fake.runner())


def _fresh_macbook() -> FakeHosts:
    fake = FakeHosts()
    fake.pair("mac", "tsuki")
    fake.share(PLAIN, "mac", "tsuki")
    fake.share(REPO, "mac", "tsuki")
    return fake


def test_add_device_dry_run_plans_in_order_without_changes() -> None:
    fake = _fresh_macbook()
    before = json.dumps(fake.configs, sort_keys=True)

    plan = _service(fake).plan_device((PLAIN, REPO), "macbook")

    assert json.dumps(fake.configs, sort_keys=True) == before
    assert not fake.files["macbook"]
    assert not fake.dirs["macbook"]
    changed = {(step.host, step.subject, step.description) for step in plan.changes}
    assert ("mac", "devices", "knows device macbook") in changed
    assert ("macbook", "devices", "knows device tsuki") in changed
    assert ("tsuki", "Zendots", "folder lists macbook") in changed
    assert ("mac", "devices", "knows device tsuki") not in changed
    target_steps = [
        step.description
        for step in plan.steps
        if step.host == "macbook" and step.subject == "Zendots"
    ]
    assert target_steps == [
        "directory /Users/dkishore/zendots",
        "managed .stignore",
        "add folder shared with macmini, tsuki",
        "machine-local Git state waits for synchronization; rerun add-device",
    ]


def test_add_device_installs_ignores_first_and_is_idempotent() -> None:
    fake = _fresh_macbook()
    service = _service(fake)

    service.apply_device(service.plan_device((PLAIN, REPO), "macbook"))

    commands = fake.commands("macbook")
    ignore = commands.index(["tee", str(REPO.mac / ".stignore")])
    added = next(
        index
        for index, command in enumerate(commands)
        if "add-json" in command and "zendots" in command[-1]
    )
    assert ignore < added
    assert ".git/FETCH_HEAD" in fake.files["macbook"][str(REPO.mac / ".stignore")]
    assert _devices(fake, "macbook", "zendots") == ["ID-mac", "ID-macbook", "ID-tsuki"]
    assert "ID-macbook" in _devices(fake, "tsuki", "zendots")
    assert fake._folder("macbook", "zendots")["paused"] is False
    assert not _service(fake).plan_device((PLAIN, REPO), "macbook").changes


def test_add_device_refuses_a_nonempty_destination() -> None:
    fake = _fresh_macbook()
    fake.dirs["macbook"].add(str(REPO.mac))
    fake.files["macbook"][str(REPO.mac / "README.md")] = "local\n"

    with pytest.raises(UsageError, match="refusing nonempty destinations"):
        _service(fake).plan_device((PLAIN, REPO), "macbook")


def test_add_device_cli_dry_run_skips_target_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fresh_macbook()
    fake.manifests()
    for path in MANIFEST_PATHS["macbook"]:
        del fake.files["macbook"][str(path)]
    manifest = tmp_path / "folders.json"
    manifest.write_text(json.dumps([_entry(PLAIN), _entry(REPO)]), encoding="utf-8")
    monkeypatch.setattr(cli_module, "_runner", fake.runner)

    result = CliRunner().invoke(
        app, ["add-device", "macbook", "--dry-run", "--manifest", str(manifest)]
    )

    assert result.exit_code == 0, result.output
    assert "Would change" in result.output
    assert "Dry run passed" in result.output
    assert not fake._folder("tsuki", "zendots")["devices"][2:]


def test_add_device_never_rewrites_an_existing_tracked_stignore() -> None:
    fake = _fresh_macbook()
    fake.share(REPO, "macbook", devices=("mac", "tsuki"))
    fake.tracked.add(("mac", str(REPO.mac)))
    fake.files["mac"][str(REPO.mac / ".stignore")] = "/peer-rule\n"
    target_ignore = str(REPO.mac / ".stignore")
    fake.files["macbook"][target_ignore] = "/target-only\n"
    service = _service(fake)

    service.apply_device(service.plan_device((REPO,), "macbook"))

    assert fake.files["macbook"][target_ignore] == "/target-only\n"
    assert ["tee", target_ignore] not in fake.commands("macbook")
    strict = replace(REPO, ignore=("/build",))
    with pytest.raises(UsageError, match=r"missing manifest patterns: /build"):
        service.plan_device((strict,), "macbook")


def test_add_device_copies_a_tracked_stignore_into_a_fresh_destination() -> None:
    fake = _fresh_macbook()
    fake.tracked.add(("mac", str(REPO.mac)))
    fake.files["mac"][str(REPO.mac / ".stignore")] = "/peer-rule\n"
    service = _service(fake)

    service.apply_device(service.plan_device((REPO,), "macbook"))

    assert fake.files["macbook"][str(REPO.mac / ".stignore")] == "/peer-rule\n"


def test_add_device_resumes_after_an_interrupted_folder_add() -> None:
    fake = _fresh_macbook()
    fake.fail_add_json = 1
    service = _service(fake)

    with pytest.raises(subprocess.CalledProcessError):
        service.apply_device(service.plan_device((PLAIN, REPO), "macbook"))
    assert str(PLAIN.mac / ".stignore") in fake.files["macbook"]
    assert not fake.configs["macbook"]["folders"]

    service.apply_device(service.plan_device((PLAIN, REPO), "macbook"))

    assert _devices(fake, "macbook", "notes") == ["ID-mac", "ID-macbook", "ID-tsuki"]
    assert not service.plan_device((PLAIN, REPO), "macbook").changes


def test_add_device_stops_on_a_stale_remote_applied_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fresh_macbook()
    fake.manifests('[{"id": "new"}]\n')
    for path in MANIFEST_PATHS["macbook"]:
        del fake.files["macbook"][str(path)]
    assert verify_manifest_for_device(fake.runner(), "macbook").unreachable == ()

    fake.files["macbook"][str(MANIFEST_PATHS["macbook"][1])] = "[]\n"
    before = json.dumps(fake.configs, sort_keys=True)
    manifest = tmp_path / "folders.json"
    manifest.write_text(json.dumps([_entry(PLAIN)]), encoding="utf-8")
    monkeypatch.setattr(cli_module, "_runner", fake.runner)

    result = CliRunner().invoke(
        app,
        ["add-device", "macbook", "--yes", "--manifest", str(manifest)],
        env={"COLUMNS": "400"},
    )

    assert result.exit_code == 1
    assert "chezmoi apply ~/.config/work-sync/folders.json" in result.output
    assert json.dumps(fake.configs, sort_keys=True) == before


def test_add_device_on_the_target_verifies_its_own_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fresh_macbook()
    fake.local = "macbook"
    fake.manifests('[{"id": "new"}]\n')
    fake.files["macbook"][str(MANIFEST_PATHS["macbook"][1])] = "[]\n"
    manifest = tmp_path / "folders.json"
    manifest.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(cli_module, "_runner", fake.runner)

    result = CliRunner().invoke(
        app, ["add-device", "macbook", "--yes", "--manifest", str(manifest)]
    )

    assert result.exit_code == 1
    assert "private manifests differ" in result.output
    assert not fake.configs["macbook"]["folders"]


def _synced_macbook_repo() -> tuple[FakeHosts, str, dict[tuple[str, str, str], str]]:
    fake = _fresh_macbook()
    fake.share(REPO, "macbook", devices=("mac", "tsuki"))
    repo = str(REPO.mac)
    fake.dirs["macbook"].add(f"{repo}/.git")
    fake.files["macbook"][f"{repo}/.stignore"] = reconcile_ignore_text("", REPO)
    fake.files["macbook"][f"{repo}/.git/info/exclude"] = ".stignore\n.stfolder\n"
    store = fake.git_config["macbook"]
    store[(repo, "local", "extensions.worktreeConfig")] = "true"
    return fake, repo, store


def test_add_device_sets_filesystem_git_keys_on_a_macos_target() -> None:
    fake, repo, store = _synced_macbook_repo()
    service = _service(fake)

    plan = service.plan_device((REPO,), "macbook")
    target_changes = [
        step.description
        for step in plan.changes
        if step.host == "macbook" and step.subject == "Zendots"
    ]
    assert target_changes == ["machine-local Git state"]
    service.apply_device(plan)

    assert store[(repo, "worktree", "core.ignorecase")] == "true"
    assert store[(repo, "worktree", "core.precomposeunicode")] == "true"
    probe = next(
        command for command in fake.commands("macbook") if command[0] == "mktemp"
    )
    assert Path(probe[-1]).parent == REPO.mac.parent
    assert not any(".work-sync-git-probe." in item for item in fake.dirs["macbook"])
    assert not service.plan_device((REPO,), "macbook").changes
    assert service._missing_filesystem_keys("tsuki", REPO.tsuki) == ()


def test_add_device_waits_for_a_git_directory_still_syncing() -> None:
    fake, repo, store = _synced_macbook_repo()
    fake.incomplete.add(("macbook", repo))
    service = _service(fake)

    plan = service.plan_device((REPO,), "macbook")
    service.apply_device(plan)

    target_steps = [
        step.description
        for step in plan.steps
        if step.host == "macbook" and step.subject == "Zendots"
    ]
    assert target_steps[-1] == (
        "machine-local Git state waits for synchronization; rerun add-device"
    )
    assert not any(scope == "worktree" for _, scope, _ in store)


def test_add_device_fails_when_the_worktree_key_read_drops() -> None:
    fake, _, store = _synced_macbook_repo()
    fake.drops.append(("macbook", "config --worktree --get core.ignorecase"))

    with pytest.raises(subprocess.CalledProcessError):
        _service(fake).plan_device((REPO,), "macbook")

    assert not fake.drops
    assert not any(scope == "worktree" for _, scope, _ in store)
    assert not any(
        command[0] in {"tee", "mktemp"} for command in fake.commands("macbook")
    )


def test_add_device_fails_when_the_probe_read_drops() -> None:
    fake, _, store = _synced_macbook_repo()
    service = _service(fake)
    plan = service.plan_device((REPO,), "macbook")
    fake.drops.append(
        ("macbook", f"{GIT_PROBE_PREFIX}abc123 config --local --get core.ignorecase")
    )

    with pytest.raises(subprocess.CalledProcessError):
        service.apply_device(plan)

    assert not fake.drops
    assert not any(scope == "worktree" for _, scope, _ in store)
    assert not any(GIT_PROBE_PREFIX in item for item in fake.dirs["macbook"])


def test_add_device_fails_when_the_applied_manifest_test_drops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fresh_macbook()
    fake.manifests('[{"id": "new"}]\n')
    applied = str(MANIFEST_PATHS["macbook"][1])
    fake.files["macbook"][applied] = "[]\n"
    fake.drops.append(("macbook", f"test -e {applied}"))
    before = json.dumps(fake.configs, sort_keys=True)
    manifest = tmp_path / "folders.json"
    manifest.write_text(json.dumps([_entry(PLAIN)]), encoding="utf-8")
    monkeypatch.setattr(cli_module, "_runner", fake.runner)

    result = CliRunner().invoke(
        app, ["add-device", "macbook", "--yes", "--manifest", str(manifest)]
    )

    assert not fake.drops
    assert result.exit_code == 1
    assert json.dumps(fake.configs, sort_keys=True) == before
    assert not any(command[0] == "tee" for command in fake.commands("macbook"))


def _nonempty_fresh_target() -> tuple[FakeHosts, tuple[Host, str]]:
    fake = _fresh_macbook()
    fake.dirs["macbook"].add(str(REPO.mac))
    fake.files["macbook"][str(REPO.mac / "README.md")] = "local\n"
    return fake, ("macbook", f"test -e {REPO.mac}")


def _local_rule_target() -> tuple[FakeHosts, tuple[Host, str]]:
    fake, repo, _ = _synced_macbook_repo()
    fake.files["macbook"][f"{repo}/.stignore"] = "/target-private\n" + (
        reconcile_ignore_text("", REPO)
    )
    return fake, ("macbook", f"cat {repo}/.stignore")


def _tracked_peer() -> tuple[FakeHosts, tuple[Host, str]]:
    fake = _fresh_macbook()
    fake.tracked.update({("mac", str(REPO.mac)), ("tsuki", str(REPO.tsuki))})
    fake.files["mac"][str(REPO.mac / ".stignore")] = reconcile_ignore_text("", REPO)
    return fake, ("mac", "ls-files --error-unmatch .stignore")


def _repository_probe_target() -> tuple[FakeHosts, tuple[Host, str]]:
    fake, _, _ = _synced_macbook_repo()
    return fake, ("macbook", "rev-parse --git-dir")


@pytest.mark.parametrize(
    "setup",
    [
        _nonempty_fresh_target,
        _local_rule_target,
        _tracked_peer,
        _repository_probe_target,
    ],
)
def test_add_device_fails_when_a_presence_probe_drops(
    setup: Callable[[], tuple[FakeHosts, tuple[Host, str]]],
) -> None:
    fake, drop = setup()
    fake.drops.append(drop)

    with pytest.raises(subprocess.CalledProcessError):
        _service(fake).plan_device((REPO,), "macbook")

    assert not fake.drops
    assert not any(command[0] == "tee" for command in fake.commands("macbook"))


def test_status_reports_offline_hosts_without_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeHosts(unreachable={"macbook"})
    fake.share(PLAIN, "mac", "tsuki")
    fake.statuses[("tsuki", "notes")] = {
        "state": "syncing",
        "globalBytes": 200,
        "needBytes": 50,
    }
    manifest = tmp_path / "folders.json"
    manifest.write_text(json.dumps([_entry(PLAIN)]), encoding="utf-8")
    monkeypatch.setattr(cli_module, "_runner", fake.runner)

    result = CliRunner().invoke(
        app, ["status", "--manifest", str(manifest)], env={"COLUMNS": "400"}
    )

    assert result.exit_code == 0, result.output
    assert "idle 100%" in result.output
    assert "syncing 75%" in result.output
    assert "unreachable" in result.output
    assert (
        "Unreachable over SSH: macbook (ssh: connect to host macbook port 22: "
        "timed out)." in result.output
    )

    fake.broken.add("tsuki")
    result = CliRunner().invoke(app, ["status", "--manifest", str(manifest)])
    assert result.exit_code == 1


def test_handoff_to_macbook_touches_only_source_and_target() -> None:
    fake = FakeHosts()
    fake.manifests()

    class EmptyOrca(Orca):
        def inventory(self, host: Host) -> OrcaInventory:
            return OrcaInventory(())

    runner = fake.runner()
    plan = Handoff(runner, Syncthing(runner), EmptyOrca(runner)).preflight(
        (), Target("macbook").host, timeout=5
    )

    assert plan.target == "macbook"
    assert plan.recovery_root.is_relative_to("/Users/dkishore/.local/state")
    assert not fake.commands("tsuki")
    assert _rsync_endpoints("mac", Path("/a"), "macbook", Path("/b")) == (
        "mac",
        ("/a/", "macbook:/b/"),
    )
    assert _rsync_endpoints("tsuki", Path("/a"), "macbook", Path("/b")) == (
        "macbook",
        ("tsuki:/a/", "/b/"),
    )

    fake.unreachable.add("macbook")
    runner = fake.runner()
    with pytest.raises(
        UsageError, match=r"macbook \(ssh: .*timed out\) is unreachable"
    ):
        Handoff(runner, Syncthing(runner), EmptyOrca(runner)).preflight(
            (), "macbook", timeout=5
        )

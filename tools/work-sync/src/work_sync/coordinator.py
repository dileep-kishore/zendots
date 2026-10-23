"""Cross-machine Orca worktree handoff planning and execution."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .handoff import (
    Orca,
    OrcaRepo,
    RepositoryPlan,
    RepoState,
    WorktreePair,
    pair_worktrees,
    preflight_missing_worktree,
    preflight_repository,
    rebuild_index,
    sync_worktree_files,
)
from .manifest import HOST_NAMES, HOSTS, Folder, Host, UsageError, alias
from .syncthing import Syncthing
from .system import Runner

MANIFEST_PATHS: dict[Host, tuple[Path, Path]] = {
    host: (
        info.home / "zendots/private_dot_config/work-sync/private_folders.json",
        info.home / ".config/work-sync/folders.json",
    )
    for host, info in HOSTS.items()
}


@dataclass(frozen=True)
class ManifestCheck:
    """Matching manifest digest and the hosts that could not be compared."""

    digest: str
    unreachable: tuple[Host, ...]


@dataclass(frozen=True)
class MissingWorktree:
    """A source worktree that Orca must create on the target."""

    pair: WorktreePair
    source_state: RepoState
    existing_commit: str | None
    base_ref: str


@dataclass(frozen=True)
class FolderHandoff:
    """Complete preflight result for one manifest repository."""

    folder: Folder
    main: RepositoryPlan
    source_orca: OrcaRepo | None
    target_orca: OrcaRepo | None
    existing_worktrees: tuple[tuple[WorktreePair, RepositoryPlan], ...]
    missing_worktrees: tuple[MissingWorktree, ...]


@dataclass(frozen=True)
class HandoffPlan:
    """Globally validated multi-repository handoff."""

    source: Host
    target: Host
    folders: tuple[FolderHandoff, ...]
    recovery_root: Path


@dataclass(frozen=True)
class HandoffResult:
    """One completed repository handoff."""

    folder: str
    worktrees: int
    recovery_root: Path


def _digest(runner: Runner, host: Host, path: Path) -> str:
    command = (
        ["shasum", "-a", "256", str(path)]
        if HOSTS[host].platform == "darwin"
        else ["sha256sum", str(path)]
    )
    try:
        return runner.run(host, command).split()[0]
    except (IndexError, OSError, subprocess.CalledProcessError) as error:
        raise UsageError(
            f"cannot hash manifest on {host}: {path}; a new machine needs "
            f"work-sync add-device {alias(host)} and a scoped chezmoi apply"
        ) from error


def verify_manifest_copies(
    runner: Runner,
    hosts: Sequence[Host] = HOST_NAMES,
) -> ManifestCheck:
    """Require private manifest copies to match on every reachable host."""
    reachable, unreachable = runner.split_reachable(hosts)
    digests = {
        (host, path): _digest(runner, host, path)
        for host in reachable
        for path in MANIFEST_PATHS[host]
    }
    if not digests:
        raise UsageError("no host is reachable for the manifest check")
    unique = set(digests.values())
    if len(unique) != 1:
        details = ", ".join(
            f"{host}:{path}={digest[:12]}" for (host, path), digest in digests.items()
        )
        raise UsageError(
            "private manifests differ; run the scoped chezmoi apply on the "
            f"stale host ({details})"
        )
    return ManifestCheck(unique.pop(), unreachable)


def verify_manifest_for_device(runner: Runner, target: Host) -> ManifestCheck:
    """Verify manifests, exempting only a remote target that has none applied."""
    if target == runner.local_host or not runner.reachable(target):
        return verify_manifest_copies(runner)
    check = verify_manifest_copies(runner, tuple(h for h in HOST_NAMES if h != target))
    applied = MANIFEST_PATHS[target][1]
    try:
        runner.run(target, ["test", "-e", str(applied)])
    except subprocess.CalledProcessError as error:
        # Only exit 1 proves absence; an ssh failure (255) must not skip the check.
        if error.returncode != 1:
            raise
        return check
    if _digest(runner, target, applied) != check.digest:
        raise UsageError(
            f"{alias(target)} has a stale {applied}; run "
            "`chezmoi apply ~/.config/work-sync/folders.json` there, then retry"
        )
    return check


def _find_orca_repo(repos: tuple[OrcaRepo, ...], path: Path) -> OrcaRepo | None:
    matches = [repo for repo in repos if repo.path == path]
    if len(matches) > 1:
        raise UsageError(f"duplicate Orca repository path: {path}")
    return matches[0] if matches else None


def _main_worktree(repo: OrcaRepo) -> WorktreePair:
    matches = [
        worktree
        for worktree in repo.worktrees
        if worktree.is_main and worktree.path == repo.path
    ]
    if len(matches) != 1:
        raise UsageError(f"Orca main worktree must match once: {repo.path}")
    return WorktreePair(matches[0], matches[0])


def _require_no_active_main(repo: OrcaRepo) -> None:
    main = _main_worktree(repo).source
    if main.active_agents:
        raise UsageError(
            f"active agent in main worktree {main.path}: "
            + ", ".join(main.active_agents)
        )


class Handoff:
    """Plan all external worktrees first, then perform a one-way handoff."""

    def __init__(self, runner: Runner, syncthing: Syncthing, orca: Orca) -> None:
        self.runner = runner
        self.syncthing = syncthing
        self.orca = orca

    def preflight(
        self,
        folders: tuple[Folder, ...],
        target: Host,
        *,
        timeout: int,
    ) -> HandoffPlan:
        """Validate every selected repository before the first mutation."""
        source = self.runner.local_host
        if source == target:
            raise UsageError("target is the current host")
        if not self.runner.reachable(target):
            raise UsageError(f"{self.runner.describe(target)} is unreachable over SSH")
        verify_manifest_copies(self.runner, (source, target))
        ids = self.syncthing.device_ids((source, target)) if folders else {}
        for folder in folders:
            self.syncthing.wait_idle(folder.id, timeout, ids)

        source_inventory = self.orca.inventory(source)
        target_inventory = self.orca.inventory(target)
        planned: list[FolderHandoff] = []
        for folder in folders:
            try:
                main = preflight_repository(
                    self.runner,
                    source,
                    folder.path(source),
                    target,
                    folder.path(target),
                    excludes=folder.ignore,
                    fallback_identity=folder.id,
                )
            except UsageError as error:
                raise UsageError(f"{folder.label} main: {error}") from error
            source_orca = _find_orca_repo(
                source_inventory.repos,
                folder.path(source),
            )
            target_orca = _find_orca_repo(
                target_inventory.repos,
                folder.path(target),
            )
            if (source_orca is None) != (target_orca is None):
                raise UsageError(
                    f"Orca registration differs for {folder.label}; "
                    "register the missing main repository first"
                )
            existing: list[tuple[WorktreePair, RepositoryPlan]] = []
            missing: list[MissingWorktree] = []
            if source_orca and target_orca:
                _require_no_active_main(source_orca)
                _require_no_active_main(target_orca)
                for pair in pair_worktrees(source_orca, target_orca):
                    if pair.target:
                        try:
                            external = preflight_repository(
                                self.runner,
                                source,
                                pair.source.path,
                                target,
                                pair.target.path,
                                excludes=(*folder.ignore, *folder.worktree_ignore),
                                allow_clean_target_difference=True,
                                fallback_identity=folder.id,
                            )
                        except UsageError as error:
                            raise UsageError(
                                f"{folder.label} ({pair.source.branch}): {error}"
                            ) from error
                        existing.append((pair, external))
                        continue
                    try:
                        source_state = preflight_missing_worktree(
                            self.runner,
                            source,
                            pair.source.path,
                            main.target,
                            fallback_identity=folder.id,
                        )
                    except UsageError as error:
                        raise UsageError(
                            f"{folder.label} ({pair.source.branch}): {error}"
                        ) from error
                    old_commit = main.target.branches.get(pair.source.branch)
                    missing.append(
                        MissingWorktree(
                            pair,
                            source_state,
                            old_commit,
                            old_commit or main.target.head,
                        )
                    )
            planned.append(
                FolderHandoff(
                    folder,
                    main,
                    source_orca,
                    target_orca,
                    tuple(existing),
                    tuple(missing),
                )
            )

        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        home = HOSTS[target].home
        return HandoffPlan(
            source,
            target,
            tuple(planned),
            home / ".local/state/work-sync/handoff" / stamp,
        )

    def execute(self, plan: HandoffPlan) -> tuple[HandoffResult, ...]:
        """Execute a validated handoff plan in folder order."""
        results: list[HandoffResult] = []
        for folder_plan in plan.folders:
            external = list(folder_plan.existing_worktrees)
            if folder_plan.missing_worktrees:
                assert folder_plan.target_orca is not None
            for missing in folder_plan.missing_worktrees:
                assert folder_plan.target_orca is not None
                created = self.orca.create_worktree(
                    plan.target,
                    folder_plan.target_orca,
                    missing.pair.source,
                    missing.base_ref,
                    existing_commit=missing.existing_commit,
                )
                created_plan = preflight_repository(
                    self.runner,
                    plan.source,
                    missing.pair.source.path,
                    plan.target,
                    created.path,
                    excludes=(
                        *folder_plan.folder.ignore,
                        *folder_plan.folder.worktree_ignore,
                    ),
                    allow_clean_target_difference=True,
                    fallback_identity=folder_plan.folder.id,
                )
                external.append(
                    (WorktreePair(missing.pair.source, created), created_plan)
                )

            for pair, worktree_plan in external:
                assert pair.target is not None
                recovery = (
                    plan.recovery_root
                    / folder_plan.folder.id
                    / pair.source.branch.replace("/", "__")
                )
                sync_worktree_files(
                    self.runner,
                    plan.source,
                    pair.source.path,
                    plan.target,
                    pair.target.path,
                    recovery,
                    excludes=(
                        *folder_plan.folder.ignore,
                        *folder_plan.folder.worktree_ignore,
                    ),
                    dry_run=False,
                )
                rebuild_index(self.runner, worktree_plan)
                assert folder_plan.target_orca is not None
                self.orca.verify_worktree(
                    plan.target,
                    folder_plan.target_orca.path,
                    pair.target,
                )
            results.append(
                HandoffResult(
                    folder_plan.folder.label,
                    len(external),
                    plan.recovery_root,
                )
            )
        return tuple(results)

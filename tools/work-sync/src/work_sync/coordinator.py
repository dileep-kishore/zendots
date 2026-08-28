"""Cross-machine handoff planning and execution."""

from __future__ import annotations

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
    transfer_refs,
)
from .manifest import Folder, Host, UsageError
from .syncthing import Syncthing
from .system import Runner

MANIFEST_PATHS: dict[Host, tuple[Path, Path]] = {
    "mac": (
        Path("/Users/dkishore/zendots/private_dot_config/work-sync/folders.json"),
        Path("/Users/dkishore/.config/work-sync/folders.json"),
    ),
    "tsuki": (
        Path("/home/dileep/zendots/private_dot_config/work-sync/folders.json"),
        Path("/home/dileep/.config/work-sync/folders.json"),
    ),
}


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
        if host == "mac"
        else ["sha256sum", str(path)]
    )
    try:
        return runner.run(host, command).split()[0]
    except (IndexError, OSError) as error:
        raise UsageError(f"cannot hash manifest on {host}: {path}") from error


def verify_manifest_copies(runner: Runner) -> str:
    """Require source and applied private manifests to match on both hosts."""
    digests = {
        (host, path): _digest(runner, host, path)
        for host, paths in MANIFEST_PATHS.items()
        for path in paths
    }
    unique = set(digests.values())
    if len(unique) != 1:
        details = ", ".join(
            f"{host}:{path}={digest[:12]}"
            for (host, path), digest in digests.items()
        )
        raise UsageError(
            "private manifests differ; run the scoped chezmoi apply on the "
            f"stale host ({details})"
        )
    return unique.pop()


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
    """Plan all repositories first, then perform a one-way handoff."""

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
        verify_manifest_copies(self.runner)
        for folder in folders:
            self.syncthing.wait_idle(folder.id, timeout)

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
                                excludes=folder.ignore,
                                allow_clean_target_difference=True,
                                fallback_identity=folder.id,
                            )
                        except UsageError as error:
                            raise UsageError(
                                f"{folder.label} [{pair.source.branch}]: {error}"
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
                            f"{folder.label} [{pair.source.branch}]: {error}"
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
        home = Path("/Users/dkishore" if target == "mac" else "/home/dileep")
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
                    excludes=folder_plan.folder.ignore,
                    allow_clean_target_difference=True,
                    fallback_identity=folder_plan.folder.id,
                )
                external.append(
                    (WorktreePair(missing.pair.source, created), created_plan)
                )

            transfer_refs(self.runner, folder_plan.main)
            rebuild_index(self.runner, folder_plan.main)
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
                    excludes=folder_plan.folder.ignore,
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

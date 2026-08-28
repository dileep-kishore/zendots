"""Explicit Git state handoff without copying .git directories."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import urlparse

from .manifest import Host, UsageError
from .syncthing import LOCAL_STATE_IGNORES
from .system import Runner

TREE_EXCLUDES = (
    "/.git",
    "/.stignore",
    "/.stfolder/",
    *LOCAL_STATE_IGNORES,
)


@dataclass(frozen=True)
class RepoState:
    """Git state required to validate and reproduce a checkout."""

    host: Host
    path: Path
    origin: str
    branch: str
    head: str
    branches: dict[str, str]
    staged_patch: str
    dirty: str


@dataclass(frozen=True)
class RepositoryPlan:
    """Validated source and target state for one repository."""

    runner: Runner
    source: RepoState
    target: RepoState


@dataclass(frozen=True)
class OrcaWorktree:
    """One Orca-managed checkout."""

    id: str
    repo_id: str
    path: Path
    branch: str
    display_name: str
    is_main: bool
    active_agents: tuple[str, ...]


@dataclass(frozen=True)
class OrcaRepo:
    """One Orca repository and its worktrees."""

    id: str
    path: Path
    display_name: str
    identity: str | None
    worktrees: tuple[OrcaWorktree, ...]


@dataclass(frozen=True)
class OrcaInventory:
    """Validated Orca repository inventory."""

    repos: tuple[OrcaRepo, ...]


@dataclass(frozen=True)
class WorktreePair:
    """A source worktree and its existing or missing target."""

    source: OrcaWorktree
    target: OrcaWorktree | None


def _orca_result(payload: Mapping[str, object], key: str) -> list[dict[str, object]]:
    if payload.get("ok") is not True or not isinstance(payload.get("result"), dict):
        raise UsageError("Orca returned an unsuccessful response")
    result = payload["result"]
    assert isinstance(result, dict)
    items = result.get(key)
    if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
        raise UsageError(f"Orca response is missing {key}")
    return items


def parse_orca_inventory(
    repos_payload: Mapping[str, object],
    worktrees_payload: Mapping[str, object],
) -> OrcaInventory:
    """Parse the installed Orca CLI's JSON envelopes."""
    worktrees_by_repo: dict[str, list[OrcaWorktree]] = {}
    for raw in _orca_result(worktrees_payload, "worktrees"):
        repo_id = str(raw.get("repoId", ""))
        branch = str(raw.get("branch", "")).removeprefix("refs/heads/")
        if not repo_id or not branch:
            continue
        agents = raw.get("agents")
        if not isinstance(agents, list):
            agents = []
        active_agents = tuple(
            str(agent.get("agentType", "agent"))
            for agent in agents
            if isinstance(agent, dict)
            and agent.get("state") not in {"done", "idle", "stopped"}
        )
        worktree = OrcaWorktree(
            id=str(raw.get("worktreeId", "")),
            repo_id=repo_id,
            path=Path(str(raw.get("path", ""))),
            branch=branch,
            display_name=str(raw.get("displayName") or branch),
            is_main=bool(raw.get("isMainWorktree")),
            active_agents=active_agents,
        )
        worktrees_by_repo.setdefault(repo_id, []).append(worktree)
    repos: list[OrcaRepo] = []
    for raw in _orca_result(repos_payload, "repos"):
        repo_id = str(raw.get("id", ""))
        remote = raw.get("gitRemoteIdentity")
        identity = (
            str(remote.get("canonicalKey"))
            if isinstance(remote, dict) and remote.get("canonicalKey")
            else None
        )
        repos.append(
            OrcaRepo(
                id=repo_id,
                path=Path(str(raw.get("path", ""))),
                display_name=str(raw.get("displayName", "")),
                identity=identity,
                worktrees=tuple(worktrees_by_repo.get(repo_id, [])),
            )
        )
    return OrcaInventory(tuple(repos))


def pair_worktrees(source: OrcaRepo, target: OrcaRepo) -> tuple[WorktreePair, ...]:
    """Pair external worktrees by branch while preserving target paths."""
    Orca.require_idle_agents(source)
    Orca.require_idle_agents(target)
    target_by_branch: dict[str, OrcaWorktree] = {}
    for worktree in target.worktrees:
        if worktree.is_main:
            continue
        if worktree.branch in target_by_branch:
            raise UsageError(f"duplicate target worktree branch: {worktree.branch}")
        target_by_branch[worktree.branch] = worktree
    pairs: list[WorktreePair] = []
    for worktree in source.worktrees:
        if worktree.is_main:
            continue
        target_worktree = target_by_branch.get(worktree.branch)
        pairs.append(WorktreePair(worktree, target_worktree))
    return tuple(pairs)


class Orca:
    """Read and update Orca-managed repository state."""

    def __init__(self, runner: Runner) -> None:
        self.runner = runner

    @staticmethod
    def _binary(host: Host) -> str:
        return "orca" if host == "mac" else "orca-ide"

    def _call(self, host: Host, *args: str) -> dict[str, object]:
        try:
            payload = json.loads(
                self.runner.run(host, [self._binary(host), *args, "--json"])
            )
        except (json.JSONDecodeError, subprocess.CalledProcessError) as error:
            raise UsageError(f"Orca command failed on {host}: {' '.join(args)}") from error
        if not isinstance(payload, dict) or payload.get("ok") is not True:
            raise UsageError(f"Orca command failed on {host}: {' '.join(args)}")
        return payload

    def inventory(self, host: Host) -> OrcaInventory:
        """Return the live Orca repository and worktree inventory."""
        repos = self._call(host, "repo", "list")
        worktrees = self._call(host, "worktree", "ps")
        return parse_orca_inventory(repos, worktrees)

    @staticmethod
    def repo_for_path(inventory: OrcaInventory, path: Path) -> OrcaRepo:
        """Find exactly one Orca repository by its main checkout path."""
        matches = [repo for repo in inventory.repos if repo.path == path]
        if len(matches) != 1:
            raise UsageError(f"Orca repository path must match once: {path}")
        return matches[0]

    @staticmethod
    def require_idle_agents(repo: OrcaRepo) -> None:
        """Reject any worktree in a repository with a running agent."""
        active = [
            f"{worktree.branch} ({', '.join(worktree.active_agents)})"
            for worktree in repo.worktrees
            if worktree.active_agents
        ]
        if active:
            raise UsageError(
                f"active agent in Orca repository {repo.display_name}: "
                + ", ".join(active)
            )

    def create_worktree(
        self,
        host: Host,
        repo: OrcaRepo,
        source: OrcaWorktree,
        base_ref: str,
        existing_commit: str | None = None,
    ) -> OrcaWorktree:
        """Create one missing target worktree with setup hooks skipped."""
        ref = f"refs/heads/{source.branch}"
        if existing_commit:
            _git(self.runner, host, repo.path, "update-ref", "-d", ref, existing_commit)
        try:
            payload = self._call(
                host,
                "worktree",
                "create",
                "--repo",
                f"id:{repo.id}",
                "--name",
                source.branch,
                "--base-branch",
                base_ref,
                "--setup",
                "skip",
                "--no-parent",
            )
        except Exception:
            if existing_commit:
                _git(self.runner, host, repo.path, "update-ref", ref, existing_commit)
            raise
        result = payload.get("result")
        raw = result.get("worktree") if isinstance(result, dict) else None
        if not isinstance(raw, dict):
            refreshed = self.repo_for_path(self.inventory(host), repo.path)
            matches = [
                worktree
                for worktree in refreshed.worktrees
                if worktree.branch == source.branch
            ]
            if len(matches) != 1:
                raise UsageError(
                    f"Orca did not return created worktree: {source.branch}"
                )
            return matches[0]
        created = OrcaWorktree(
            id=str(raw.get("id") or raw.get("worktreeId") or ""),
            repo_id=str(raw.get("repoId") or repo.id),
            path=Path(str(raw.get("path", ""))),
            branch=str(raw.get("branch", "")).removeprefix("refs/heads/"),
            display_name=str(raw.get("displayName") or source.display_name),
            is_main=bool(raw.get("isMainWorktree")),
            active_agents=(),
        )
        if created.branch != source.branch:
            _git(
                self.runner,
                host,
                created.path,
                "branch",
                "-m",
                source.branch,
            )
            created = replace(created, branch=source.branch)
            self._call(
                host,
                "worktree",
                "set",
                "--worktree",
                f"path:{created.path}",
                "--display-name",
                source.display_name,
            )
        return created

    def verify_worktree(
        self,
        host: Host,
        repo_path: Path,
        worktree: OrcaWorktree,
    ) -> None:
        """Verify a worktree still has the expected ID, path, and branch."""
        repo = self.repo_for_path(self.inventory(host), repo_path)
        if not any(
            current.id == worktree.id
            and current.path == worktree.path
            and current.branch == worktree.branch
            for current in repo.worktrees
        ):
            raise UsageError(f"Orca verification failed: {worktree.path}")


def _rsync_endpoints(
    source_host: Host,
    source_path: Path,
    target_host: Host,
    target_path: Path,
) -> tuple[Host, tuple[str, str]]:
    if source_host == "tsuki" and target_host == "mac":
        return "mac", (f"tsuki:{source_path}/", f"{target_path}/")
    destination = f"{target_path}/"
    if target_host != source_host:
        alias = "tsuki" if target_host == "tsuki" else "macmini"
        destination = f"{alias}:{destination}"
    return source_host, (f"{source_path}/", destination)


def sync_worktree_files(
    runner: Runner,
    source_host: Host,
    source_path: Path,
    target_host: Host,
    target_path: Path,
    recovery_path: Path,
    *,
    excludes: tuple[str, ...],
    dry_run: bool,
) -> tuple[str, ...]:
    """Mirror external worktree files and retain replaced target files."""
    if source_host != runner.local_host:
        raise UsageError("handoff source must be the current host")
    rsync_host, endpoints = _rsync_endpoints(
        source_host,
        source_path,
        target_host,
        target_path,
    )
    command = [
        "rsync",
        "-rlic",
        "--executability",
        "--no-perms",
        "--no-owner",
        "--no-group",
        "--out-format=%i %n%L",
    ]
    patterns = (*TREE_EXCLUDES, *excludes)
    include_rules: list[str] = []
    for pattern in patterns:
        if not pattern.startswith("!"):
            continue
        included = pattern[1:]
        parts = included.strip("/").split("/")[:-1]
        for index in range(1, len(parts) + 1):
            parent = "/" + "/".join(parts[:index]) + "/"
            if parent not in include_rules:
                include_rules.append(parent)
        include_rules.append(included)
    command.extend(f"--include={pattern}" for pattern in include_rules)
    included_paths = [pattern.strip("/") for pattern in include_rules]
    for pattern in patterns:
        if pattern.startswith("!"):
            continue
        bare = pattern.rstrip("/").strip("/")
        if any(path.startswith(bare + "/") for path in included_paths):
            pattern = pattern.rstrip("/") + "/***"
        command.append(f"--exclude={pattern}")
    deletion_scan = runner.run(
        rsync_host,
        [*command, "--dry-run", "--delete-after", *endpoints],
    )
    if dry_run:
        return tuple(line for line in deletion_scan.splitlines() if line)

    runner.run(target_host, ["mkdir", "-p", str(recovery_path)])
    deletion_paths: list[Path] = []
    for line in deletion_scan.splitlines():
        if not line.startswith("*deleting "):
            continue
        relative = Path(line.removeprefix("*deleting ").lstrip().rstrip("/"))
        if relative.is_absolute() or ".." in relative.parts:
            raise UsageError(f"unsafe rsync deletion path: {relative}")
        deletion_paths.append(relative)
    minimal_deletions = [
        path
        for path in sorted(set(deletion_paths), key=lambda item: len(item.parts))
        if not any(parent in deletion_paths for parent in path.parents)
    ]
    if len(minimal_deletions) > 10_000:
        raise UsageError("refusing more than 10000 worktree deletions")
    for relative in minimal_deletions:
        source_item = target_path / relative
        recovery_item = recovery_path / relative
        runner.run(target_host, ["mkdir", "-p", str(recovery_item.parent)])
        runner.run(
            target_host,
            ["cp", "-pR", str(source_item), str(recovery_item)],
        )

    updated = runner.run(
        rsync_host,
        [
            *command,
            "--backup",
            f"--backup-dir={recovery_path}",
            *endpoints,
        ],
    )
    deleted = runner.run(
        rsync_host,
        [*command, "--delete-after", *endpoints],
    )
    return tuple(
        line for line in (*updated.splitlines(), *deleted.splitlines()) if line
    )


def _git(runner: Runner, host: Host, repo: Path, *args: str) -> str:
    return runner.run(host, ["git", "-C", str(repo), *args])


def _normalize_remote(url: str) -> str:
    value = url.strip()
    scp_match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", value)
    if scp_match and "://" not in value:
        host, path = scp_match.groups()
        return f"{host.lower()}/{path.removesuffix('.git').strip('/')}"
    parsed = urlparse(value)
    if parsed.scheme and parsed.hostname:
        path = parsed.path.removesuffix(".git").strip("/")
        return f"{parsed.hostname.lower()}/{path}"
    return "local:" + str(Path(value).expanduser().resolve())


def canonical_origin(runner: Runner, host: Host, repo: Path) -> str:
    """Return a protocol-independent identity for the origin fetch URL."""
    try:
        url = _git(runner, host, repo, "remote", "get-url", "origin")
    except subprocess.CalledProcessError as error:
        raise UsageError(f"missing origin remote: {repo}") from error
    return _normalize_remote(url)


def _branches(runner: Runner, host: Host, repo: Path) -> dict[str, str]:
    output = _git(
        runner,
        host,
        repo,
        "for-each-ref",
        "--format=%(refname:short)%00%(objectname)",
        "refs/heads",
    )
    branches: dict[str, str] = {}
    for line in output.splitlines():
        if not line:
            continue
        name, commit = line.split("\0", 1)
        branches[name] = commit
    return branches


def _exists(runner: Runner, host: Host, path: Path) -> bool:
    try:
        runner.run(host, ["test", "-e", str(path)])
    except subprocess.CalledProcessError:
        return False
    return True


def _operation_in_progress(runner: Runner, host: Host, repo: Path) -> str | None:
    git_dir = Path(_git(runner, host, repo, "rev-parse", "--absolute-git-dir"))
    for name in (
        "MERGE_HEAD",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "rebase-merge",
        "rebase-apply",
        "BISECT_LOG",
    ):
        if _exists(runner, host, git_dir / name):
            return name
    for name in (
        "index.lock",
        "HEAD.lock",
        "packed-refs.lock",
        "config.lock",
        "shallow.lock",
    ):
        if _exists(runner, host, git_dir / name):
            return name
    refs = git_dir / "refs"
    if _exists(runner, host, refs):
        locks = runner.run(
            host,
            ["find", str(refs), "-name", "*.lock", "-print", "-quit"],
        )
        if locks:
            return str(Path(locks).relative_to(git_dir))
    if _git(runner, host, repo, "ls-files", "-u"):
        return "unmerged index"
    return None


def inspect_repo(
    runner: Runner,
    host: Host,
    repo: Path,
    *,
    fallback_identity: str | None = None,
) -> RepoState:
    """Inspect a repository without changing it."""
    try:
        branch = _git(runner, host, repo, "branch", "--show-current")
        head = _git(runner, host, repo, "rev-parse", "HEAD")
    except subprocess.CalledProcessError as error:
        raise UsageError(f"not a Git repository on {host}: {repo}") from error
    if not branch:
        raise UsageError(f"detached HEAD on {host}: {repo}")
    operation = _operation_in_progress(runner, host, repo)
    if operation:
        raise UsageError(f"Git operation or lock on {host}: {repo} ({operation})")
    try:
        origin = canonical_origin(runner, host, repo)
    except UsageError:
        if not fallback_identity:
            raise
        origin = f"manifest:{fallback_identity}"
    return RepoState(
        host=host,
        path=repo,
        origin=origin,
        branch=branch,
        head=head,
        branches=_branches(runner, host, repo),
        staged_patch=_git(runner, host, repo, "diff", "--cached", "--binary", "HEAD", "--"),
        dirty=_git(runner, host, repo, "status", "--porcelain=v1", "--untracked-files=all"),
    )


def _require_fast_forward(
    runner: Runner,
    source: RepoState,
    branch: str,
    target_commit: str,
    source_commit: str,
) -> None:
    if target_commit == source_commit:
        return
    try:
        _git(
            runner,
            source.host,
            source.path,
            "merge-base",
            "--is-ancestor",
            target_commit,
            source_commit,
        )
    except subprocess.CalledProcessError as error:
        raise UsageError(
            f"diverged branch {branch}: "
            f"{target_commit[:12]} is not behind {source_commit[:12]}"
        ) from error


def _tree_changes(
    runner: Runner,
    source: RepoState,
    target: RepoState,
    excludes: tuple[str, ...],
    *,
    delete: bool,
) -> tuple[str, ...]:
    rsync_host, endpoints = _rsync_endpoints(
        source.host,
        source.path,
        target.host,
        target.path,
    )
    command = [
        "rsync",
        "-rlinc",
        "--executability",
        "--out-format=%i %n%L",
    ]
    if delete:
        command.append("--delete")
    for pattern in (*TREE_EXCLUDES, *excludes):
        if not pattern.startswith("!"):
            command.append(f"--exclude={pattern}")
    command.extend(endpoints)
    output = runner.run(rsync_host, command)
    return tuple(
        line for line in output.splitlines() if line and not line.startswith(".")
    )


def preflight_repository(
    runner: Runner,
    source_host: Host,
    source_path: Path,
    target_host: Host,
    target_path: Path,
    *,
    excludes: tuple[str, ...] = (),
    allow_clean_target_difference: bool = False,
    allow_branch_switch: bool = False,
    fallback_identity: str | None = None,
) -> RepositoryPlan:
    """Validate one source and target repository without changing either."""
    source = inspect_repo(
        runner,
        source_host,
        source_path,
        fallback_identity=fallback_identity,
    )
    target = inspect_repo(
        runner,
        target_host,
        target_path,
        fallback_identity=fallback_identity,
    )
    if source.origin != target.origin:
        raise UsageError(
            f"origin mismatch: {source.origin} != {target.origin}"
        )
    if source.branch != target.branch and not allow_branch_switch:
        raise UsageError(
            f"checked-out branches differ: {source.branch} != {target.branch}"
        )
    if source.branch != target.branch:
        checked_out = _git(
            runner,
            target.host,
            target.path,
            "for-each-ref",
            "--format=%(worktreepath)",
            f"refs/heads/{source.branch}",
        )
        if checked_out:
            raise UsageError(
                f"target branch is checked out elsewhere: "
                f"{source.branch} ({checked_out})"
            )
    for branch, source_commit in source.branches.items():
        target_commit = target.branches.get(branch)
        if target_commit:
            _require_fast_forward(
                runner,
                source,
                branch,
                target_commit,
                source_commit,
            )
    differences = _tree_changes(
        runner,
        source,
        target,
        excludes,
        delete=True,
    )
    target_only = ()
    if differences and allow_clean_target_difference and target.dirty:
        target_only = _tree_changes(
            runner,
            target,
            source,
            excludes,
            delete=False,
        )
    safe_external_update = allow_clean_target_difference and (
        not target.dirty or not target_only
    )
    if differences and not safe_external_update:
        preview = ", ".join(differences[:3])
        raise UsageError(f"target files differ from source: {preview}")
    return RepositoryPlan(runner, source, target)


def preflight_missing_worktree(
    runner: Runner,
    source_host: Host,
    source_path: Path,
    target_repo: RepoState,
    *,
    fallback_identity: str | None = None,
) -> RepoState:
    """Validate the source branch for a worktree missing on the target."""
    source = inspect_repo(
        runner,
        source_host,
        source_path,
        fallback_identity=fallback_identity,
    )
    if source.origin != target_repo.origin:
        raise UsageError(
            f"origin mismatch: {source.origin} != {target_repo.origin}"
        )
    if source.branch == target_repo.branch:
        raise UsageError(
            f"worktree layout conflict on target branch: {source.branch}"
        )
    base_commit = target_repo.branches.get(source.branch, target_repo.head)
    _require_fast_forward(
        runner,
        source,
        source.branch,
        base_commit,
        source.head,
    )
    return source


def _source_remote(source: RepoState, target: RepoState) -> str:
    if source.host == target.host:
        return str(source.path)
    alias = "macmini" if source.host == "mac" else "tsuki"
    return f"{alias}:{source.path}"


def _cleanup_incoming(plan: RepositoryPlan) -> None:
    refs = _git(
        plan.runner,
        plan.target.host,
        plan.target.path,
        "for-each-ref",
        "--format=%(refname)",
        "refs/work-sync/incoming",
    )
    for ref in refs.splitlines():
        if ref:
            _git(plan.runner, plan.target.host, plan.target.path, "update-ref", "-d", ref)


def transfer_refs(runner: Runner, plan: RepositoryPlan) -> None:
    """Transfer every source branch without deleting target-only branches."""
    source = plan.source
    target = plan.target
    refspec = "+refs/heads/*:refs/work-sync/incoming/*"
    _git(
        runner,
        target.host,
        target.path,
        "fetch",
        "--no-tags",
        "--no-write-fetch-head",
        _source_remote(source, target),
        refspec,
    )
    try:
        for branch, source_commit in source.branches.items():
            incoming = _git(
                runner,
                target.host,
                target.path,
                "rev-parse",
                f"refs/work-sync/incoming/{branch}",
            )
            if incoming != source_commit:
                raise UsageError(f"fetched branch changed during handoff: {branch}")
            ref = f"refs/heads/{branch}"
            target_commit = target.branches.get(branch)
            args = ["update-ref", ref, source_commit]
            if target_commit:
                args.append(target_commit)
            _git(runner, target.host, target.path, *args)
    finally:
        _cleanup_incoming(plan)


def rebuild_index(runner: Runner, plan: RepositoryPlan) -> None:
    """Reproduce one source checkout's staged state on its target checkout."""
    source = plan.source
    target = plan.target
    if source.branch != target.branch:
        _git(
            runner,
            target.host,
            target.path,
            "symbolic-ref",
            "HEAD",
            f"refs/heads/{source.branch}",
        )
    _git(
        runner,
        target.host,
        target.path,
        "reset",
        "-q",
        "--mixed",
        source.head,
    )
    if source.staged_patch:
        runner.run(
            target.host,
            [
                "git",
                "-C",
                str(target.path),
                "apply",
                "--cached",
                "--binary",
                "-",
            ],
            input_text=source.staged_patch + "\n",
        )
    actual_head = _git(runner, target.host, target.path, "rev-parse", "HEAD")
    actual_patch = _git(
        runner,
        target.host,
        target.path,
        "diff",
        "--cached",
        "--binary",
        "HEAD",
        "--",
    )
    if actual_head != source.head or actual_patch != source.staged_patch:
        raise UsageError(f"Git verification failed: {target.path}")


def transfer_git_state(runner: Runner, plan: RepositoryPlan) -> None:
    """Transfer source branches and index state into a validated target."""
    transfer_refs(runner, plan)
    rebuild_index(runner, plan)

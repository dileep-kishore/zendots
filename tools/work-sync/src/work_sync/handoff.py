"""Explicit Git state handoff without copying .git directories."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .manifest import Host, UsageError
from .system import Runner

TREE_EXCLUDES = (
    "/.git",
    "/.stignore",
    ".DS_Store",
    "._*",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "node_modules/",
    ".claude/worktrees/",
    ".serena/cache/",
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


@dataclass(frozen=True)
class RepositoryPlan:
    """Validated source and target state for one repository."""

    runner: Runner
    source: RepoState
    target: RepoState


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
    locks = runner.run(
        host,
        ["find", str(git_dir), "-name", "*.lock", "-print", "-quit"],
    )
    if locks:
        return Path(locks).name
    if _git(runner, host, repo, "ls-files", "-u"):
        return "unmerged index"
    return None


def inspect_repo(runner: Runner, host: Host, repo: Path) -> RepoState:
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
    return RepoState(
        host=host,
        path=repo,
        origin=canonical_origin(runner, host, repo),
        branch=branch,
        head=head,
        branches=_branches(runner, host, repo),
        staged_patch=_git(runner, host, repo, "diff", "--cached", "--binary", "HEAD", "--"),
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


def _working_tree_changes(
    runner: Runner,
    source: RepoState,
    target: RepoState,
    excludes: tuple[str, ...],
) -> tuple[str, ...]:
    if source.host != runner.local_host:
        raise UsageError("handoff source must be the current host")
    destination = str(target.path) + "/"
    if target.host != runner.local_host:
        alias = "tsuki" if target.host == "tsuki" else "macmini"
        destination = f"{alias}:{destination}"
    command = [
        "rsync",
        "-rlinc",
        "--delete",
        "--executability",
        "--out-format=%i %n%L",
    ]
    for pattern in (*TREE_EXCLUDES, *excludes):
        if not pattern.startswith("!"):
            command.append(f"--exclude={pattern}")
    command.extend((str(source.path) + "/", destination))
    output = runner.run(source.host, command)
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
) -> RepositoryPlan:
    """Validate one source and target repository without changing either."""
    source = inspect_repo(runner, source_host, source_path)
    target = inspect_repo(runner, target_host, target_path)
    if source.origin != target.origin:
        raise UsageError(
            f"origin mismatch: {source.origin} != {target.origin}"
        )
    if source.branch != target.branch:
        raise UsageError(
            f"checked-out branches differ: {source.branch} != {target.branch}"
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
    differences = _working_tree_changes(
        runner,
        source,
        target,
        excludes,
    )
    if differences:
        preview = ", ".join(differences[:3])
        raise UsageError(f"target files differ from source: {preview}")
    return RepositoryPlan(runner, source, target)


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


def transfer_git_state(runner: Runner, plan: RepositoryPlan) -> None:
    """Transfer source branch and index state into a validated target."""
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
    finally:
        _cleanup_incoming(plan)

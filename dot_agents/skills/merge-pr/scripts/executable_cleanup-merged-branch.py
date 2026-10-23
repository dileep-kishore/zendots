#!/usr/bin/env python3
"""Remove the worktree, local branch, and remote branch of a merged PR.

Refuses anything it cannot prove is safe: a dirty worktree, a branch tip that
is neither in the default branch nor the merged PR's head, a remote branch
that open PRs still target, or a branch checked out in the main checkout.
Then fast-forwards the main checkout when it is on the default branch with no
tracked changes, and prints `skipped-fast-forward` with the reason otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

EXAMPLES = """examples:
  cleanup-merged-branch.py --branch feat/x --dry-run
  cleanup-merged-branch.py --branch feat/x --pr-head 1a2b3c4d
  cleanup-merged-branch.py --repo ~/code/app --branch fix/y --keep-remote
"""


def run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise SystemExit(f"error: {' '.join(args)}: {result.stderr.strip() or result.stdout.strip()}")
    return result


def git(cwd: Path, *args: str, check: bool = True) -> str:
    return run(["git", *args], cwd, check).stdout.strip()


def main_checkout(start: Path) -> Path:
    # The first `worktree list` entry is the main checkout, even when run from a linked worktree.
    first = git(start, "worktree", "list", "--porcelain").splitlines()[0]
    return Path(first.removeprefix("worktree "))


def worktrees_on(root: Path, branch: str) -> list[Path]:
    paths, current = [], None
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            current = Path(line.removeprefix("worktree "))
        elif line == f"branch refs/heads/{branch}" and current is not None:
            paths.append(current)
    return paths


def default_branch(root: Path, remote: str) -> str:
    ref = git(root, "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD", check=False)
    if ref:
        return ref.removeprefix(f"refs/remotes/{remote}/")
    out = git(root, "ls-remote", "--symref", remote, "HEAD")
    for line in out.splitlines():
        if line.startswith("ref: refs/heads/"):
            return line.split()[1].removeprefix("refs/heads/")
    raise SystemExit(f"error: cannot resolve the default branch of {remote}")


def open_prs_based_on(root: Path, branch: str) -> list[str] | None:
    if shutil.which("gh") is None:
        return None
    result = run(["gh", "pr", "list", "--base", branch, "--state", "open", "--json", "number", "-q", ".[].number"], root, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.split()


def orca_owns(path: Path) -> bool | None:
    """True or False when Orca answers, None when it cannot be asked."""
    if shutil.which("orca") is None:
        return False
    result = subprocess.run(
        ["orca", "worktree", "show", "--worktree", f"path:{path}", "--json"], text=True, capture_output=True, check=False
    )
    try:
        reply = json.loads(result.stdout)
    except json.JSONDecodeError:
        reply = {}
    if reply.get("ok") is True:
        return True
    code = (reply.get("error") or {}).get("code")
    if code in (None, "runtime_unavailable"):
        return None
    return False


def remote_tip_of(root: Path, remote: str, branch: str) -> str:
    # An exact refname, because ls-remote patterns also match archive/<branch>.
    for line in git(root, "ls-remote", remote, f"refs/heads/{branch}").splitlines():
        sha, _, ref = line.partition("\t")
        if ref == f"refs/heads/{branch}":
            return sha
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--branch", required=True, help="head branch of the merged PR")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="any checkout of the repository (default: cwd)")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--pr-head", help="merged PR's headRefOid; proves a squash or rebase merge")
    parser.add_argument("--keep-remote", action="store_true", help="leave the remote branch alone")
    parser.add_argument("--no-orca", action="store_true", help="remove worktrees with git even if Orca manages them")
    parser.add_argument("--dry-run", action="store_true", help="print the plan; skips the fetch, so merge proof uses cached refs")
    opts = parser.parse_args()

    root = main_checkout(opts.repo.expanduser().resolve())
    branch, remote = opts.branch, opts.remote
    if opts.dry_run:
        print(f"would-run git fetch --quiet --prune {remote}")
    else:
        git(root, "fetch", "--quiet", "--prune", remote)
    base = default_branch(root, remote)
    if branch == base:
        raise SystemExit(f"error: refusing to delete the default branch {base}")

    local_tip = git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}^{{commit}}", check=False)
    remote_tip = remote_tip_of(root, remote, branch)
    if not (local_tip or remote_tip or worktrees_on(root, branch)):
        print(f"already-clean {branch}")
        return 0

    def merged(sha: str) -> bool:
        if opts.pr_head and (sha.startswith(opts.pr_head) or opts.pr_head.startswith(sha)):
            return True
        return run(["git", "merge-base", "--is-ancestor", sha, f"{remote}/{base}"], root, check=False).returncode == 0

    for label, tip in (("local", local_tip), ("remote", remote_tip)):
        if tip and not merged(tip):
            raise SystemExit(
                f"error: {label} {branch} at {tip[:9]} is not in {remote}/{base} and is not --pr-head; it holds unmerged commits"
            )

    plan: list[tuple[str, list[str], str]] = []
    for path in worktrees_on(root, branch):
        if path == root:
            raise SystemExit(f"error: {branch} is checked out in the main checkout {root}; switch it to {base} first")
        dirty = git(path, "status", "--porcelain", "--untracked-files=all")
        if dirty:
            raise SystemExit(f"error: {path} has uncommitted changes:\n{dirty}")
        owned = False if opts.no_orca else orca_owns(path)
        if owned is None:
            print(f"warning: Orca is not running; if it tracks {path}, its sidebar may keep a stale entry")
        if owned:
            plan.append(("removed-worktree", ["orca", "worktree", "rm", "--worktree", f"path:{path}", "--json"], str(path)))
        else:
            plan.append(("removed-worktree", ["git", "worktree", "remove", str(path)], str(path)))
    plan.append(("pruned-worktrees", ["git", "worktree", "prune"], ""))
    if local_tip:
        # Deletes only if the tip is still the commit proven merged above; worktree removal already freed the ref.
        plan.append(("deleted-branch", ["git", "update-ref", "-d", f"refs/heads/{branch}", local_tip], branch))
    if remote_tip and not opts.keep_remote:
        children = open_prs_based_on(root, branch)
        if children is None:
            raise SystemExit("error: cannot list PRs based on this branch (gh missing or failing); rerun with --keep-remote")
        if children:
            raise SystemExit(f"error: open PRs {', '.join('#' + c for c in children)} target {branch}; retarget them to {base} first")
        lease = f"--force-with-lease=refs/heads/{branch}:{remote_tip}"
        plan.append(("deleted-remote-branch", ["git", "push", "--quiet", lease, remote, f":refs/heads/{branch}"], f"{remote}/{branch}"))

    for label, cmd, target in plan:
        if opts.dry_run:
            print(f"would-run {' '.join(cmd)}")
            continue
        if label == "deleted-branch":
            if not git(root, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", check=False):
                print(f"{label} {target} (already gone)")
                continue
            if worktrees_on(root, branch):
                raise SystemExit(f"error: {branch} is still checked out in a worktree; not deleting it")
        run(cmd, root)
        print(f"{label} {target}".rstrip())

    # A bare repository has no checkout to update.
    if not opts.dry_run and git(root, "rev-parse", "--is-bare-repository") != "true":
        if git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False) != base:
            print(f"skipped-fast-forward {root}: not on {base}")
        elif git(root, "status", "--porcelain", "--untracked-files=no"):
            print(f"skipped-fast-forward {root}: uncommitted changes to tracked files")
        else:
            before = git(root, "rev-parse", "HEAD")
            result = run(["git", "merge", "--ff-only", "--quiet", f"{remote}/{base}"], root, check=False)
            if result.returncode != 0:
                # Git lists the blocking paths on the lines after its first.
                lines = (result.stderr + result.stdout).splitlines()
                detail = " ".join(line.strip() for line in lines if line.strip()) or "git merge --ff-only failed"
                print(f"skipped-fast-forward {root}: {detail}")
            elif git(root, "rev-parse", "HEAD") != before:
                print(f"fast-forwarded {root} to {remote}/{base}")
    print(f"main-checkout {root}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
    sys.exit(main())

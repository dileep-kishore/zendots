"""Typer interface for work-sync."""

from __future__ import annotations

import fcntl
import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from .conflicts import apply_conflicts, scan_conflicts
from .coordinator import Handoff, HandoffPlan, verify_manifest_copies
from .handoff import Orca
from .manifest import Host, UsageError, detect_host, load_manifest
from .syncthing import BootstrapPlan, Syncthing, managed_patterns
from .system import Runner

ROOT_EPILOG = """
Target means the receiving machine.

Examples:

    work-sync bootstrap QBio_perspective
    work-sync bootstrap QBio_perspective --apply
    work-sync handoff tsuki
    work-sync handoff tsuki --dry-run
"""

BOOTSTRAP_EPILOG = """
Examples:

    work-sync bootstrap QBio_perspective
    work-sync bootstrap QBio_perspective --apply
"""

HANDOFF_EPILOG = """
Examples:

    work-sync handoff tsuki
    work-sync handoff macmini
    work-sync handoff tsuki --folder LifeOS
    work-sync handoff macmini --folder LifeOS --folder CommScores
    work-sync handoff tsuki --dry-run
"""

CONFLICTS_EPILOG = """
Examples:

    work-sync conflicts .
    work-sync conflicts /path/to/project --apply
"""

app = typer.Typer(
    name="work-sync",
    help="Configure project sync and hand external Orca worktrees to the other machine.",
    epilog=ROOT_EPILOG,
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode="markdown",
)
console = Console()
DEFAULT_MANIFEST_PATH = Path.home() / ".config/work-sync/folders.json"


class Target(StrEnum):
    """Receiving machine names."""

    MACMINI = "macmini"
    TSUKI = "tsuki"

    @property
    def host(self) -> Host:
        """Return the manifest host name."""
        return "mac" if self is Target.MACMINI else "tsuki"


@app.callback()
def main(ctx: typer.Context) -> None:
    """Show help when no command is provided."""
    os.umask(0o077)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _runner() -> Runner:
    return Runner(detect_host())


def _abort(error: Exception) -> NoReturn:
    message = str(error)
    if isinstance(error, subprocess.CalledProcessError):
        message = (error.stderr or error.stdout or message).strip()
    console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(1)


def _show_bootstrap(plan: BootstrapPlan, apply: bool) -> None:
    table = Table(title="Syncthing folder")
    table.add_column("Folder")
    table.add_column("macmini")
    table.add_column("tsuki")
    table.add_column("Ignores")
    table.add_row(
        plan.folder.label,
        str(plan.folder.mac),
        str(plan.folder.tsuki),
        ", ".join(managed_patterns(plan.folder)),
    )
    console.print(table)
    if plan.repository_managed_ignore:
        console.print(".stignore is repository-managed and was not edited.")
    console.print(
        "[green]Applied and verified.[/green]"
        if apply
        else "Dry run passed. Add [bold]--apply[/bold] to configure the folder."
    )


def _show_handoff(plan: HandoffPlan, dry_run: bool) -> None:
    table = Table(title=f"Orca worktree handoff {plan.source} -> {plan.target}")
    table.add_column("Repository")
    table.add_column("Branch")
    table.add_column("External worktrees")
    table.add_column("Missing on target")
    for folder in plan.folders:
        table.add_row(
            folder.folder.label,
            folder.main.source.branch,
            str(len(folder.existing_worktrees) + len(folder.missing_worktrees)),
            str(len(folder.missing_worktrees)),
        )
    console.print(table)
    if dry_run:
        console.print("[green]Dry run passed. No files or Git state changed.[/green]")


@contextmanager
def _handoff_lock() -> Iterator[None]:
    path = Path.home() / ".local/state/work-sync/handoff.lock"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise UsageError("another work-sync handoff is running") from error
        yield


@app.command(epilog=BOOTSTRAP_EPILOG, rich_help_panel="Syncthing")
def bootstrap(
    folder: Annotated[
        str,
        typer.Argument(help="Manifest folder ID or label."),
    ],
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Apply the validated Syncthing setup."),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(min=1, help="Seconds to wait for Syncthing to become idle."),
    ] = 300,
    manifest_path: Annotated[
        Path,
        typer.Option(
            "--manifest",
            help="Private folder manifest.",
            dir_okay=False,
        ),
    ] = DEFAULT_MANIFEST_PATH,
) -> None:
    """Validate or install one manifest-defined Syncthing folder."""
    try:
        runner = _runner()
        verify_manifest_copies(runner)
        selected = load_manifest(manifest_path).select(folder)
        plan = Syncthing(runner).bootstrap(
            selected,
            apply=apply,
            timeout=timeout,
        )
    except (UsageError, subprocess.CalledProcessError) as error:
        _abort(error)
    _show_bootstrap(plan, apply)


@app.command(epilog=HANDOFF_EPILOG, rich_help_panel="Git")
def handoff(
    target: Annotated[
        Target,
        typer.Argument(help="Receiving machine. Target means the receiving machine."),
    ],
    folders: Annotated[
        list[str] | None,
        typer.Option(
            "--folder",
            help="Git folder ID or label. Repeat to select more than one.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Validate and show changes without writing."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Skip the confirmation prompt."),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(min=1, help="Seconds to wait for Syncthing to become idle."),
    ] = 300,
    manifest_path: Annotated[
        Path,
        typer.Option(
            "--manifest",
            help="Private folder manifest.",
            dir_okay=False,
        ),
    ] = DEFAULT_MANIFEST_PATH,
) -> None:
    """Hand external Orca worktrees to the target machine."""
    source = detect_host()
    if target.host == source:
        raise typer.BadParameter("target is the current host", param_hint="TARGET")
    try:
        lock = nullcontext() if dry_run else _handoff_lock()
        with lock:
            runner = Runner(source)
            selected = load_manifest(manifest_path).git_folders(tuple(folders or ()))
            service = Handoff(runner, Syncthing(runner), Orca(runner))
            plan = service.preflight(selected, target.host, timeout=timeout)
            _show_handoff(plan, dry_run)
            if dry_run:
                return
            if not yes and not Confirm.ask(
                f"Hand {len(plan.folders)} repositories to {target.value}?"
            ):
                console.print("Cancelled. Nothing changed.")
                return
            results = service.execute(plan)
    except (UsageError, subprocess.CalledProcessError) as error:
        _abort(error)
    for result in results:
        console.print(
            f"[green]{result.folder}[/green]: "
            f"{result.worktrees} external worktrees; "
            f"recovery {result.recovery_root}"
        )


@app.command(epilog=CONFLICTS_EPILOG, rich_help_panel="Syncthing")
def conflicts(
    path: Annotated[
        Path,
        typer.Argument(help="Folder to scan recursively."),
    ] = Path("."),
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Recover or quarantine safe conflict copies."),
    ] = False,
    recovery_root: Annotated[
        Path | None,
        typer.Option(
            "--recovery-root",
            help="Recovery directory. Defaults under ~/.local/state/work-sync.",
        ),
    ] = None,
) -> None:
    """Scan Syncthing conflicts without blindly deleting unique data."""
    try:
        root = path.expanduser().resolve()
        if apply:
            stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            recovery = (
                recovery_root.expanduser().resolve()
                if recovery_root
                else Path.home() / ".local/state/work-sync/conflicts" / stamp
            )
            report = apply_conflicts(root, recovery)
        else:
            found = scan_conflicts(root)
            report = None
    except UsageError as error:
        _abort(error)
    if not apply:
        restorable = sum(item.action.startswith("restore-") for item in found)
        quarantinable = sum(item.action == "quarantine" for item in found)
        unresolved = sum(item.action == "unresolved" for item in found)
        console.print(
            f"Found {len(found)}; restorable {restorable}; "
            f"quarantinable {quarantinable}; unresolved {unresolved}."
        )
        if found:
            raise typer.Exit(1)
        return
    assert report is not None
    console.print(
        f"Found {report.total}; restored {report.restored}; "
        f"quarantined {report.quarantined}; unresolved {report.unresolved}."
    )
    if report.recovery_root:
        console.print(f"Recovery: {report.recovery_root}")
    if report.unresolved:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

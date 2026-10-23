"""Bounded local and SSH command execution."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

from .manifest import Host, alias

Execute = Callable[[list[str], str | None], str]

SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=8",
)
# ssh reserves 255 for its own failures: refused, timed out, or rejected keys.
SSH_FAILURE = 255


def _execute(argv: list[str], input_text: str | None) -> str:
    return subprocess.run(
        argv,
        input=input_text,
        text=True,
        errors="replace",
        capture_output=True,
        check=True,
    ).stdout.strip()


@dataclass
class Runner:
    """Run an argv locally or on another configured host."""

    local_host: Host
    execute: Execute = field(default=_execute)
    _reachable: dict[Host, bool] = field(default_factory=dict, init=False, repr=False)
    _ssh_errors: dict[Host, str] = field(default_factory=dict, init=False, repr=False)

    def command(self, host: Host, argv: Sequence[str]) -> list[str]:
        """Build the local or remote command without executing it."""
        command = list(argv)
        if host == self.local_host:
            return command
        return ["ssh", *SSH_OPTIONS, alias(host), shlex.join(command)]

    def reachable(self, host: Host) -> bool:
        """Probe a host over SSH once; the local host is always reachable."""
        if host == self.local_host:
            return True
        if host not in self._reachable:
            try:
                self.run(host, ["true"])
            except subprocess.CalledProcessError as error:
                if error.returncode != SSH_FAILURE:
                    raise
                self._reachable[host] = False
                lines = str(error.stderr or "").strip().splitlines()
                self._ssh_errors[host] = lines[-1] if lines else ""
            else:
                self._reachable[host] = True
        return self._reachable[host]

    def describe(self, host: Host) -> str:
        """Name a host with the last ssh error line from a failed probe."""
        reason = self._ssh_errors.get(host)
        return f"{alias(host)} ({reason})" if reason else alias(host)

    def split_reachable(
        self,
        hosts: Iterable[Host],
    ) -> tuple[tuple[Host, ...], tuple[Host, ...]]:
        """Return reachable and unreachable hosts, preserving order."""
        ordered = tuple(dict.fromkeys(hosts))
        reachable = tuple(host for host in ordered if self.reachable(host))
        return reachable, tuple(host for host in ordered if host not in reachable)

    def run(
        self,
        host: Host,
        argv: Sequence[str],
        *,
        input_text: str | None = None,
    ) -> str:
        """Run a command and return stripped stdout."""
        return self.execute(self.command(host, argv), input_text)

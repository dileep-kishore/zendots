"""Bounded local and SSH command execution."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from .manifest import Host

Execute = Callable[[list[str], str | None], str]

SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=8",
)


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
    """Run an argv locally or on the other configured host."""

    local_host: Host
    execute: Execute = field(default=_execute)

    def command(self, host: Host, argv: Sequence[str]) -> list[str]:
        """Build the local or remote command without executing it."""
        command = list(argv)
        if host == self.local_host:
            return command
        alias = "tsuki" if host == "tsuki" else "macmini"
        return ["ssh", *SSH_OPTIONS, alias, shlex.join(command)]

    def run(
        self,
        host: Host,
        argv: Sequence[str],
        *,
        input_text: str | None = None,
    ) -> str:
        """Run a command and return stripped stdout."""
        return self.execute(self.command(host, argv), input_text)

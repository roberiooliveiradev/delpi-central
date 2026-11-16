"""ATLAS P2.2h.2l: offline, read-only Git checkout observation (INERT).

This module is not an MCP tool, web endpoint, persistent agent, CLI or deploy
executor. A clean Git status is NOT an authenticated host attestation, safe
migration, backup/rollback proof or PREPARE grant. The collector must run
under a separately reviewed, unprivileged read-only identity on a trusted
repository, without Docker privileges or API caller-selected paths.
"""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .deploy_host_source import RuntimeTarget, validate_target

_ROOT = Path("/home/operador/projetos/delpi-central")
_HEX_SHA = re.compile(r"[0-9a-f]{40}\Z")
_MAX_OUTPUT = 65536
_TIMEOUT = 5
_ALLOWLIST = {
    ("hml", "public-hub"): ("delpi-hml-public-hub", "delpi-hml"),
    ("prod", "public-hub"): ("delpi-public-hub", "infra"),
}
_ENV = {
    "PATH": "/usr/bin:/bin",
    "HOME": "/nonexistent",
    "LC_ALL": "C",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_LFS_SKIP_SMUDGE": "1",
}


class GitCheckoutReadError(Exception):
    """Finite codes only: never leak filenames, Git config or stderr."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class GitCheckoutObservation:
    """Untrusted-for-PREPARE diagnostic of Git state at one host checkout."""

    environment: str
    service_id: str
    branch: str
    head_sha: str
    tracked_and_untracked_clean: bool
    observed_at: datetime
    status: str
    blocks: tuple[str, ...]
    # Explicitly not an authenticated, challenge-bound host proof.
    checkout_attested: bool = False
    challenge_bound: bool = False
    rollback_ready: bool = False
    prepare_eligible: bool = False


class GitCheckoutReadOnlyObserver:
    """Reads the one server-owned checkout via read-only, bounded Git commands.

    The checkout_root and runner injection exist exclusively for hermetic
    tests; never wire either from an HTTP/MCP request. Production uses the
    fixed srv-api root. Local Git configuration is not accepted as an
    authority for repository provenance.
    """

    def __init__(
        self, *,
        checkout_root: Path = _ROOT,
        run_command: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._checkout_root = checkout_root
        self._runner = run_command
        self._clock = clock

    def _root(self) -> Path:
        path = self._checkout_root
        if not isinstance(path, Path) or not path.is_absolute() or path.is_symlink():
            raise GitCheckoutReadError("GIT_CHECKOUT_PATH_INVALID")
        try:
            resolved = path.resolve(strict=True)
            if resolved != path or not path.is_dir():
                raise GitCheckoutReadError("GIT_CHECKOUT_PATH_INVALID")
            metadata = path / ".git"
            if metadata.is_symlink() or not metadata.is_dir():
                # Do not allow an external gitdir, submodule checkout or
                # worktree whose authority cannot be established here.
                raise GitCheckoutReadError("GIT_CHECKOUT_METADATA_INVALID")
        except (OSError, RuntimeError):
            raise GitCheckoutReadError("GIT_CHECKOUT_PATH_INVALID") from None
        return path

    def _git(self, root: Path, *args: str) -> str:
        argv = [
            "git", "--no-optional-locks", "-C", str(root),
            "-c", "core.fsmonitor=false",
            "-c", "core.untrackedCache=false",
            "-c", "core.hooksPath=/dev/null",
            *args,
        ]
        try:
            done = self._runner(
                argv, env=dict(_ENV), capture_output=True,
                text=True, check=False, timeout=_TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
            raise GitCheckoutReadError("GIT_CHECKOUT_COMMAND_UNAVAILABLE") from None
        if (
            type(done.returncode) is not int or done.returncode != 0
            or type(done.stdout) is not str
        ):
            raise GitCheckoutReadError("GIT_CHECKOUT_COMMAND_FAILED")
        if len(done.stdout.encode("utf-8", "replace")) > _MAX_OUTPUT:
            raise GitCheckoutReadError("GIT_CHECKOUT_OUTPUT_TOO_LARGE")
        return done.stdout

    def read(self, *, target: RuntimeTarget) -> GitCheckoutObservation:
        if not validate_target(target):
            raise GitCheckoutReadError("GIT_CHECKOUT_TARGET_INVALID")
        expected = _ALLOWLIST.get((target.environment, target.service_id))
        if expected is None or (
            target.container_name, target.compose_project
        ) != expected:
            raise GitCheckoutReadError("GIT_CHECKOUT_TARGET_NOT_ALLOWLISTED")
        observed_at = self._clock()
        if (
            type(observed_at) is not datetime
            or observed_at.tzinfo is None
            or observed_at.utcoffset() is None
        ):
            raise GitCheckoutReadError("GIT_CHECKOUT_CLOCK_INVALID")
        root = self._root()
        top = self._git(root, "rev-parse", "--show-toplevel").strip()
        if top != str(root):
            raise GitCheckoutReadError("GIT_CHECKOUT_ROOT_MISMATCH")
        branch = self._git(root, "symbolic-ref", "--quiet", "--short", "HEAD").strip()
        head = self._git(root, "rev-parse", "--verify", "HEAD^{commit}").strip()
        if not _HEX_SHA.fullmatch(head):
            raise GitCheckoutReadError("GIT_CHECKOUT_HEAD_INVALID")
        changes = self._git(
            root, "status", "--porcelain=v1", "-z",
            "--untracked-files=all", "--ignore-submodules=none",
        )
        branch_again = self._git(
            root, "symbolic-ref", "--quiet", "--short", "HEAD",
        ).strip()
        head_again = self._git(root, "rev-parse", "--verify", "HEAD^{commit}").strip()
        top_again = self._git(root, "rev-parse", "--show-toplevel").strip()
        if branch != branch_again or head != head_again or top != top_again:
            raise GitCheckoutReadError("GIT_CHECKOUT_CHANGED_DURING_READ")

        clean = not changes
        blocks = ["GIT_CHECKOUT_NOT_HOST_ATTESTED"]
        if branch != "main":
            blocks.append("GIT_CHECKOUT_NOT_ON_MAIN")
        if changes:
            blocks.append("GIT_CHECKOUT_DIRTY")
        return GitCheckoutObservation(
            environment=target.environment, service_id=target.service_id,
            branch=branch, head_sha=head,
            tracked_and_untracked_clean=clean,
            observed_at=observed_at.astimezone(timezone.utc),
            status="inspection_only_blocked",
            blocks=tuple(blocks),
        )

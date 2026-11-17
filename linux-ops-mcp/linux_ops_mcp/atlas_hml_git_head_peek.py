"""ATLAS HML: bounded, metadata-only peek of a shared Git checkout.

The srv-api checkout is owned by an operator and group-writable. The
unprivileged ATLAS account cannot safely elevate it into Git's trusted
repository set. Instead this code reads only .git/HEAD and main's direct or
packed ref, using nofollow file descriptors. It does NOT invoke Git, load
repository configuration, calculate clean status, check objects, verify an
image deployment, authenticate the checkout, or grant PREPARE / ACT.

The checkout_root argument exists ONLY for disposable unit tests. The CLI
passes the fixed Linux host path and never accepts a path from its caller.
"""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .deploy_git_checkout_readonly import _ROOT as _HOST_CHECKOUT

_HEX = re.compile(rb"[0-9a-f]{40}\Z")
_MAIN_REF = b"ref: refs/heads/main"
_MAIN_NAME = b"refs/heads/main"
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK


class GitHeadPeekError(Exception):
    """Codes are finite and sanitized; never return filesystem content."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class UntrustedGitHead:
    branch: str
    head_sha: str
    source: str = "filesystem_head_only_untrusted"
    checkout_attested: bool = False
    clean_status_observed: bool = False
    challenge_bound: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _bounded_file(git_fd: int, parts: tuple[str, ...], limit: int) -> bytes:
    """Open only known static components using O_NOFOLLOW at each hop."""
    parent = os.dup(git_fd)
    try:
        for component in parts[:-1]:
            child = os.open(component, _DIR_FLAGS, dir_fd=parent)
            os.close(parent)
            parent = child
        fd = os.open(parts[-1], _FILE_FLAGS, dir_fd=parent)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
                raise GitHeadPeekError("GIT_HEAD_METADATA_INVALID")
            pieces = bytearray()
            while len(pieces) <= limit:
                fragment = os.read(fd, min(1024, limit + 1 - len(pieces)))
                if not fragment:
                    break
                pieces.extend(fragment)
            if len(pieces) > limit or b"\x00" in pieces:
                raise GitHeadPeekError("GIT_HEAD_METADATA_INVALID")
            return bytes(pieces)
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def _valid_sha(data: bytes) -> str:
    if _HEX.fullmatch(data.strip()) is None:
        raise GitHeadPeekError("GIT_HEAD_METADATA_INVALID")
    return data.strip().decode("ascii")


def _sha_from_packed(git_fd: int) -> bytes:
    packed = _bounded_file(git_fd, ("packed-refs",), 65536)
    hits: list[bytes] = []
    for entry in packed.splitlines():
        if entry.startswith((b"#", b"^")) or not entry:
            continue
        parts = entry.split(b" ")
        if len(parts) == 2 and parts[1] == _MAIN_NAME:
            hits.append(parts[0])
    if len(hits) != 1:
        raise GitHeadPeekError("GIT_HEAD_REF_UNAVAILABLE")
    return hits[0]


def _read_main_ref(git_fd: int) -> str:
    try:
        data = _bounded_file(git_fd, ("refs", "heads", "main"), 128)
    except FileNotFoundError:
        data = _sha_from_packed(git_fd)
    return _valid_sha(data)


class GitHeadMetadataPeek:
    """Never calls subprocess, Git, configured hooks, external filters or DNS."""

    def __init__(self, *, checkout_root: Path = _HOST_CHECKOUT):
        self._checkout_root = checkout_root

    def read(self) -> UntrustedGitHead:
        root = self._checkout_root
        if not isinstance(root, Path) or not root.is_absolute():
            raise GitHeadPeekError("GIT_HEAD_PATH_INVALID")
        try:
            if root.is_symlink() or root.resolve(strict=True) != root:
                raise GitHeadPeekError("GIT_HEAD_PATH_INVALID")
            root_fd = os.open(root, _DIR_FLAGS)
            try:
                git_fd = os.open(".git", _DIR_FLAGS, dir_fd=root_fd)
                try:
                    # This source is mutable by the operator group. Repeat
                    # reads to detect some races, but NEVER claim atomicity.
                    first_head = _bounded_file(git_fd, ("HEAD",), 128)
                    if first_head.strip() != _MAIN_REF:
                        raise GitHeadPeekError("GIT_HEAD_NOT_MAIN")
                    sha = _read_main_ref(git_fd)
                    last_head = _bounded_file(git_fd, ("HEAD",), 128)
                    last_sha = _read_main_ref(git_fd)
                    if last_head != first_head or last_sha != sha:
                        raise GitHeadPeekError("GIT_HEAD_CHANGED_DURING_READ")
                    return UntrustedGitHead(branch="main", head_sha=sha)
                finally:
                    os.close(git_fd)
            finally:
                os.close(root_fd)
        except GitHeadPeekError:
            raise
        except (OSError, RuntimeError, ValueError):
            raise GitHeadPeekError("GIT_HEAD_UNAVAILABLE") from None

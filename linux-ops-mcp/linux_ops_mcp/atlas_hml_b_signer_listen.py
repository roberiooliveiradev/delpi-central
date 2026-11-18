"""Signer-owned AF_UNIX listen candidate (source-only, disposable fixtures).

The signer process MUST already be non-root before bind/listen. Root-prebound
socket activation is rejected. Serves a bounded number of requests, then exits.
Never installs systemd, never opens Docker, never returns the private key.
"""
from __future__ import annotations

import os
import socket
import stat
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .atlas_hml_posix_acl_review import has_no_extended_posix_acl

from .atlas_hml_b_local_signer import (
    HMLLocalSigner,
    HMLLocalSignerError,
    _serve_one_local_sign_request,
)

_BLOCKS = (
    "SIGNER_LISTEN_SOURCE_ONLY",
    "ROOT_PREBOUND_SOCKET_REJECTED",
    "SAME_HOST_ROOT_CAN_STILL_READ_KEY",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLSignerListenError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSignerListenResult:
    served: int
    socket_path: Path
    status: str = "blocked"
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _require_nonroot_signer_uid() -> int:
    try:
        real, effective, saved = os.getresuid()
    except (OSError, AttributeError):
        raise HMLSignerListenError("HML_SIGNER_LISTEN_IDENTITY_UNVERIFIABLE") from None
    if (
        not all(type(uid) is int for uid in (real, effective, saved))
        or real <= 0
        or (real, effective, saved) != (real, real, real)
    ):
        raise HMLSignerListenError("HML_SIGNER_LISTEN_MUST_BE_NONROOT")
    return effective


def _inode_policy_signature(st: os.stat_result) -> tuple[int, ...]:
    """Compare FD and pathname identity; cannot defend against host root."""
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_gid, st.st_nlink)


def bind_signer_owned_socket(
    *,
    socket_path: Path,
    owner_uid: int,
    socket_gid: int,
    mode: int = 0o660,
) -> socket.socket:
    """Bind/listen after non-root drop in signer:bridge 02750 directory.

    The setgid parent, not best-effort chown, gives the bridge group to the
    socket. UID/GID/mode/ACL and link identity checks are fail-closed.
    """
    uid = _require_nonroot_signer_uid()
    if (
        type(socket_path) is not type(Path("/"))
        or not socket_path.is_absolute()
        or socket_path.name != "sign.sock"
        or type(owner_uid) is not int
        or owner_uid != uid
        or type(socket_gid) is not int
        or socket_gid <= 0
        or type(mode) is not int
        or mode != 0o660
        or not all(hasattr(os, flag) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"))
    ):
        raise HMLSignerListenError("HML_SIGNER_LISTEN_POLICY_DENIED")
    parent = socket_path.parent
    directory_fd = -1
    try:
        directory_fd = os.open(
            parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        parent_st = os.fstat(directory_fd)
        named_parent = os.stat(parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(parent_st.st_mode)
            or parent_st.st_uid != owner_uid
            or parent_st.st_gid != socket_gid
            or stat.S_IMODE(parent_st.st_mode) != 0o2750
            or parent_st.st_nlink < 2
            or _inode_policy_signature(parent_st) != _inode_policy_signature(named_parent)
            or not has_no_extended_posix_acl(directory_fd, directory=True)
        ):
            raise HMLSignerListenError("HML_SIGNER_LISTEN_PARENT_DENIED")
        # Also reject dangling symlinks, which Path.exists() misses.
        try:
            os.stat("sign.sock", dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise HMLSignerListenError("HML_SIGNER_LISTEN_PATH_EXISTS")
    except HMLSignerListenError:
        raise
    except (OSError, ValueError, TypeError):
        raise HMLSignerListenError("HML_SIGNER_LISTEN_PARENT_DENIED") from None
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)

    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bound = False
    try:
        listener.bind(str(socket_path))
        bound = True
        first = os.stat(socket_path, follow_symlinks=False)
        if (
            not stat.S_ISSOCK(first.st_mode)
            or first.st_uid != owner_uid
            or first.st_gid != socket_gid
            or first.st_nlink != 1
            or first.st_dev != parent_st.st_dev
        ):
            raise HMLSignerListenError("HML_SIGNER_LISTEN_SOCKET_UNTRUSTED")
        # Never chown: group inheritance is enforced before/after bind.
        os.chmod(socket_path, mode)
        listener.listen(1)
        after = os.stat(socket_path, follow_symlinks=False)
        parent_after = os.stat(parent, follow_symlinks=False)
        if (
            not stat.S_ISSOCK(after.st_mode)
            or after.st_uid != owner_uid
            or after.st_gid != socket_gid
            or after.st_nlink != 1
            or stat.S_IMODE(after.st_mode) != mode
            or (after.st_dev, after.st_ino) != (first.st_dev, first.st_ino)
            or _inode_policy_signature(parent_after) != _inode_policy_signature(parent_st)
            or listener.getsockname() != str(socket_path)
            or listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1
        ):
            raise HMLSignerListenError("HML_SIGNER_LISTEN_SOCKET_UNTRUSTED")
    except HMLSignerListenError:
        listener.close()
        if bound:
            _safe_unlink_owned(socket_path, owner_uid=owner_uid)
        raise
    except (OSError, ValueError, TypeError):
        listener.close()
        if bound:
            _safe_unlink_owned(socket_path, owner_uid=owner_uid)
        raise HMLSignerListenError("HML_SIGNER_LISTEN_BIND_FAILED") from None
    return listener


def _safe_unlink_owned(path: Path, *, owner_uid: int) -> None:
    try:
        st = os.stat(path, follow_symlinks=False)
        if not stat.S_ISSOCK(st.st_mode) or st.st_uid != owner_uid:
            return
        path.unlink()
    except OSError:
        return


def serve_signer_owned_requests(
    *,
    listener: socket.socket,
    signer: HMLLocalSigner,
    socket_path: Path,
    now: datetime,
    expected_generation_start: int,
    max_requests: int = 1,
) -> HMLSignerListenResult:
    """Serve up to max_requests on an already signer-bound listener."""
    if (
        type(listener) is not socket.socket
        or type(signer) is not HMLLocalSigner
        or type(socket_path) is not type(Path("/"))
        or not socket_path.is_absolute()
        or type(expected_generation_start) is not int
        or expected_generation_start < 1
        or type(max_requests) is not int
        or not 1 <= max_requests <= 8
    ):
        raise HMLSignerListenError("HML_SIGNER_LISTEN_INPUT_INVALID")
    served = 0
    generation = expected_generation_start
    try:
        while served < max_requests:
            _serve_one_local_sign_request(
                listener=listener,
                signer=signer,
                expected_path=socket_path,
                now=now,
                expected_generation=generation,
            )
            served += 1
            generation += 1
    except HMLLocalSignerError as exc:
        raise HMLSignerListenError(exc.code) from None
    return HMLSignerListenResult(served=served, socket_path=socket_path)


def run_signer_listen_once_fixture(
    *,
    socket_path: Path,
    owner_uid: int,
    socket_gid: int,
    signer: HMLLocalSigner,
    now: datetime,
    expected_generation: int,
) -> HMLSignerListenResult:
    """Disposable helper: bind as non-root, serve one request, unlink own socket."""
    listener = bind_signer_owned_socket(
        socket_path=socket_path, owner_uid=owner_uid, socket_gid=socket_gid,
    )
    try:
        return serve_signer_owned_requests(
            listener=listener,
            signer=signer,
            socket_path=socket_path,
            now=now,
            expected_generation_start=expected_generation,
            max_requests=1,
        )
    finally:
        try:
            listener.close()
        except OSError:
            pass
        _safe_unlink_owned(socket_path, owner_uid=owner_uid)


def start_background_signer_listen_fixture(
    *,
    socket_path: Path,
    owner_uid: int,
    socket_gid: int,
    signer: HMLLocalSigner,
    now: datetime,
    expected_generation: int,
    ready: threading.Event,
    errors: list[str],
) -> threading.Thread:
    """CI helper: background bind+serve one request without root prebinding."""

    def _run() -> None:
        try:
            listener = bind_signer_owned_socket(
                socket_path=socket_path, owner_uid=owner_uid, socket_gid=socket_gid,
            )
            ready.set()
            try:
                serve_signer_owned_requests(
                    listener=listener,
                    signer=signer,
                    socket_path=socket_path,
                    now=now,
                    expected_generation_start=expected_generation,
                    max_requests=1,
                )
            finally:
                listener.close()
                _safe_unlink_owned(socket_path, owner_uid=owner_uid)
        except Exception as exc:  # noqa: BLE001 — fixture collects code
            code = getattr(exc, "code", type(exc).__name__)
            errors.append(str(code))
            ready.set()

    thread = threading.Thread(target=_run, name="atlas-hml-signer-listen", daemon=True)
    thread.start()
    return thread

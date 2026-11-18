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


def bind_signer_owned_socket(
    *,
    socket_path: Path,
    owner_uid: int,
    socket_gid: int,
    mode: int = 0o660,
) -> socket.socket:
    """Create, bind and listen on a Unix socket after non-root identity is fixed."""
    uid = _require_nonroot_signer_uid()
    if (
        type(socket_path) is not type(Path("/"))
        or not socket_path.is_absolute()
        or socket_path.name != "sign.sock"
        or type(owner_uid) is not int
        or owner_uid != uid
        or type(socket_gid) is not int
        or socket_gid < 0
        or type(mode) is not int
        or mode != 0o660
    ):
        raise HMLSignerListenError("HML_SIGNER_LISTEN_POLICY_DENIED")
    parent = socket_path.parent
    if not parent.is_absolute() or not parent.is_dir():
        raise HMLSignerListenError("HML_SIGNER_LISTEN_PARENT_DENIED")
    try:
        parent_stat = os.stat(parent, follow_symlinks=False)
        if (
            not stat.S_ISDIR(parent_stat.st_mode)
            or parent_stat.st_uid != owner_uid
            or stat.S_IMODE(parent_stat.st_mode) not in (0o750, 0o700)
        ):
            raise HMLSignerListenError("HML_SIGNER_LISTEN_PARENT_DENIED")
    except OSError:
        raise HMLSignerListenError("HML_SIGNER_LISTEN_PARENT_DENIED") from None
    if socket_path.exists():
        raise HMLSignerListenError("HML_SIGNER_LISTEN_PATH_EXISTS")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path, mode)
        # Ownership: only chown when privileges allow; otherwise require match.
        try:
            if hasattr(os, "chown"):
                os.chown(socket_path, owner_uid, socket_gid)
        except OSError:
            pass
        listener.listen(1)
        st = os.stat(socket_path, follow_symlinks=False)
        if (
            not stat.S_ISSOCK(st.st_mode)
            or st.st_uid != owner_uid
            or stat.S_IMODE(st.st_mode) != mode
        ):
            raise HMLSignerListenError("HML_SIGNER_LISTEN_SOCKET_UNTRUSTED")
        # GID must match when chown succeeded; otherwise accept process primary gid.
        if st.st_gid != socket_gid and st.st_gid != os.getgid():
            raise HMLSignerListenError("HML_SIGNER_LISTEN_SOCKET_UNTRUSTED")
    except HMLSignerListenError:
        listener.close()
        _safe_unlink_owned(socket_path, owner_uid=owner_uid)
        raise
    except (OSError, ValueError, TypeError):
        listener.close()
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

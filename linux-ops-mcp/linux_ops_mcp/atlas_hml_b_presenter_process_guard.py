"""Linux presenter self-boundary guard candidate for ATLAS architecture B.

Source-only. Reads only this process, /proc/self/status, /proc/self/fd,
the inherited AF_UNIX listener and selected environment KEY NAMES.
No Docker API, network dial, service, systemd, CLI, MCP or host mutation.
A clean observation is NOT independent SEC-03/04 or producer attestation.
"""
from __future__ import annotations

import errno
import os
import socket
import stat
from dataclasses import dataclass
from pathlib import Path

_CAPS = ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")
_REQUIRED = ("Uid", "Gid", "Groups", "NoNewPrivs", "Seccomp", *_CAPS)
_DENIED_ENV = frozenset({
    "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "DOCKER_TLS_VERIFY",
    "DOCKER_CERT_PATH", "CONTAINER_HOST", "SSH_AUTH_SOCK",
    "LD_PRELOAD", "LD_LIBRARY_PATH",
})
# Socket activation variables are rejected unless the caller explicitly opts
# into validating a single prebound listener (fixture/CI path). Unexpected
# LISTEN_* inheritance is treated as an alternate Docker/transport risk.
_SOCKET_ACTIVATION_ENV = frozenset({
    "LISTEN_PID", "LISTEN_FDS", "LISTEN_FDNAMES",
})
_RESIDUAL = (
    "PRESENTER_SELF_OBSERVATION_NOT_HOST_ATTESTATION",
    "PRODUCER_ROOT_DOCKER_RISK_NOT_ATTESTED",
    "NONSTANDARD_DOCKER_ENDPOINTS_NOT_ATTESTED",
    "SYSTEMD_LSM_NAMESPACES_NOT_INDEPENDENTLY_ATTESTED",
    "SEC_01_TO_10_PENDING", "PREPARE_DISABLED", "ACT_DISABLED",
)


class HMLPresenterBoundaryError(Exception):
    """Finite sanitized fault; never include raw process details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class PresenterProcessReview:
    status: str = "blocked"
    identity_fd_preflight_passed: bool = False
    sandbox_basics_observed: bool = False
    socket_activation_consistent: bool = False
    open_fd_count: int = 0
    unexpected_socket_fds: int = 0
    host_isolation_attested: bool = False
    docker_isolation_attested: bool = False
    producer_privilege_attested: bool = False
    operational_authorization_granted: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _RESIDUAL


def _read_status() -> dict[str, object]:
    """Bounded procfs parse; never read /proc/self/environ or secrets."""
    try:
        with open("/proc/self/status", "rb") as source:
            raw = source.read(16385)
        if not 0 < len(raw) <= 16384 or b"\x00" in raw:
            raise ValueError("invalid size")
        values: dict[str, str] = {}
        for line in raw.decode("ascii").splitlines():
            key, delim, value = line.partition(":")
            if delim and key in _REQUIRED:
                if key in values:
                    raise ValueError("duplicate")
                values[key] = value.strip()
        if set(values) != set(_REQUIRED):
            raise ValueError("missing")
        uids = tuple(int(x) for x in values["Uid"].split())
        gids = tuple(int(x) for x in values["Gid"].split())
        groups = tuple(int(x) for x in values["Groups"].split())
        if len(uids) != 4 or len(gids) != 4:
            raise ValueError("ids")
        if any(x < 0 for x in (*uids, *gids, *groups)):
            raise ValueError("negative")
        caps = []
        for key in _CAPS:
            hex_value = values[key]
            if not 1 <= len(hex_value) <= 16 or any(
                c not in "0123456789abcdefABCDEF" for c in hex_value
            ):
                raise ValueError("cap")
            caps.append(int(hex_value, 16))
        nnp, seccomp = values["NoNewPrivs"], values["Seccomp"]
        if nnp not in ("0", "1") or seccomp not in ("0", "1", "2"):
            raise ValueError("sandbox")
        return {
            "uids": uids, "gids": gids, "groups": groups,
            "caps": tuple(caps), "nnp": int(nnp), "seccomp": int(seccomp),
        }
    except (OSError, TypeError, UnicodeError, ValueError, OverflowError):
        raise HMLPresenterBoundaryError("HML_PRESENTER_PROC_UNVERIFIABLE") from None


def _fd_set() -> tuple[tuple[int, bool], ...]:
    """Inspect real open descriptor types, never infer them from fd numbers."""
    try:
        names = os.listdir("/proc/self/fd")
        if len(names) > 128 or any(not name.isdecimal() for name in names):
            raise HMLPresenterBoundaryError("HML_PRESENTER_FDS_UNVERIFIABLE")
        found: list[tuple[int, bool]] = []
        for name in names:
            fd = int(name)
            try:
                mode = os.fstat(fd).st_mode
            except OSError as exc:
                # /proc/self/fd enumerator can be closed after listdir().
                if exc.errno == errno.EBADF:
                    continue
                raise
            found.append((fd, stat.S_ISSOCK(mode)))
        return tuple(sorted(found))
    except HMLPresenterBoundaryError:
        raise
    except (OSError, TypeError, ValueError):
        raise HMLPresenterBoundaryError("HML_PRESENTER_FDS_UNVERIFIABLE") from None


def _socket_activation_consistent(listener_fd: int) -> bool:
    """Refuse inherited systemd activation unless it names exactly this FD."""
    present = _SOCKET_ACTIVATION_ENV & set(os.environ)
    if not present:
        return True
    if present != _SOCKET_ACTIVATION_ENV:
        return False
    try:
        listen_pid = int(os.environ["LISTEN_PID"])
        listen_fds = int(os.environ["LISTEN_FDS"])
    except (KeyError, TypeError, ValueError):
        return False
    if listen_pid != os.getpid() or listen_fds != 1:
        return False
    # systemd passes activated sockets starting at FD 3.
    if listener_fd != 3:
        return False
    names = os.environ.get("LISTEN_FDNAMES", "")
    if type(names) is not str or not 1 <= len(names) <= 64 or "/" in names:
        return False
    return True


def _review_prebound_process_fixture(
    listener: socket.socket, *, expected_uid: int, expected_gid: int,
    expected_path: Path,
) -> PresenterProcessReview:
    """Internal fixture-capable guard; no activation, never an attestation.

    Linux CI runs the very same guard inside a separate non-root process.
    Sandbox properties are reviewed independently from the FD/identity check.
    """
    if (
        type(listener) is not socket.socket
        or type(expected_uid) is not int or expected_uid <= 0
        or type(expected_gid) is not int or expected_gid <= 0
        or type(expected_path) is not type(Path("/")) or not expected_path.is_absolute()
        or os.name != "posix" or not hasattr(os, "getresuid")
        or not hasattr(os, "getresgid")
    ):
        raise HMLPresenterBoundaryError("HML_PRESENTER_POLICY_INVALID")
    proc = _read_status()
    fds = _fd_set()
    try:
        descriptor = listener.fileno()
        listener_valid = (
            descriptor >= 3 and listener.family == socket.AF_UNIX
            and listener.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) == socket.SOCK_STREAM
            and listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
            and listener.getsockname() == str(expected_path)
            and stat.S_ISSOCK(os.stat(expected_path, follow_symlinks=False).st_mode)
        )
        # UID/GID real, effective, saved and filesystem must all be dedicated.
        identity_valid = (
            proc["uids"] == (expected_uid,) * 4
            and proc["gids"] == (expected_gid,) * 4
            and not proc["groups"]
            and os.getresuid() == (expected_uid,) * 3
            and os.getresgid() == (expected_gid,) * 3
            and not os.getgroups()
        )
        # No other socket, directory, pipe, regular file or device descriptor
        # above stderr. Avoid assigning trust by simply counting sockets.
        fd_valid = (
            (descriptor, True) in fds
            and len(fds) == len({fd for fd, _ in fds})
            and all(
                (fd == descriptor and is_socket)
                or (fd in (0, 1, 2) and not is_socket)
                for fd, is_socket in fds
            )
        )
        activation_ok = _socket_activation_consistent(descriptor)
        unexpected_sockets = sum(
            1 for fd, is_socket in fds if is_socket and fd != descriptor
        )
    except (OSError, TypeError, ValueError, AttributeError):
        raise HMLPresenterBoundaryError("HML_PRESENTER_CONTEXT_UNVERIFIABLE") from None
    no_capability = proc["caps"][0:3] == (0, 0, 0) and proc["caps"][4] == 0
    prohibited_env = any(
        key in _DENIED_ENV or key.startswith("DOCKER_")
        for key in os.environ
    )
    identity_fd_ok = (
        listener_valid and identity_valid and fd_valid
        and no_capability and not prohibited_env and activation_ok
        and unexpected_sockets == 0
    )
    # NNP/seccomp/cap bounding alone are not proof of filter quality or LSM.
    sandbox_basics = (
        identity_fd_ok and proc["caps"][3] == 0
        and proc["nnp"] == 1 and proc["seccomp"] == 2
    )
    blocks: list[str] = []
    if not identity_valid:
        blocks.append("HML_PRESENTER_IDENTITY_DENIED")
    if not listener_valid or not fd_valid or unexpected_sockets:
        blocks.append("HML_PRESENTER_FD_BOUNDARY_DENIED")
    if not no_capability:
        blocks.append("HML_PRESENTER_CAPABILITIES_DENIED")
    if prohibited_env:
        blocks.append("HML_PRESENTER_ENVIRONMENT_DENIED")
    if not activation_ok:
        blocks.append("HML_PRESENTER_SOCKET_ACTIVATION_DENIED")
    if not sandbox_basics:
        blocks.append("HML_PRESENTER_SANDBOX_NOT_CONFIRMED")
    return PresenterProcessReview(
        identity_fd_preflight_passed=identity_fd_ok,
        sandbox_basics_observed=sandbox_basics,
        socket_activation_consistent=activation_ok,
        open_fd_count=len(fds),
        unexpected_socket_fds=unexpected_sockets,
        blocks=(*blocks, *_RESIDUAL),
    )

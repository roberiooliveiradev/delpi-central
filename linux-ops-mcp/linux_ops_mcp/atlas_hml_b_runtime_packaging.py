"""ATLAS HML runtime packaging review and gated entrypoints (source-only).

Provides process-identity, inherited-FD, Docker-endpoint and supplementary-group
preflight for future authorized packaging. Candidate systemd units remain under
candidate-units/ with ExecStart=/usr/bin/false. packaging-review/ holds explicit
future-install wrappers that refuse host activation without disposable mode.

Never converts .candidate into installable/active units. Never opens Docker.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from .atlas_hml_b_candidate_unit_review import review_candidate_unit_sources
from .atlas_hml_b_stage73_boot_guard import review_stage73_package

_PACKAGING_DIR = Path(__file__).resolve().parents[1] / "packaging-review"
_DENIED_ENV = frozenset({
    "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "DOCKER_TLS_VERIFY",
    "DOCKER_CERT_PATH", "CONTAINER_HOST",
})
_DOCKER_SOCKS = (
    "/run/docker.sock", "/var/run/docker.sock",
)
_ROLES = frozenset({"signer", "bridge", "presenter", "producer"})
_BLOCKS = (
    "RUNTIME_PACKAGING_SOURCE_ONLY",
    "CANDIDATE_UNITS_REMAIN_NON_INSTALLABLE",
    "HOST_ACTIVATION_NOT_AUTHORIZED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLRuntimePackagingError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLRuntimeIdentityPreflight:
    role: str
    uid: int
    gid: int
    supplementary_gids: tuple[int, ...]
    denied_env_present: tuple[str, ...]
    unexpected_socket_fds: int
    status: str = "blocked"
    docker_endpoints_clear: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


@dataclass(frozen=True, slots=True)
class HMLRuntimePackagingReview:
    candidate_units_ok: bool
    stage73_ok: bool
    packaging_review_present: bool
    entrypoint_wrappers: tuple[str, ...]
    status: str = "blocked"
    installable: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _require_nonroot() -> tuple[int, int]:
    try:
        real, effective, saved = os.getresuid()
        rgid, egid, sgid = os.getresgid()
    except (OSError, AttributeError):
        raise HMLRuntimePackagingError("HML_RUNTIME_IDENTITY_UNVERIFIABLE") from None
    if (
        real <= 0 or (real, effective, saved) != (real, real, real)
        or rgid <= 0 or (rgid, egid, sgid) != (rgid, rgid, rgid)
    ):
        raise HMLRuntimePackagingError("HML_RUNTIME_MUST_BE_NONROOT")
    return effective, egid


def _supplementary_gids() -> tuple[int, ...]:
    try:
        groups = tuple(sorted(set(os.getgroups())))
    except OSError:
        raise HMLRuntimePackagingError("HML_RUNTIME_GROUPS_UNVERIFIABLE") from None
    return groups


def _scan_unexpected_socket_fds() -> int:
    """Count non-stdio socket FDs; Docker sock inheritance is always fatal."""
    unexpected = 0
    fd_dir = Path("/proc/self/fd")
    if not fd_dir.is_dir():
        raise HMLRuntimePackagingError("HML_RUNTIME_FD_SCAN_UNAVAILABLE")
    for entry in fd_dir.iterdir():
        try:
            fd = int(entry.name)
        except ValueError:
            continue
        if fd in (0, 1, 2):
            continue
        try:
            target = os.readlink(entry)
        except OSError:
            continue
        for sock in _DOCKER_SOCKS:
            if target == sock or target.endswith(sock):
                raise HMLRuntimePackagingError("HML_RUNTIME_DOCKER_FD_INHERITED")
        if target.startswith("socket:["):
            unexpected += 1
    return unexpected


def _denied_env() -> tuple[str, ...]:
    return tuple(sorted(k for k in _DENIED_ENV if os.environ.get(k)))


def review_runtime_identity_preflight(
    *,
    role: str,
    expected_uid: int | None = None,
    expected_gid: int | None = None,
    allowed_supplementary_gids: frozenset[int] | None = None,
    allow_socket_fds: bool = False,
    disposable_fixture: bool = False,
) -> HMLRuntimeIdentityPreflight:
    """Fail-closed process boundary check for packaging entrypoints."""
    if role not in _ROLES:
        raise HMLRuntimePackagingError("HML_RUNTIME_ROLE_DENIED")
    uid, gid = _require_nonroot()
    if expected_uid is not None and (
        type(expected_uid) is not int or expected_uid <= 0 or uid != expected_uid
    ):
        raise HMLRuntimePackagingError("HML_RUNTIME_UID_MISMATCH")
    if expected_gid is not None and (
        type(expected_gid) is not int or expected_gid <= 0 or gid != expected_gid
    ):
        raise HMLRuntimePackagingError("HML_RUNTIME_GID_MISMATCH")
    groups = _supplementary_gids()
    # Primary gid may appear in getgroups; filter it for policy comparison.
    extras = tuple(g for g in groups if g != gid)
    if allowed_supplementary_gids is not None:
        if type(allowed_supplementary_gids) is not frozenset:
            raise HMLRuntimePackagingError("HML_RUNTIME_GROUP_POLICY_DENIED")
        if frozenset(extras) - allowed_supplementary_gids:
            raise HMLRuntimePackagingError("HML_RUNTIME_SUPPLEMENTARY_DENIED")
    elif extras and not disposable_fixture:
        # Host packaging requires empty supplementary for signer/presenter.
        # Disposable CI runners often inherit groups; that path is explicit.
        if role in {"signer", "presenter"}:
            raise HMLRuntimePackagingError("HML_RUNTIME_SUPPLEMENTARY_DENIED")
    denied = _denied_env()
    if denied:
        raise HMLRuntimePackagingError("HML_RUNTIME_DOCKER_ENV_DENIED")
    unexpected = _scan_unexpected_socket_fds()
    # Disposable fixtures may inherit AF_UNIX from the test harness; host
    # packaging must pass allow_socket_fds=False and have zero extras.
    if unexpected and not allow_socket_fds and not disposable_fixture:
        raise HMLRuntimePackagingError("HML_RUNTIME_UNEXPECTED_SOCKET_FD")
    # Probe classic docker sockets without connecting.
    for path in _DOCKER_SOCKS:
        try:
            st = os.stat(path, follow_symlinks=False)
        except FileNotFoundError:
            continue
        except OSError:
            raise HMLRuntimePackagingError("HML_RUNTIME_DOCKER_SOCK_UNVERIFIABLE") from None
        if stat.S_ISSOCK(st.st_mode):
            # Presence alone is not failure; connecting would be. Mark unclear.
            docker_clear = False
            break
    else:
        docker_clear = True
    return HMLRuntimeIdentityPreflight(
        role=role,
        uid=uid,
        gid=gid,
        supplementary_gids=extras,
        denied_env_present=denied,
        unexpected_socket_fds=unexpected,
        docker_endpoints_clear=docker_clear,
    )


def review_runtime_packaging() -> HMLRuntimePackagingReview:
    """Static packaging review; never marks installable."""
    candidates = review_candidate_unit_sources()
    stage73 = review_stage73_package()
    if not _PACKAGING_DIR.is_dir():
        raise HMLRuntimePackagingError("HML_PACKAGING_REVIEW_DIR_MISSING")
    wrappers = tuple(sorted(p.name for p in _PACKAGING_DIR.glob("atlas-hml-*.entrypoint.py")))
    readme = _PACKAGING_DIR / "README.md"
    if not readme.is_file():
        raise HMLRuntimePackagingError("HML_PACKAGING_README_MISSING")
    readme_text = readme.read_text(encoding="utf-8")
    if "NOT INSTALLABLE" not in readme_text or "AUTHORIZED_INSTALL_ONLY" not in readme_text:
        raise HMLRuntimePackagingError("HML_PACKAGING_README_POLICY_DENIED")
    return HMLRuntimePackagingReview(
        candidate_units_ok=candidates.status == "blocked",
        stage73_ok=stage73.status == "blocked",
        packaging_review_present=True,
        entrypoint_wrappers=wrappers,
    )


def run_packaging_entrypoint(role: str, argv: list[str] | None = None) -> int:
    """CLI wrapper: only disposable-fixture mode is accepted; always blocked."""
    parser = argparse.ArgumentParser(description=f"ATLAS HML {role} packaging entrypoint")
    parser.add_argument("--disposable-fixture", action="store_true", required=True)
    parser.add_argument("--expected-uid", type=int)
    parser.add_argument("--expected-gid", type=int)
    args = parser.parse_args(argv)
    if not args.disposable_fixture:
        raise HMLRuntimePackagingError("HML_RUNTIME_HOST_MODE_DENIED")
    if os.environ.get("ATLAS_HML_RUNTIME_MODE") != "disposable-fixture":
        raise HMLRuntimePackagingError("HML_RUNTIME_MODE_ENV_REQUIRED")
    preflight = review_runtime_identity_preflight(
        role=role,
        expected_uid=args.expected_uid,
        expected_gid=args.expected_gid,
        allow_socket_fds=False,
        disposable_fixture=True,
    )
    packaging = review_runtime_packaging()
    print(json.dumps({
        "schema": "atlas.hml.runtime-entrypoint.v1",
        "role": role,
        "status": "blocked",
        "preflight": asdict(preflight),
        "packaging": asdict(packaging),
        "prepare_eligible": False,
        "can_execute": False,
    }, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(run_packaging_entrypoint("signer"))

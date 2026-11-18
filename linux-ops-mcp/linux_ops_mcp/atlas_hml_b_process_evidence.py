"""Offline, fail-closed Linux process evidence review for architecture B.

Consumes only operator-supplied data. No /proc access, shell, Docker, systemd,
network, or activation entrypoint. Passing review does NOT attest the host.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.process-observation.v1"
_CAP_ZERO = "0000000000000000"
_SOCKET_RE = re.compile(r"socket:\[[0-9]+\]\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = frozenset({
    "schema", "source", "host", "role", "uid", "euid", "gid", "egid",
    "supplementary_gids", "cap_eff", "cap_prm", "cap_amb",
    "no_new_privileges", "seccomp_mode", "lsm_enforcing",
    "namespace_isolation_verified", "fd_targets", "docker_endpoints_checked",
    "evidence_sha256",
})
_REQUIRED_ENDPOINTS = frozenset({
    "/run/docker.sock", "/var/run/docker.sock",
    "docker_tcp", "docker_host_env", "docker_fd_inheritance",
    "docker_mount_aliases",
})
_BLOCKS = (
    "HOST_PROCESS_NOT_INDEPENDENTLY_ATTESTED",
    "DOCKER_ENDPOINTS_NOT_EXHAUSTIVELY_ATTESTED",
    "SNAPSHOT_PRODUCER_PRIVILEGE_NOT_ATTESTED",
    "SEC_01_TO_10_NOT_APPROVED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLProcessEvidenceError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLProcessEvidenceReview:
    status: str = "blocked"
    checks_claimed: bool = True
    host_attested: bool = False
    producer_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for k, v in pairs:
        if k in result:
            raise HMLProcessEvidenceError("HML_PROCESS_DUPLICATE_FIELD")
        result[k] = v
    return result


def _reject_constant(_: str) -> None:
    raise HMLProcessEvidenceError("HML_PROCESS_INVALID_JSON")


def review_untrusted_process_observation(raw: bytes) -> HMLProcessEvidenceReview:
    """Review a deliberately limited presenter observation, never perform probing.

    Root/process compromise, stale observation and forged evidence are not
    detectable from supplied JSON. This function never enables execution.
    """
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096 or b"\x00" in raw:
        raise HMLProcessEvidenceError("HML_PROCESS_INVALID_INPUT")
    try:
        doc = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except HMLProcessEvidenceError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise HMLProcessEvidenceError("HML_PROCESS_INVALID_JSON") from None
    if type(doc) is not dict or set(doc) != _FIELDS:
        raise HMLProcessEvidenceError("HML_PROCESS_INVALID_SCHEMA")
    if any(doc[k] != value or type(doc[k]) is not str for k, value in {
        "schema": _SCHEMA,
        "source": "operator_supplied_untrusted",
        "host": "srv-api",
        "role": "presenter",
    }.items()):
        raise HMLProcessEvidenceError("HML_PROCESS_SCOPE_DENIED")
    ids = ("uid", "euid", "gid", "egid")
    if any(type(doc[k]) is not int or doc[k] <= 0 for k in ids):
        raise HMLProcessEvidenceError("HML_PROCESS_IDENTITY_DENIED")
    if doc["uid"] != doc["euid"] or doc["gid"] != doc["egid"]:
        raise HMLProcessEvidenceError("HML_PROCESS_IDENTITY_DENIED")
    if type(doc["supplementary_gids"]) is not list or doc["supplementary_gids"]:
        raise HMLProcessEvidenceError("HML_PROCESS_GROUPS_DENIED")
    if any(type(doc[k]) is not str or doc[k] != _CAP_ZERO for k in
           ("cap_eff", "cap_prm", "cap_amb")):
        raise HMLProcessEvidenceError("HML_PROCESS_CAPABILITIES_DENIED")
    if (doc["no_new_privileges"] is not True
            or type(doc["seccomp_mode"]) is not int
            or doc["seccomp_mode"] != 2
            or doc["lsm_enforcing"] is not True
            or doc["namespace_isolation_verified"] is not True):
        raise HMLProcessEvidenceError("HML_PROCESS_SANDBOX_UNVERIFIED")
    fds = doc["fd_targets"]
    if (type(fds) is not list or len(fds) != len(set(map(str, fds)))
            or len(fds) > 32 or not fds
            or any(type(s) is not str or not _SOCKET_RE.fullmatch(s) for s in fds)):
        raise HMLProcessEvidenceError("HML_PROCESS_FD_UNVERIFIED")
    # One inherited socket is expected for systemd activation. FD metadata
    # alone cannot prove its peer is safe: evidence remains untrusted.
    if len(fds) != 1:
        raise HMLProcessEvidenceError("HML_PROCESS_FD_UNVERIFIED")
    endpoints = doc["docker_endpoints_checked"]
    if (type(endpoints) is not list or len(endpoints) != len(_REQUIRED_ENDPOINTS)
            or any(type(v) is not str for v in endpoints)
            or set(endpoints) != _REQUIRED_ENDPOINTS):
        raise HMLProcessEvidenceError("HML_PROCESS_ENDPOINTS_UNVERIFIED")
    digest = doc["evidence_sha256"]
    if type(digest) is not str or not _HEX.fullmatch(digest):
        raise HMLProcessEvidenceError("HML_PROCESS_EVIDENCE_UNVERIFIED")
    return HMLProcessEvidenceReview()

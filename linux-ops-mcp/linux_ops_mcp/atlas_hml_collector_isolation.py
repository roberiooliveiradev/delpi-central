"""Manual read-only Linux OS posture review for the future ATLAS HML collector.

Run as the dedicated collector ONLY after operator approval. No Docker
connection, socket binding, privilege changes, subprocess, network, systemd
changes, host service, DB, Keycloak, deploy or MCP tool. A successful OS
observation is NOT security attestation or permission to PREPARE / ACT.
"""
from __future__ import annotations

import grp
import json
import os
import pwd
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_COLLECTOR = "atlas-hml"
_CHECKOUT = Path("/home/operador/projetos/delpi-central")
_PROC_STATUS = Path("/proc/self/status")
_RAW_DOCKER_SOCKETS = (Path("/run/docker.sock"), Path("/var/run/docker.sock"))
_PRIVILEGED_GROUPS = frozenset(
    {"root", "docker", "sudo", "wheel", "lxd", "podman"}
)
_ALTERNATE_ENV = ("DOCKER_HOST", "DOCKER_CONTEXT", "CONTAINER_HOST")
_ALWAYS = (
    "RAW_DOCKER_ENDPOINTS_NOT_EXHAUSTIVELY_ATTESTED",
    "HML_UPSTREAM_PROCESS_NOT_INDEPENDENTLY_ATTESTED",
    "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED",
    "HOST_COLLECTOR_TRANSPORT_NOT_ATTESTED",
    "HML_BACKUP_RESTORE_ROLLBACK_NOT_ATTESTED",
    "JOURNAL_CHALLENGE_NOT_CONSUMED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)
_CHECKS = (
    ("named_account_matches_process", "COLLECTOR_OS_IDENTITY_UNVERIFIED"),
    ("nologin_shell", "COLLECTOR_LOGIN_SHELL_UNSAFE"),
    ("primary_group_exclusive", "COLLECTOR_PRIMARY_GROUP_UNVERIFIED"),
    ("privileged_groups_absent", "COLLECTOR_PRIVILEGED_GROUP_PRESENT_OR_UNKNOWN"),
    ("checkout_write_denied", "COLLECTOR_CHECKOUT_WRITE_NOT_DENIED"),
    ("raw_socket_write_denied", "COLLECTOR_RAW_DOCKER_ACCESS_NOT_DENIED"),
    ("capabilities_zero", "COLLECTOR_LINUX_CAPABILITIES_NOT_ZERO"),
    ("ambient_capabilities_zero", "COLLECTOR_AMBIENT_CAPABILITIES_NOT_ZERO"),
    ("no_new_privileges", "COLLECTOR_NO_NEW_PRIVILEGES_NOT_ESTABLISHED"),
    ("seccomp_filter", "COLLECTOR_SECCOMP_FILTER_NOT_ESTABLISHED"),
    ("alternate_docker_env_unset", "COLLECTOR_ALTERNATE_DOCKER_ENV_PRESENT"),
)


@dataclass(frozen=True, slots=True)
class CollectorPostureFacts:
    """Sanitized observation only, no usernames, UID, raw proc or env values."""

    named_account_matches_process: bool | None
    nologin_shell: bool | None
    primary_group_exclusive: bool | None
    privileged_groups_absent: bool | None
    checkout_write_denied: bool | None
    raw_socket_write_denied: bool | None
    capabilities_zero: bool | None
    ambient_capabilities_zero: bool | None
    no_new_privileges: bool | None
    seccomp_filter: bool | None
    alternate_docker_env_unset: bool | None


@dataclass(frozen=True, slots=True)
class CollectorIsolationReview:
    status: str
    blocks: tuple[str, ...]
    checks: CollectorPostureFacts
    environment: str = "hml"
    service_id: str = "public-hub"
    host_identity_attested: bool = False
    upstream_process_attested: bool = False
    proxy_policy_independently_attested: bool = False
    checkout_integrity_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


class CollectorReviewError(Exception):
    """Only sanitized finite error codes may escape the review."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _proc_flags(path: Path = _PROC_STATUS) -> tuple[bool | None, ...]:
    """Read a bounded, fixed proc file; never expose the text to the caller."""
    try:
        with path.open("rb") as handle:
            data = handle.read(8193)
        if len(data) > 8192:
            return (None, None, None, None)
        text = data.decode("ascii")
        values = {}
        for line in text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                if key in ("CapEff", "CapAmb", "NoNewPrivs", "Seccomp"):
                    values[key] = value.strip()
        def zero_cap(name: str) -> bool | None:
            value = values.get(name, "")
            return int(value, 16) == 0 if re.fullmatch(r"[0-9a-fA-F]{1,32}", value) else None
        cap_eff = zero_cap("CapEff")
        cap_amb = zero_cap("CapAmb")
        nnp = values.get("NoNewPrivs")
        seccomp = values.get("Seccomp")
        return (
            cap_eff,
            cap_amb,
            nnp == "1" if nnp in ("0", "1") else None,
            seccomp == "2" if seccomp in ("0", "1", "2") else None,
        )
    except (OSError, UnicodeError, ValueError):
        return (None, None, None, None)


def _writable(path: Path, *, check_exists: bool = False) -> bool | None:
    """Observe DAC effective access without connecting/opening a Docker API."""
    try:
        if check_exists:
            try:
                path.stat()
            except FileNotFoundError:
                return False
        return os.access(path, os.W_OK, effective_ids=True)
    except (OSError, NotImplementedError, TypeError, ValueError):
        return None


def _raw_socket_denied() -> bool | None:
    for path in _RAW_DOCKER_SOCKETS:
        writable = _writable(path, check_exists=True)
        if writable is None:
            return None
        if writable:
            return False
    return True


def observe_current_process() -> CollectorPostureFacts:
    """Read-only local observations; must run with atlas-hml credentials."""
    named = login = primary = privileged_absent = None
    try:
        account = pwd.getpwnam(_COLLECTOR)
        group = grp.getgrnam(_COLLECTOR)
        named = (
            account.pw_uid > 0
            and os.getuid() == account.pw_uid
            and os.geteuid() == account.pw_uid
        )
        login = account.pw_shell in ("/usr/sbin/nologin", "/sbin/nologin")
        primary = (
            group.gr_gid > 0
            and account.pw_gid == group.gr_gid
            and os.getgid() == group.gr_gid
            and os.getegid() == group.gr_gid
        )
        actual_gids = set(os.getgroups()) | {os.getegid()}
        names = {grp.getgrgid(gid).gr_name for gid in actual_gids}
        privileged_absent = not bool(names & _PRIVILEGED_GROUPS)
    except (OSError, KeyError, TypeError, ValueError):
        pass
    cap_eff, cap_amb, nnp, seccomp = _proc_flags()
    checkout_writable = _writable(_CHECKOUT)
    return CollectorPostureFacts(
        named_account_matches_process=named,
        nologin_shell=login,
        primary_group_exclusive=primary,
        privileged_groups_absent=privileged_absent,
        checkout_write_denied=(
            not checkout_writable if checkout_writable is not None else None
        ),
        raw_socket_write_denied=_raw_socket_denied(),
        capabilities_zero=cap_eff,
        ambient_capabilities_zero=cap_amb,
        no_new_privileges=nnp,
        seccomp_filter=seccomp,
        alternate_docker_env_unset=not any(
            os.environ.get(key) for key in _ALTERNATE_ENV
        ),
    )


def review_facts(facts: CollectorPostureFacts) -> CollectorIsolationReview:
    """Deny-only interpretation: facts can never assert host attestation."""
    if type(facts) is not CollectorPostureFacts:
        raise CollectorReviewError("ATLAS_COLLECTOR_FACTS_INVALID")
    blocks = list(_ALWAYS)
    for name, code in _CHECKS:
        item = getattr(facts, name)
        if item is not None and type(item) is not bool:
            raise CollectorReviewError("ATLAS_COLLECTOR_FACTS_INVALID")
        if item is not True:
            blocks.append(code)
    return CollectorIsolationReview(
        status="blocked", blocks=tuple(blocks), checks=facts,
    )


def main() -> int:
    """Safe CLI with no user-supplied path or options. Exit 0 is NOT approval."""
    try:
        result = review_facts(observe_current_process())
        print(json.dumps(asdict(result), sort_keys=True, separators=(",", ":")))
        return 0
    except Exception:
        print(json.dumps({
            "status": "blocked",
            "code": "ATLAS_COLLECTOR_REVIEW_UNAVAILABLE",
            "prepare_eligible": False,
            "can_execute": False,
        }, sort_keys=True, separators=(",", ":")))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

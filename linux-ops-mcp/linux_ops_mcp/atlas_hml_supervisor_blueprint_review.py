"""Static review of intentionally NON-RUNNABLE ATLAS HML systemd blueprints.

No systemd execution, host inspection, shell, Docker connection, service start,
filesystem mutation, MCP endpoint or PREPARE/ACT integration exists here.
Passing this lexical review proves only that checked-in proposal text matches
its own review-only contract. It NEVER attests Linux isolation or Docker policy.
"""
from __future__ import annotations

import configparser
import io
from dataclasses import dataclass
from pathlib import Path

_DIR = Path(__file__).resolve().parents[1] / "review-only"
_SENTINEL = "/run/atlas-hml-readonly/REVIEW-ONLY-NEVER-CREATE"
_UNIT = {
    "ConditionPathExists": _SENTINEL,
    "RefuseManualStart": "yes",
}
_HARDENED = {
    "NoNewPrivileges": "yes",
    "CapabilityBoundingSet": "",
    "AmbientCapabilities": "",
    "ProtectSystem": "strict",
    "ProtectHome": "yes",
    "PrivateTmp": "yes",
    "PrivateDevices": "yes",
    "ProtectKernelTunables": "yes",
    "ProtectKernelModules": "yes",
    "ProtectKernelLogs": "yes",
    "ProtectControlGroups": "yes",
    "RestrictSUIDSGID": "yes",
    "RestrictNamespaces": "yes",
    "LockPersonality": "yes",
    "SystemCallArchitectures": "native",
    "RestrictAddressFamilies": "AF_UNIX",
    "UMask": "0077",
}
_EXPECTED: dict[str, dict[str, dict[str, str]]] = {
    "atlas-hml-snapshot-producer.service.review": {
        "Unit": {**_UNIT, "Description": "ATLAS HML SNAPSHOT PRODUCER REVIEW ONLY"},
        "Service": {
            **_HARDENED, "Type": "oneshot", "User": "root",
            "Group": "root", "ExecStart": "/usr/bin/false",
            "ReadWritePaths": "/run/atlas-hml-readonly",
        },
    },
    "atlas-hml-snapshot-presenter.service.review": {
        "Unit": {**_UNIT, "Description": "ATLAS HML SNAPSHOT PRESENTER REVIEW ONLY"},
        "Service": {
            **_HARDENED, "Type": "simple", "User": "atlas-hml",
            "Group": "atlas-hml", "SupplementaryGroups": "",
            "ExecStart": "/usr/bin/false",
            "InaccessiblePaths": "/run/docker.sock /var/run/docker.sock",
            "ReadOnlyPaths": "/run/atlas-hml-readonly",
        },
    },
    "atlas-hml-snapshot-presenter.socket.review": {
        "Unit": {**_UNIT, "Description": "ATLAS HML SNAPSHOT PRESENTER SOCKET REVIEW ONLY"},
        "Socket": {
            "ListenStream": "/run/atlas-hml-readonly/inspect.sock",
            "SocketUser": "root", "SocketGroup": "atlas-hml",
            "SocketMode": "0660", "DirectoryMode": "0750",
            "Accept": "no", "Service": "atlas-hml-snapshot-presenter.service",
        },
    },
    "atlas-hml-snapshot-producer.timer.review": {
        "Unit": {**_UNIT, "Description": "ATLAS HML SNAPSHOT PRODUCER TIMER REVIEW ONLY"},
        "Timer": {
            "OnUnitActiveSec": "30s", "Unit": "atlas-hml-snapshot-producer.service",
            "Persistent": "no",
        },
    },
}
_TMPFILES = "d /run/atlas-hml-readonly 0750 root atlas-hml -"
_TMPFILES_NAME = "atlas-hml-runtime-dir.tmpfiles.review"
_ALLOWED_NAMES = frozenset((*_EXPECTED, _TMPFILES_NAME))
_ALWAYS_BLOCKS = (
    "HML_ARCHITECTURE_NOT_APPROVED",
    "SYSTEMD_BLUEPRINTS_NON_RUNNABLE",
    "SYSTEMD_HOST_SANDBOX_NOT_ATTESTED",
    "ROOT_PRODUCER_DOCKER_PRIVILEGE_UNREVIEWED",
    "SOCKET_PARENT_OWNER_NOT_ATTESTED",
    "RAW_DOCKER_ALIASES_AND_FDS_NOT_EXHAUSTIVELY_ATTESTED",
    "SNAPSHOT_ORIGIN_AND_REPLAY_NOT_ATTESTED",
    "INDEPENDENT_SECURITY_REVIEW_REQUIRED",
    "CORE_PREPARE_NOT_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLSupervisorBlueprintError(Exception):
    """Finite error only, independent of submitted source text."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSupervisorBlueprintReview:
    status: str = "blocked"
    scope: str = "hml/public-hub"
    files_reviewed: int = 5
    systemd_units_installed: bool = False
    docker_privilege_attested: bool = False
    presenter_isolation_attested: bool = False
    socket_directory_attested: bool = False
    architecture_approved: bool = False
    host_identity_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _ALWAYS_BLOCKS


def _parse_unit(source: str) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser(
        interpolation=None, strict=True, allow_no_value=False,
    )
    parser.optionxform = str
    try:
        parser.read_file(io.StringIO(source))
        if parser.defaults() or not parser.sections():
            raise ValueError("no sections")
        return {
            section: dict(parser.items(section, raw=True))
            for section in parser.sections()
        }
    except (configparser.Error, ValueError, TypeError):
        raise HMLSupervisorBlueprintError("HML_BLUEPRINT_UNIT_INVALID") from None


def review_blueprint_sources(sources: dict[str, str]) -> HMLSupervisorBlueprintReview:
    """Exact allowlisted lexical contract. It cannot authorize a host operation."""
    if type(sources) is not dict or set(sources) != _ALLOWED_NAMES:
        raise HMLSupervisorBlueprintError("HML_BLUEPRINT_SET_INVALID")
    for name, content in sources.items():
        if (
            type(name) is not str or not name.endswith(".review")
            or type(content) is not str
            or not 1 <= len(content) <= 8192
            or "\x00" in content
        ):
            raise HMLSupervisorBlueprintError("HML_BLUEPRINT_SOURCE_INVALID")
        if name == _TMPFILES_NAME:
            active = [
                line.strip() for line in content.splitlines()
                if line.strip() and not line.lstrip().startswith(("#", ";"))
            ]
            if active != [_TMPFILES]:
                raise HMLSupervisorBlueprintError("HML_BLUEPRINT_TMPFILES_UNSAFE")
            continue
        actual = _parse_unit(content)
        if actual != _EXPECTED[name]:
            raise HMLSupervisorBlueprintError("HML_BLUEPRINT_POLICY_DRIFT")
        # Intentionally different extensions and the false ExecStart/condition
        # must remain; review templates must never be runtime-ready.
        if "Install" in actual or actual["Unit"].get("ConditionPathExists") != _SENTINEL:
            raise HMLSupervisorBlueprintError("HML_BLUEPRINT_POLICY_DRIFT")
    return HMLSupervisorBlueprintReview()


def load_repository_blueprint_sources() -> dict[str, str]:
    """Read only checked-in REVIEW files; never a host systemd or Docker path."""
    try:
        return {
            name: (_DIR / name).read_text(encoding="utf-8")
            for name in sorted(_ALLOWED_NAMES)
        }
    except (OSError, UnicodeError, ValueError):
        raise HMLSupervisorBlueprintError("HML_BLUEPRINT_FILES_UNAVAILABLE") from None

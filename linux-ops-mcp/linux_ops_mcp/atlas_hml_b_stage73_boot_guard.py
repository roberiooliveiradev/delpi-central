"""ATLAS HML stage 73: fail-closed boot layout and unit packaging review.

SOURCE ONLY: no tmpfiles invocation, systemd, Docker, key creation, subprocess,
MCP tool, privilege change or host mutation. A matching directory is NOT
independent host attestation and NEVER enables PREPARE/ACT.
"""
from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .atlas_hml_b_candidate_unit_review import (
    _DIR,
    _EXPECTED_TMPFILES,
    _parse,
    review_candidate_unit_sources,
)
from .atlas_hml_b_stage71_readonly_preflight import (
    Stage71ReadOnlyPreflight,
    _DIRECTORY_POLICY,
)
from .atlas_hml_posix_acl_review import has_no_extended_posix_acl

_TMPFILES_NAME = "atlas-hml-runtime-layout.tmpfiles.candidate"
_SIGNER = "atlas-hml-local-signer.service.candidate"
_BRIDGE = "atlas-hml-nonroot-bridge.service.candidate"
_COMMON = {
    "NoNewPrivileges": "yes",
    "ProtectSystem": "strict",
    "ProtectHome": "yes",
    "PrivateTmp": "yes",
    "PrivateDevices": "yes",
    "PrivateNetwork": "yes",
    "ProtectKernelTunables": "yes",
    "ProtectKernelModules": "yes",
    "ProtectKernelLogs": "yes",
    "ProtectControlGroups": "yes",
    "RestrictNamespaces": "yes",
    "RestrictSUIDSGID": "yes",
    "LockPersonality": "yes",
    "RestrictAddressFamilies": "AF_UNIX",
    "CapabilityBoundingSet": "",
    "AmbientCapabilities": "",
    "UMask": "0077",
    "StandardInput": "null",
    "FileDescriptorStoreMax": "0",
}
_ROLE = {
    _SIGNER: {
        "User": "atlas-hml-signer",
        "Group": "atlas-hml-signer",
        "Type": "simple",
        "SupplementaryGroups": "",
        "InaccessiblePaths": "/run/docker.sock /var/run/docker.sock",
        "ReadOnlyPaths": "/run/atlas-hml-signer",
        "ReadWritePaths": "/run/atlas-hml-signer-socket /var/lib/atlas-hml-signer-state",
    },
    _BRIDGE: {
        "User": "atlas-hml-bridge",
        "Group": "atlas-hml-bridge",
        "Type": "oneshot",
        "SupplementaryGroups": "atlas-hml",
        "InaccessiblePaths": (
            "/run/docker.sock /var/run/docker.sock "
            "/run/atlas-hml-signer /var/lib/atlas-hml-signer-state "
            "/var/lib/atlas-hml-signer-keys"
        ),
        "ReadOnlyPaths": "/run/atlas-hml-readonly",
    },
}
_FORBIDDEN_DIRECTIVES = frozenset({
    "Environment", "EnvironmentFile", "PassEnvironment",
    "BindPaths", "BindReadOnlyPaths", "Sockets", "RootDirectory",
    "RootImage", "ExecStartPre", "ExecStartPost", "ExecReload",
    "ExecStopPost", "JoinsNamespaceOf", "NetworkNamespacePath",
    "StandardInputData", "LoadCredential", "SetCredential",
    "ImportCredential", "PermissionsStartOnly", "DynamicUser",
    "Delegate", "SocketDirectory",
})
_BLOCKS = (
    "STAGE73_SOURCE_ONLY_NOT_INSTALLED",
    "TMPFILES_BOOT_RECREATION_NOT_VALIDATED",
    "EFFECTIVE_APPARMOR_NOT_ATTESTED",
    "DOCKER_ALTERNATE_ENDPOINTS_AND_INHERITED_FDS_NOT_ATTESTED",
    "HOST_IDENTITY_SUPPLEMENTARY_GROUPS_NOT_ATTESTED",
    "BOOTSTRAP_GEN1_AND_EXTERNAL_ANCHOR_PENDING",
    "PRIVATE_KEY_GLPI_AND_ROLLBACK_PENDING",
    "PROD_BEFORE_AFTER_HEALTH_NOT_ATTESTED",
    "SEC_01_TO_10_PENDING",
    "OWNER_OPERATIONAL_AUTHORIZATION_REQUIRED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class Stage73ReviewError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Stage73PackageReview:
    candidate_units_reviewed: int
    tmpfiles_directives: int
    status: str = "blocked"
    installed: bool = False
    boot_recreation_attested: bool = False
    host_isolation_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


@dataclass(frozen=True, slots=True)
class Stage73DirectoryCheck:
    path: str
    present: bool
    policy_match: bool
    finding: str


@dataclass(frozen=True, slots=True)
class Stage73IdentityReview:
    findings: tuple[str, ...]
    status: str = "blocked"
    independently_attested: bool = False
    supplementary_groups_attested: bool = False
    can_execute: bool = False


@dataclass(frozen=True, slots=True)
class Stage73PilotGate:
    directory_policy_matches: bool
    identity_primary_policy_matches: bool
    status: str = "blocked"
    independently_attested: bool = False
    operational_authorization: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _sources(sources: dict[str, str] | None) -> dict[str, str]:
    if sources is not None:
        if type(sources) is not dict:
            raise Stage73ReviewError("STAGE73_SOURCES_DENIED")
        return sources
    if not _DIR.is_dir():
        raise Stage73ReviewError("STAGE73_PACKAGE_MISSING")
    return {p.name: p.read_text(encoding="utf-8")
            for p in sorted(_DIR.glob("*.candidate"))}


def _tmpfile_lines(sources: dict[str, str]) -> tuple[str, ...]:
    text = sources[_TMPFILES_NAME]
    lines = tuple(line.strip() for line in text.splitlines()
                  if line.strip() and not line.lstrip().startswith("#"))
    if len(lines) != 5 or set(lines) != _EXPECTED_TMPFILES:
        raise Stage73ReviewError("STAGE73_TMPFILES_POLICY_DENIED")
    actual_paths = tuple(line.split()[1] for line in lines)
    if actual_paths != tuple(item[0] for item in _DIRECTORY_POLICY):
        raise Stage73ReviewError("STAGE73_TMPFILES_ORDER_DENIED")
    return lines


def review_stage73_package(
    sources: dict[str, str] | None = None,
) -> Stage73PackageReview:
    """Check uninstalled candidate units and five deterministic tmpfiles rules."""
    sources = _sources(sources)
    base = review_candidate_unit_sources(sources)
    lines = _tmpfile_lines(sources)
    for filename, role in _ROLE.items():
        sections = _parse(sources[filename])
        service = sections.get("Service", {})
        expected = {**_COMMON, **role}
        if any(service.get(key) != value for key, value in expected.items()):
            raise Stage73ReviewError("STAGE73_SERVICE_BOUNDARY_DENIED")
        if set(service).intersection(_FORBIDDEN_DIRECTIVES):
            raise Stage73ReviewError("STAGE73_SERVICE_INHERITANCE_DENIED")
        if filename == _BRIDGE and "ReadWritePaths" in service:
            raise Stage73ReviewError("STAGE73_BRIDGE_WRITE_DENIED")
        if service.get("ExecStart") != "/usr/bin/false":
            raise Stage73ReviewError("STAGE73_EXEC_MUST_REMAIN_FALSE")
    return Stage73PackageReview(base.files_reviewed, len(lines))


def render_stage73_tmpfiles_payload(
    sources: dict[str, str] | None = None,
) -> str:
    """Return future tmpfiles.d payload IN MEMORY only. Never install it."""
    sources = _sources(sources)
    review_stage73_package(sources)
    lines = _tmpfile_lines(sources)
    return (
        "# ATLAS HML proposed tmpfiles.d payload; manual review/install only\n"
        + "\n".join(lines) + "\n"
    )


def inspect_stage73_directory(
    *, root: Path, path: str, expected_uid: int, expected_gid: int,
    expected_mode: int,
) -> Stage73DirectoryCheck:
    """Read-only FD walk; no-follow every component and deny ACL/owner/mode drift.

    Root is an explicit fixture root or / under a separately approved operator
    observation. Neither outcome is a live host attest or permission to install.
    """
    known_modes = {item[0]: item[3] for item in _DIRECTORY_POLICY}
    if (
        type(root) is not type(Path("/")) or not root.is_absolute()
        or root.is_symlink() or not root.is_dir()
        or type(path) is not str or path not in known_modes
        or type(expected_uid) is not int or expected_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
        or type(expected_mode) is not int
        or expected_mode != known_modes[path]
        or (root == Path("/") and path == "/run/atlas-hml-readonly"
            and expected_uid != 0)
    ):
        raise Stage73ReviewError("STAGE73_DIRECTORY_ARGUMENTS_DENIED")
    flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    ) if all(hasattr(os, x) for x in (
        "O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC"
    )) else None
    if flags is None:
        return Stage73DirectoryCheck(path, False, False, "NOFOLLOW_UNAVAILABLE")
    fd = -1
    try:
        fd = os.open(root, flags)
        for piece in path.lstrip("/").split("/"):
            prior = os.fstat(fd)
            if (
                not stat.S_ISDIR(prior.st_mode)
                or stat.S_IMODE(prior.st_mode) & 0o022
                or not has_no_extended_posix_acl(fd, directory=True)
            ):
                return Stage73DirectoryCheck(path, False, False, "ANCESTOR_DENIED")
            next_fd = os.open(piece, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        checked = os.fstat(fd)
        named = os.stat(root / path.lstrip("/"), follow_symlinks=False)
        if (
            not stat.S_ISDIR(checked.st_mode)
            or checked.st_nlink < 2
            or (checked.st_dev, checked.st_ino, checked.st_mode,
                checked.st_uid, checked.st_gid)
            != (named.st_dev, named.st_ino, named.st_mode,
                named.st_uid, named.st_gid)
            or checked.st_uid != expected_uid
            or checked.st_gid != expected_gid
            or stat.S_IMODE(checked.st_mode) != expected_mode
            or not has_no_extended_posix_acl(fd, directory=True)
        ):
            return Stage73DirectoryCheck(path, True, False, "DAC_OR_ACL_DENIED")
        return Stage73DirectoryCheck(path, True, True, "FD_POLICY_MATCH_UNTRUSTED")
    except FileNotFoundError:
        return Stage73DirectoryCheck(path, False, False, "DIRECTORY_ABSENT")
    except (OSError, ValueError, TypeError):
        return Stage73DirectoryCheck(path, False, False, "PATH_UNVERIFIABLE")
    finally:
        if fd >= 0:
            os.close(fd)


def review_stage73_identities(
    observation: Stage71ReadOnlyPreflight, *, docker_group_gid: int | None = None,
) -> Stage73IdentityReview:
    """Reject primary identity drift; supplementary groups still need live proof."""
    if type(observation) is not Stage71ReadOnlyPreflight:
        raise Stage73ReviewError("STAGE73_OBSERVATION_DENIED")
    if docker_group_gid is not None and (
        type(docker_group_gid) is not int or docker_group_gid <= 0
    ):
        raise Stage73ReviewError("STAGE73_DOCKER_GID_DENIED")
    if tuple(item.name for item in observation.identities) != (
        "atlas-hml", "atlas-hml-bridge", "atlas-hml-signer"
    ):
        raise Stage73ReviewError("STAGE73_IDENTITY_SET_DENIED")
    findings = ["SUPPLEMENTARY_GROUPS_UNATTESTED",
                "OBSERVATION_NOT_INDEPENDENT"]
    uids: list[int] = []
    gids: list[int] = []
    for person in observation.identities:
        if (
            not person.user_present or not person.group_present
            or type(person.uid) is not int or person.uid <= 0
            or type(person.gid) is not int or person.gid <= 0
            or person.user_primary_gid != person.gid
        ):
            findings.append("IDENTITY_DENIED_" + person.name.upper().replace("-", "_"))
            continue
        uids.append(person.uid)
        gids.append(person.gid)
        if docker_group_gid is not None and person.gid == docker_group_gid:
            findings.append("DOCKER_PRIMARY_GROUP_DENIED")
    if len(uids) != 3 or len(gids) != 3 or len(set(uids)) != 3 or len(set(gids)) != 3:
        findings.append("IDENTITY_COLLISION_OR_MISSING")
    return Stage73IdentityReview(tuple(dict.fromkeys(findings)))


def review_stage73_pilot_gate(
    package: Stage73PackageReview,
    identities: Stage73IdentityReview,
    directories: tuple[Stage73DirectoryCheck, ...],
) -> Stage73PilotGate:
    """Evidence classification only; passing fixture checks never enables pilot."""
    if (
        type(package) is not Stage73PackageReview
        or type(identities) is not Stage73IdentityReview
        or type(directories) is not tuple
        or any(type(item) is not Stage73DirectoryCheck for item in directories)
        or tuple(item.path for item in directories)
        != tuple(item[0] for item in _DIRECTORY_POLICY)
    ):
        raise Stage73ReviewError("STAGE73_PILOT_EVIDENCE_DENIED")
    return Stage73PilotGate(
        directory_policy_matches=all(item.policy_match for item in directories),
        identity_primary_policy_matches=not any(
            finding.startswith(("IDENTITY_", "DOCKER_PRIMARY_"))
            for finding in identities.findings
        ),
    )

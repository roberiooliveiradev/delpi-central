"""ATLAS stage 71: bounded, read-only local preflight candidate.

This collector is NOT deployed or automatically called. It does not invoke
Docker, systemd, subprocess, network APIs or privileged commands. It only
reads metadata of allowlisted paths and Linux identity records. Even a complete
result is an *untrusted self-observation*, not independent SEC attestation.
"""
from __future__ import annotations

import grp
import os
import pwd
import stat
from dataclasses import dataclass
from pathlib import Path

from .atlas_hml_posix_acl_review import has_no_extended_posix_acl

_IDENTITY_NAMES = ("atlas-hml", "atlas-hml-bridge", "atlas-hml-signer")
_DIRECTORY_POLICY: tuple[tuple[str, str, str, int], ...] = (
    ("/run/atlas-hml-readonly", "root", "atlas-hml", 0o750),
    ("/run/atlas-hml-signer", "atlas-hml-signer", "atlas-hml-signer", 0o750),
    ("/run/atlas-hml-signer-socket", "atlas-hml-signer", "atlas-hml-bridge", 0o2750),
    ("/var/lib/atlas-hml-signer-state", "atlas-hml-signer", "atlas-hml-signer", 0o750),
    ("/var/lib/atlas-hml-signer-keys", "atlas-hml-signer", "atlas-hml-signer", 0o700),
)
_UNIT_NAMES = (
    "atlas-hml-snapshot-producer.service",
    "atlas-hml-snapshot-producer.timer",
    "atlas-hml-local-signer.service",
    "atlas-hml-nonroot-bridge.service",
    "atlas-hml-snapshot-presenter.service",
)
_SYSTEMD_LOCATIONS = ("etc/systemd/system", "run/systemd/system", "usr/lib/systemd/system")
_BLOCKS = (
    "LOCAL_READONLY_OBSERVATION_NOT_INDEPENDENT",
    "SYSTEMD_RUNTIME_NOT_ATTESTED",
    "DOCKER_ENGINE_AND_ENDPOINTS_NOT_ATTESTED",
    "APPARMOR_EFFECTIVE_PROFILE_NOT_ATTESTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


@dataclass(frozen=True, slots=True)
class Stage71Identity:
    name: str
    user_present: bool
    uid: int | None
    user_primary_gid: int | None
    group_present: bool
    gid: int | None


@dataclass(frozen=True, slots=True)
class Stage71Directory:
    path: str
    present: bool
    mode: int | None
    uid: int | None
    gid: int | None
    acl_absent: bool
    compliant: bool
    finding: str


@dataclass(frozen=True, slots=True)
class Stage71ReadOnlyPreflight:
    identities: tuple[Stage71Identity, ...]
    directories: tuple[Stage71Directory, ...]
    systemd_unit_names_found: tuple[str, ...]
    docker_socket_kind: str
    docker_socket_mode: int | None
    docker_socket_uid: int | None
    docker_socket_gid: int | None
    apparmor_enabled: bool | None
    findings: tuple[str, ...]
    status: str = "blocked"
    host_attested: bool = False
    can_provision: bool = False
    can_execute: bool = False
    prepare_eligible: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _rooted(root: Path, absolute: str) -> Path:
    return root.joinpath(absolute.lstrip("/"))


def _read_apparmor_flag(root: Path) -> bool | None:
    candidate = _rooted(root, "/sys/module/apparmor/parameters/enabled")
    try:
        if candidate.is_symlink():
            return None
        with candidate.open("rb") as handle:
            flag = handle.read(8).strip()
        if flag == b"Y":
            return True
        if flag == b"N":
            return False
    except (OSError, ValueError):
        pass
    return None


def _directory_observation(
    root: Path, target: tuple[str, str, str, int],
    ids: dict[str, Stage71Identity],
) -> Stage71Directory:
    name, owner, group, mode = target
    path = _rooted(root, name)
    try:
        st = os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        return Stage71Directory(name, False, None, None, None, False, False, "ABSENT")
    except OSError:
        return Stage71Directory(name, False, None, None, None, False, False, "UNVERIFIABLE")
    if not stat.S_ISDIR(st.st_mode):
        return Stage71Directory(name, True, stat.S_IMODE(st.st_mode), st.st_uid, st.st_gid,
                                False, False, "NOT_DIRECTORY")

    expected_owner = 0 if owner == "root" else ids[owner].uid
    expected_group = ids[group].gid
    actual_mode = stat.S_IMODE(st.st_mode)
    valid_dac = (
        expected_owner is not None and expected_group is not None
        and st.st_uid == expected_owner and st.st_gid == expected_group
        and actual_mode == mode
    )
    acl_absent = False
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            after = os.fstat(fd)
            if (after.st_dev, after.st_ino) == (st.st_dev, st.st_ino):
                acl_absent = has_no_extended_posix_acl(fd, directory=True)
            else:
                valid_dac = False
        finally:
            os.close(fd)
    except (OSError, AttributeError):
        valid_dac = False
    okay = bool(valid_dac and acl_absent)
    return Stage71Directory(name, True, actual_mode, st.st_uid, st.st_gid,
                            acl_absent, okay, "DAC_MATCH" if okay else "DAC_OR_ACL_DENIED")


def _get_identities(root: Path) -> tuple[Stage71Identity, ...]:
    if root != Path("/"):
        # Fixture root is not the real passwd/group database.
        return tuple(Stage71Identity(name, False, None, None, False, None)
                     for name in _IDENTITY_NAMES)
    result: list[Stage71Identity] = []
    for name in _IDENTITY_NAMES:
        try:
            user = pwd.getpwnam(name)
        except KeyError:
            user = None
        try:
            group = grp.getgrnam(name)
        except KeyError:
            group = None
        result.append(Stage71Identity(
            name, user is not None, user.pw_uid if user else None,
            user.pw_gid if user else None, group is not None,
            group.gr_gid if group else None,
        ))
    return tuple(result)


def collect_stage71_readonly(*, root: Path) -> Stage71ReadOnlyPreflight:
    """Explicit call only; no side effects or automatic host invocation.

    On fixture roots the identity database is intentionally marked unknown.
    This API does not claim that no Docker TCP endpoint exists; that requires
    separately reviewed evidence. Do not execute on srv-api without approval.
    """
    if type(root) is not type(Path("/")) or not root.is_absolute() or root.is_symlink():
        raise ValueError("STAGE71_ROOT_DENIED")
    identities = _get_identities(root)
    ids = {item.name: item for item in identities}
    directories = tuple(_directory_observation(root, item, ids)
                        for item in _DIRECTORY_POLICY)
    found: list[str] = []
    for unit in _UNIT_NAMES:
        for base in _SYSTEMD_LOCATIONS:
            candidate = root / base / unit
            try:
                os.stat(candidate, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError:
                found.append(unit + ":unverifiable")
            else:
                found.append(unit)
            break

    dock = _rooted(root, "/run/docker.sock")
    try:
        st = os.stat(dock, follow_symlinks=False)
        kind = "socket" if stat.S_ISSOCK(st.st_mode) else "unexpected_object"
        socket_mode, socket_uid, socket_gid = stat.S_IMODE(st.st_mode), st.st_uid, st.st_gid
    except FileNotFoundError:
        kind, socket_mode, socket_uid, socket_gid = "absent", None, None, None
    except OSError:
        kind, socket_mode, socket_uid, socket_gid = "unverifiable", None, None, None

    findings = ["PROBE_UNTRUSTED", "DOCKER_TCP_ENDPOINTS_UNOBSERVED",
                "EFFECTIVE_APPARMOR_PROFILE_UNOBSERVED"]
    if found:
        findings.append("ATLAS_UNIT_PRESENT_MANUAL_REVIEW")
    if kind != "socket":
        findings.append("DOCKER_SOCKET_NOT_ATTESTED")
    if any(not identity.user_present or not identity.group_present
           for identity in identities):
        findings.append("ATLAS_IDENTITY_ABSENT_OR_UNKNOWN")
    if any(directory.present and not directory.compliant for directory in directories):
        findings.append("ATLAS_DIRECTORY_DAC_DENIED")
    return Stage71ReadOnlyPreflight(
        identities=identities, directories=directories,
        systemd_unit_names_found=tuple(sorted(set(found))),
        docker_socket_kind=kind, docker_socket_mode=socket_mode,
        docker_socket_uid=socket_uid, docker_socket_gid=socket_gid,
        apparmor_enabled=_read_apparmor_flag(root),
        findings=tuple(findings),
    )

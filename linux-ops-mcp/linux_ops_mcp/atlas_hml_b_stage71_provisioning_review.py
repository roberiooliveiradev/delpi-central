"""ATLAS stage 71: non-operational provisioning review.

Emits a deterministic, human-reviewable plan from a read-only observation.
No useradd, groupadd, chmod, chown, systemd, Docker, GLPI or shell execution.
Even an apparently compliant observation cannot authorize a host change.
"""
from __future__ import annotations

from dataclasses import dataclass

from .atlas_hml_b_stage71_readonly_preflight import (
    Stage71ReadOnlyPreflight,
)

_TARGETS = (
    ("atlas-hml-bridge", "system-user", "nonlogin; own primary group; no Docker"),
    ("atlas-hml-signer", "system-user", "nonlogin; own primary group; no Docker"),
    ("/run/atlas-hml-readonly", "directory", "root:atlas-hml 0750"),
    ("/run/atlas-hml-signer", "directory", "atlas-hml-signer:atlas-hml-signer 0750"),
    ("/run/atlas-hml-signer-socket", "directory", "atlas-hml-signer:atlas-hml-bridge 02750"),
    ("/var/lib/atlas-hml-signer-state", "directory", "atlas-hml-signer:atlas-hml-signer 0750"),
    ("/var/lib/atlas-hml-signer-keys", "directory", "atlas-hml-signer:atlas-hml-signer 0700"),
)
_BLOCKS = (
    "STAGE71_PLAN_ONLY",
    "OWNER_CHANGE_CONTROL_REQUIRED",
    "SUPPLEMENTARY_GROUPS_NOT_ATTESTED",
    "APPARMOR_PROFILE_NOT_ATTESTED",
    "DOCKER_ENDPOINTS_AND_FDS_NOT_ATTESTED",
    "ROOT_HOST_RESIDUAL",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


@dataclass(frozen=True, slots=True)
class Stage71ProvisionStep:
    target: str
    kind: str
    desired: str
    action: str = "OWNER_AUTHORIZATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class Stage71ProvisioningReview:
    steps: tuple[Stage71ProvisionStep, ...]
    findings: tuple[str, ...]
    status: str = "blocked"
    host_attested: bool = False
    change_authorized: bool = False
    commands_generated: bool = False
    can_execute: bool = False
    prepare_eligible: bool = False
    progress_percent_reference: int = 60
    blocks: tuple[str, ...] = _BLOCKS


def build_stage71_provisioning_review(
    observation: Stage71ReadOnlyPreflight, *, docker_group_gid: int | None = None,
) -> Stage71ProvisioningReview:
    if type(observation) is not Stage71ReadOnlyPreflight:
        raise ValueError("STAGE71_OBSERVATION_DENIED")
    if docker_group_gid is not None and (
        type(docker_group_gid) is not int or docker_group_gid <= 0
    ):
        raise ValueError("STAGE71_DOCKER_GID_DENIED")
    if tuple(item.name for item in observation.identities) != (
        "atlas-hml", "atlas-hml-bridge", "atlas-hml-signer"
    ):
        raise ValueError("STAGE71_IDENTITY_SET_DENIED")
    findings = ["HOST_ATTESTATION_PENDING", "OWNER_APPROVAL_PENDING",
                "SUPPLEMENTARY_GROUPS_UNVERIFIED", "SEC_01_TO_10_PENDING"]
    uids: list[int] = []
    gids: list[int] = []
    for identity in observation.identities:
        if not identity.user_present or not identity.group_present:
            findings.append("IDENTITY_MISSING_" + identity.name.upper().replace("-", "_"))
            continue
        if (
            identity.uid is None or identity.user_primary_gid is None
            or identity.gid is None
            or identity.uid <= 0 or identity.gid <= 0
            or identity.user_primary_gid != identity.gid
        ):
            findings.append("IDENTITY_DAC_INVALID_" + identity.name.upper().replace("-", "_"))
            continue
        uids.append(identity.uid)
        gids.append(identity.gid)
        if docker_group_gid is not None and identity.gid == docker_group_gid:
            findings.append("DOCKER_PRIMARY_GROUP_DENIED")
    if len(uids) != len(set(uids)) or len(gids) != len(set(gids)):
        findings.append("IDENTITY_COLLISION_DENIED")

    names = tuple(item.path for item in observation.directories)
    expected = tuple(item[0] for item in _TARGETS[2:])
    if names != expected:
        raise ValueError("STAGE71_DIRECTORY_SET_DENIED")
    for item in observation.directories:
        if not item.present:
            findings.append("DIRECTORY_MISSING_" + item.path.rsplit("/", 1)[-1].upper().replace("-", "_"))
        elif not item.compliant:
            findings.append("DIRECTORY_POLICY_DENIED_" + item.path.rsplit("/", 1)[-1].upper().replace("-", "_"))
    if observation.systemd_unit_names_found:
        findings.append("SYSTEMD_ATLAS_UNEXPECTED_REVIEW_REQUIRED")
    if observation.docker_socket_kind != "socket":
        findings.append("DOCKER_SOCKET_UNVERIFIABLE")
    if observation.apparmor_enabled is not True:
        findings.append("APPARMOR_ENABLEMENT_UNCONFIRMED")
    return Stage71ProvisioningReview(
        steps=tuple(Stage71ProvisionStep(*part) for part in _TARGETS),
        findings=tuple(dict.fromkeys(findings)),
    )

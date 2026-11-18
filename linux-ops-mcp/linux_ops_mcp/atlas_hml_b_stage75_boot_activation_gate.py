"""ATLAS HML stage 75: mandatory boot activation gate (source-only).

Composes stage 73 directory inspection, stage 74 no-clobber/conflict audit and
rollback inventory. Fail-closed when directories exist with wrong DAC/ACL/setgid
even if a prior tmpfiles create-only run reported success. Never installs
units, never mutates the host, never enables PREPARE/ACT.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .atlas_hml_b_stage71_readonly_preflight import _DIRECTORY_POLICY, _UNIT_NAMES
from .atlas_hml_b_stage73_boot_guard import (
    Stage73DirectoryCheck,
    Stage73PackageReview,
    Stage73PilotGate,
    inspect_stage73_directory,
    review_stage73_package,
    review_stage73_pilot_gate,
    review_stage73_identities,
)
from .atlas_hml_b_stage71_readonly_preflight import Stage71ReadOnlyPreflight
from .atlas_hml_b_stage74_tmpfiles_audit import (
    Stage74BootAudit,
    audit_stage74_boot_config,
    review_no_clobber_candidate,
)

_ATLAS_ONLY_ROLLBACK = (
    "atlas-hml-runtime-layout.tmpfiles.candidate",
    "atlas-hml-local-signer.service.candidate",
    "atlas-hml-nonroot-bridge.service.candidate",
    "atlas-hml-snapshot-producer.service.candidate",
    "atlas-hml-snapshot-producer.timer.candidate",
    "atlas-hml-snapshot-presenter.service.candidate",
    "/run/atlas-hml-readonly",
    "/run/atlas-hml-signer",
    "/run/atlas-hml-signer-socket",
    "/var/lib/atlas-hml-signer-state",
    "/var/lib/atlas-hml-signer-keys",
)
_STOP = (
    "DIRECTORY_POLICY_MISMATCH",
    "TMPFILES_CONFLICT_OR_CLOBBERABLE",
    "ATLAS_UNIT_ALREADY_PRESENT",
    "SYMLINK_OR_INODE_SUBSTITUTION",
    "DOCKER_ENGINE_IMPACT_RISK",
    "NON_ATLAS_SHARED_PATH_MUTATION",
    "OWNER_AUTHORIZATION_MISSING",
)
_BLOCKS = (
    "STAGE75_SOURCE_ONLY_NOT_INSTALLED",
    "BOOT_GATE_NOT_HOST_ATTESTATION",
    "POST_REBOOT_CRITERIA_NOT_HOST_PROVEN",
    "SEC_01_TO_10_PENDING",
    "OPERATIONAL_CHANGE_CONTROL_REQUIRED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class Stage75BootGateError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class Stage75RollbackInventory:
    atlas_only_components: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    status: str = "blocked"
    host_rollback_executed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


@dataclass(frozen=True, slots=True)
class Stage75PostCreateValidation:
    directories: tuple[Stage73DirectoryCheck, ...]
    all_present: bool
    all_policy_match: bool
    rejected_codes: tuple[str, ...]
    status: str = "blocked"
    tmpfiles_success_ignored_on_drift: bool = True
    prepare_eligible: bool = False
    can_execute: bool = False


@dataclass(frozen=True, slots=True)
class Stage75BootActivationGate:
    package: Stage73PackageReview
    no_clobber: bool
    boot_audit: Stage74BootAudit
    post_create: Stage75PostCreateValidation
    rollback: Stage75RollbackInventory
    pilot: Stage73PilotGate | None
    status: str = "blocked"
    activation_authorized: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def build_atlas_only_rollback_inventory() -> Stage75RollbackInventory:
    """Typed inventory of exclusive ATLAS artifacts eligible for future rollback."""
    return Stage75RollbackInventory(
        atlas_only_components=_ATLAS_ONLY_ROLLBACK,
        stop_conditions=_STOP,
    )


def validate_post_create_directories(
    *,
    root: Path,
    uid_map: dict[str, int],
    gid_map: dict[str, int],
    claim_tmpfiles_succeeded: bool = False,
) -> Stage75PostCreateValidation:
    """Reject wrong DAC even when tmpfiles reported success (create-only semantics).

    uid_map/gid_map keys are Linux account names from _DIRECTORY_POLICY.
    """
    if (
        type(root) is not type(Path("/"))
        or not root.is_absolute()
        or root.is_symlink()
        or not root.is_dir()
        or type(uid_map) is not dict
        or type(gid_map) is not dict
        or type(claim_tmpfiles_succeeded) is not bool
    ):
        raise Stage75BootGateError("STAGE75_POST_CREATE_ARGS_DENIED")
    required_names = {owner for _, owner, _, _ in _DIRECTORY_POLICY} | {
        group for _, _, group, _ in _DIRECTORY_POLICY
    }
    if set(uid_map) < required_names or set(gid_map) < required_names:
        raise Stage75BootGateError("STAGE75_IDENTITY_MAP_INCOMPLETE")
    if any(type(v) is not int or v < 0 for v in uid_map.values()):
        raise Stage75BootGateError("STAGE75_UID_MAP_DENIED")
    if any(type(v) is not int or v <= 0 for v in gid_map.values()):
        raise Stage75BootGateError("STAGE75_GID_MAP_DENIED")

    checks: list[Stage73DirectoryCheck] = []
    rejected: list[str] = []
    for path, owner, group, mode in _DIRECTORY_POLICY:
        item = inspect_stage73_directory(
            root=root,
            path=path,
            expected_uid=uid_map[owner],
            expected_gid=gid_map[group],
            expected_mode=mode,
        )
        checks.append(item)
        if not item.present:
            rejected.append("ABSENT:" + path)
        elif not item.policy_match:
            rejected.append("DRIFT:" + path + ":" + item.finding)
            if claim_tmpfiles_succeeded:
                rejected.append("TMPFILES_SUCCESS_MASKED_DRIFT:" + path)
        if item.finding in {"ANCESTOR_DENIED", "PATH_UNVERIFIABLE"}:
            rejected.append("INODE_OR_SYMLINK_RISK:" + path)

    return Stage75PostCreateValidation(
        directories=tuple(checks),
        all_present=all(c.present for c in checks),
        all_policy_match=all(c.policy_match for c in checks),
        rejected_codes=tuple(dict.fromkeys(rejected)),
    )


def evaluate_stage75_boot_activation_gate(
    *,
    fixture_root: Path | None = None,
    uid_map: dict[str, int] | None = None,
    gid_map: dict[str, int] | None = None,
    identities: Stage71ReadOnlyPreflight | None = None,
    claim_tmpfiles_succeeded: bool = False,
    host_readonly_root: Path | None = None,
) -> Stage75BootActivationGate:
    """Compose package, no-clobber, conflict audit and post-create fail-closed gate."""
    package = review_stage73_package()
    no_clobber = review_no_clobber_candidate()
    if fixture_root is not None and host_readonly_root is not None:
        raise Stage75BootGateError("STAGE75_ROOT_SCOPE_AMBIGUOUS")
    if fixture_root is not None:
        boot_audit = audit_stage74_boot_config(root=fixture_root, host_readonly=False)
        root = fixture_root
    elif host_readonly_root is not None:
        boot_audit = audit_stage74_boot_config(
            root=host_readonly_root, host_readonly=(host_readonly_root == Path("/")),
        )
        root = host_readonly_root
    else:
        boot_audit = Stage74BootAudit(
            config_files_scanned=0,
            config_dirs_present=0,
            candidate_no_clobber=no_clobber,
            finding_codes=("STAGE75_NO_ROOT_SCOPED_AUDIT", "HOST_ATTESTATION_NOT_INDEPENDENT"),
        )
        root = None

    if root is not None and uid_map is not None and gid_map is not None:
        post = validate_post_create_directories(
            root=root,
            uid_map=uid_map,
            gid_map=gid_map,
            claim_tmpfiles_succeeded=claim_tmpfiles_succeeded,
        )
    else:
        post = Stage75PostCreateValidation(
            directories=tuple(
                Stage73DirectoryCheck(path, False, False, "DIRECTORY_ABSENT")
                for path, _, _, _ in _DIRECTORY_POLICY
            ),
            all_present=False,
            all_policy_match=False,
            rejected_codes=("STAGE75_POST_CREATE_SKIPPED",),
        )

    pilot = None
    if identities is not None and uid_map is not None and gid_map is not None:
        id_review = review_stage73_identities(identities)
        pilot = review_stage73_pilot_gate(package, id_review, post.directories)

    rollback = build_atlas_only_rollback_inventory()
    if boot_audit.finding_codes:
        # Keep fail-closed classification even with empty findings on fixture.
        pass
    return Stage75BootActivationGate(
        package=package,
        no_clobber=no_clobber,
        boot_audit=boot_audit,
        post_create=post,
        rollback=rollback,
        pilot=pilot,
    )


def render_post_reboot_validation_criteria() -> dict[str, object]:
    """Machine-readable criteria for a future authorized reboot window."""
    return {
        "schema": "atlas.hml.b.post-reboot-validation.v1",
        "status": "blocked",
        "require_create_only_tmpfiles": True,
        "require_post_create_policy_match": True,
        "reject_on_tmpfiles_success_with_dac_drift": True,
        "atlas_only_rollback_components": list(_ATLAS_ONLY_ROLLBACK),
        "stop_conditions": list(_STOP),
        "prepare_eligible": False,
        "can_execute": False,
        "unit_names_must_remain_absent_until_authorized": list(_UNIT_NAMES),
    }


def main() -> int:
    payload = {
        "gate": "stage75",
        "status": "blocked",
        "rollback": build_atlas_only_rollback_inventory().__dict__,
        "post_reboot": render_post_reboot_validation_criteria(),
        "prepare_eligible": False,
        "can_execute": False,
    }
    # dataclasses with nested objects need json via asdict-like; keep simple
    print(json.dumps({
        "gate": "stage75",
        "status": "blocked",
        "atlas_only_components": list(_ATLAS_ONLY_ROLLBACK),
        "stop_conditions": list(_STOP),
        "post_reboot": render_post_reboot_validation_criteria(),
        "prepare_eligible": False,
        "can_execute": False,
    }, indent=2, sort_keys=True))
    return 2  # blocked exit


if __name__ == "__main__":
    raise SystemExit(main())

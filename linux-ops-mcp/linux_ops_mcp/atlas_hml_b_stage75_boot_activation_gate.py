"""ATLAS HML stage 75/76: mandatory boot activation gate (source-only).

Composes stage 73 directory inspection, stage 74 classified tmpfiles audit and
rollback inventory. Fail-closed when directories exist with wrong DAC/ACL/setgid
even if a prior tmpfiles create-only run reported success. Never installs
units, never mutates the host, never enables PREPARE/ACT.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

from .atlas_hml_b_stage71_readonly_preflight import (
    Stage71ReadOnlyPreflight,
    _DIRECTORY_POLICY,
    _UNIT_NAMES,
)
from .atlas_hml_b_stage73_boot_guard import (
    Stage73DirectoryCheck,
    Stage73PackageReview,
    Stage73PilotGate,
    inspect_stage73_directory,
    review_stage73_identities,
    review_stage73_package,
    review_stage73_pilot_gate,
)
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


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def build_atlas_only_rollback_inventory() -> Stage75RollbackInventory:
    return Stage75RollbackInventory(
        atlas_only_components=_ATLAS_ONLY_ROLLBACK,
        stop_conditions=_STOP,
    )


def _validate_identity_maps(
    uid_map: dict[str, int], gid_map: dict[str, int],
) -> None:
    required_names = {owner for _, owner, _, _ in _DIRECTORY_POLICY} | {
        group for _, _, group, _ in _DIRECTORY_POLICY
    }
    if set(uid_map) < required_names or set(gid_map) < required_names:
        raise Stage75BootGateError("STAGE75_IDENTITY_MAP_INCOMPLETE")
    for name, value in uid_map.items():
        if type(value) is not int or value < 0:
            raise Stage75BootGateError("STAGE75_UID_MAP_DENIED")
        if name != "root" and value == 0:
            raise Stage75BootGateError("STAGE75_UID_MAP_DENIED")
    for name, value in gid_map.items():
        if type(value) is not int or value < 0:
            raise Stage75BootGateError("STAGE75_GID_MAP_DENIED")
        # GID 0 is legitimate only for the root group required by policy.
        if value == 0 and name != "root":
            raise Stage75BootGateError("STAGE75_GID_MAP_DENIED")
        if value == 0 and name == "root":
            continue
        if value <= 0:
            raise Stage75BootGateError("STAGE75_GID_MAP_DENIED")


def validate_post_create_directories(
    *,
    root: Path,
    uid_map: dict[str, int],
    gid_map: dict[str, int],
    claim_tmpfiles_succeeded: bool = False,
) -> Stage75PostCreateValidation:
    """Reject wrong DAC even when tmpfiles reported success (create-only)."""
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
    _validate_identity_maps(uid_map, gid_map)

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
            if item.finding == "DAC_OR_ACL_DENIED":
                # Distinguish mode/owner/ACL/setgid class without trusting tmpfiles.
                rejected.append("DAC_ACL_OR_SETGID_DENIED:" + path)
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
            root=host_readonly_root,
            host_readonly=(host_readonly_root == Path("/")),
        )
        root = host_readonly_root
    else:
        boot_audit = Stage74BootAudit(
            config_files_scanned=0,
            config_dirs_present=0,
            candidate_no_clobber=no_clobber,
            findings=(),
            finding_codes=("STAGE75_NO_ROOT_SCOPED_AUDIT", "HOST_ATTESTATION_NOT_INDEPENDENT"),
            critical_codes=("STAGE75_NO_ROOT_SCOPED_AUDIT",),
            info_codes=(),
        )
        root = None

    critical_tmpfiles = bool(boot_audit.critical_codes)
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

    if critical_tmpfiles and "TMPFILES_CRITICAL_CONFLICT" not in post.rejected_codes:
        # Surface tmpfiles criticals into the gate without promoting activation.
        post = Stage75PostCreateValidation(
            directories=post.directories,
            all_present=post.all_present,
            all_policy_match=post.all_policy_match and not critical_tmpfiles,
            rejected_codes=tuple(dict.fromkeys(
                (*post.rejected_codes, "TMPFILES_CRITICAL_CONFLICT")
            )),
        )

    pilot = None
    if identities is not None and uid_map is not None and gid_map is not None:
        id_review = review_stage73_identities(identities)
        pilot = review_stage73_pilot_gate(package, id_review, post.directories)

    return Stage75BootActivationGate(
        package=package,
        no_clobber=no_clobber,
        boot_audit=boot_audit,
        post_create=post,
        rollback=build_atlas_only_rollback_inventory(),
        pilot=pilot,
    )


def render_post_reboot_validation_criteria() -> dict[str, object]:
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


def build_stage75_cli_report(
    gate: Stage75BootActivationGate | None = None,
) -> dict[str, Any]:
    inventory = build_atlas_only_rollback_inventory()
    payload: dict[str, Any] = {
        "schema": "atlas.hml.stage75.boot-gate.v1",
        "gate": "stage75",
        "status": "blocked",
        "error_code": "STAGE75_BLOCKED_NOT_AUTHORIZED",
        "activation_authorized": False,
        "prepare_eligible": False,
        "can_execute": False,
        "rollback": _jsonable(inventory),
        "post_reboot": render_post_reboot_validation_criteria(),
        "blocks": list(_BLOCKS),
    }
    if gate is not None:
        payload["evaluation"] = _jsonable(gate)
        payload["error_code"] = (
            "STAGE75_TMPFILES_OR_DAC_DENIED"
            if gate.post_create.rejected_codes
            else "STAGE75_BLOCKED_NOT_AUTHORIZED"
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ATLAS Stage75 boot activation gate")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--fixture-root", type=Path, metavar="ABSOLUTE_DIR")
    scope.add_argument("--host-readonly", action="store_true")
    parser.add_argument("--claim-tmpfiles-succeeded", action="store_true")
    args = parser.parse_args(argv)

    gate = None
    if args.fixture_root is not None or args.host_readonly:
        root = Path("/") if args.host_readonly else args.fixture_root
        if (
            root is None
            or not root.is_absolute()
            or root.is_symlink()
            or not root.is_dir()
        ):
            parser.error("STAGE75_ROOT_DENIED")
        if args.host_readonly:
            gate = evaluate_stage75_boot_activation_gate(
                host_readonly_root=root,
                claim_tmpfiles_succeeded=args.claim_tmpfiles_succeeded,
            )
        else:
            gate = evaluate_stage75_boot_activation_gate(
                fixture_root=root,
                claim_tmpfiles_succeeded=args.claim_tmpfiles_succeeded,
            )
    print(json.dumps(build_stage75_cli_report(gate), sort_keys=True, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

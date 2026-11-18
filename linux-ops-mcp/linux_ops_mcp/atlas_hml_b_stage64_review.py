"""ATLAS stage 64: OFFLINE pre-activation evidence review, never an executor.

Only validates an untrusted, manually collected HML dossier. It does not read
host files, open sockets, spawn processes, generate keys or authorize a pilot.
All returns, including complete evidence, are permanently BLOCKED.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.preactivation-v1"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_REQUIRED = frozenset({
    "owner_change_record", "independent_security_decision", "real_host_baseline",
    "docker_aliases_and_inherited_fds", "systemd_effective_units",
    "uid_gid_acl_capabilities_lsm", "socket_peer_authentication",
    "signer_bootstrap_anchor", "key_custody_escrow", "hml_negative_tests",
    "prod_unchanged_baseline", "atlas_only_rollback", "change_window",
})
_ROLES = {
    "producer": "root",
    "bridge": "atlas-hml-bridge",
    "signer": "atlas-hml-signer",
    "presenter": "atlas-hml",
}
_FIELDS = frozenset({
    "schema", "host", "environment", "target", "revision_sha",
    "source", "systemd_installed", "key_generated", "mcp_tools",
    "prepare_enabled", "act_enabled", "roles", "evidence",
})
_BLOCKS = (
    "UNTRUSTED_OFFLINE_DOSSIER",
    "REAL_PID_AND_DOCKER_BOUNDARIES_NOT_ATTESTED",
    "OWNER_CHANGE_CONTROL_NOT_EXECUTED",
    "BOOTSTRAP_AND_KEY_CUSTODY_NOT_ATTESTED",
    "SYSTEMD_INSTALLATION_NOT_AUTHORIZED",
    "PREPARE_DISABLED", "ACT_DISABLED",
)


class HMLStage64ReviewError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLStage64Review:
    status: str = "blocked"
    scope: str = "hml/public-hub"
    evidence_items: int = 0
    declared_present: int = 0
    host_attested: bool = False
    owner_authorization_granted: bool = False
    signer_bootstrap_approved: bool = False
    systemd_installed: bool = False
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HMLStage64ReviewError("ATLAS64_DUPLICATE_JSON_FIELD")
        result[key] = value
    return result


def _constant(_: str) -> object:
    raise HMLStage64ReviewError("ATLAS64_INVALID_JSON")


def review_untrusted_stage64_dossier(raw: bytes) -> HMLStage64Review:
    """Offline contract. 'present' is merely a claim, never security proof."""
    if type(raw) is not bytes or not 1 <= len(raw) <= 16384 or b"\x00" in raw:
        raise HMLStage64ReviewError("ATLAS64_INVALID_INPUT")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique,
                         parse_constant=_constant)
    except HMLStage64ReviewError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise HMLStage64ReviewError("ATLAS64_INVALID_JSON") from None
    if type(doc) is not dict or set(doc) != _FIELDS:
        raise HMLStage64ReviewError("ATLAS64_SCHEMA_DENIED")
    if (
        doc["schema"] != _SCHEMA
        or doc["host"] != "srv-api"
        or doc["environment"] != "hml"
        or doc["target"] != "delpi-hml-public-hub"
        or doc["source"] != "untrusted_manual_evidence_index"
        or type(doc["revision_sha"]) is not str
        or _SHA.fullmatch(doc["revision_sha"]) is None
        or doc["systemd_installed"] is not False
        or doc["key_generated"] is not False
        or doc["prepare_enabled"] is not False
        or doc["act_enabled"] is not False
        or doc["mcp_tools"] != [
            "get_deployment_revision", "get_host_health",
            "get_service_health", "list_managed_services",
        ]
        or type(doc["roles"]) is not dict or doc["roles"] != _ROLES
    ):
        raise HMLStage64ReviewError("ATLAS64_SCOPE_OR_POLICY_DENIED")
    evidence = doc["evidence"]
    if type(evidence) is not dict or set(evidence) != _REQUIRED:
        raise HMLStage64ReviewError("ATLAS64_EVIDENCE_SET_DENIED")
    for value in evidence.values():
        if type(value) is not str or value not in ("missing", "declared_present_untrusted"):
            raise HMLStage64ReviewError("ATLAS64_EVIDENCE_VALUE_DENIED")
    return HMLStage64Review(
        evidence_items=len(evidence),
        declared_present=sum(v == "declared_present_untrusted" for v in evidence.values()),
    )

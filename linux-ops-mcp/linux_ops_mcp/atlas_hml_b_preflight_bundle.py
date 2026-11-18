"""Structured offline/host-observation preflight for ATLAS HML (source-only).

Accepts an untrusted observation dossier collected by an operator or future
read-only helper. Emits sanitized, fail-closed codes. Never prints secrets,
never mutates host state, never treats self-declared fields as SEC attestation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.preflight-bundle.v1"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_FIELDS = frozenset({
    "schema", "host", "environment", "revision_sha", "os_release_id",
    "users_present", "groups_present", "paths", "sockets", "systemd_units",
    "docker_endpoints", "hml_container", "prod_container", "capabilities",
    "secrets_redacted", "prepare_enabled", "act_enabled", "mcp_tools",
})
_PATH_KEYS = frozenset({
    "snapshot_dir", "signer_socket_dir", "signer_key_dir", "signer_state_dir",
})
_SOCKET_KEYS = frozenset({"presenter", "signer"})
_UNIT_KEYS = frozenset({
    "producer", "producer_timer", "signer", "bridge", "presenter",
})
_DOCKER = frozenset({
    "unix_docker_sock", "unix_containerd", "tcp_endpoint_detected",
})
_MCP = [
    "get_deployment_revision", "get_host_health",
    "get_service_health", "list_managed_services",
]
_BLOCKS = (
    "PREFLIGHT_DOSSIER_UNTRUSTED",
    "NOT_INDEPENDENT_SEC_ATTESTATION",
    "HOST_MUTATION_NOT_PERFORMED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLPreflightBundleError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLPreflightFinding:
    code: str
    severity: str
    blocking: bool


@dataclass(frozen=True, slots=True)
class HMLPreflightBundleReview:
    findings: tuple[HMLPreflightFinding, ...]
    status: str = "blocked"
    host_attested: bool = False
    secrets_exposed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLPreflightBundleError("HML_PREFLIGHT_DUPLICATE_FIELD")
        out[key] = value
    return out


def _constant(_: str) -> object:
    raise HMLPreflightBundleError("HML_PREFLIGHT_JSON_INVALID")


def _bool_map(value: object, keys: frozenset[str]) -> dict[str, bool]:
    if type(value) is not dict or set(value) != keys:
        raise HMLPreflightBundleError("HML_PREFLIGHT_MAP_DENIED")
    out: dict[str, bool] = {}
    for key in keys:
        item = value[key]
        if type(item) is not bool:
            raise HMLPreflightBundleError("HML_PREFLIGHT_MAP_DENIED")
        out[key] = item
    return out


def review_untrusted_preflight_bundle(raw: bytes) -> HMLPreflightBundleReview:
    if type(raw) is not bytes or not 1 <= len(raw) <= 16384 or b"\x00" in raw:
        raise HMLPreflightBundleError("HML_PREFLIGHT_INPUT_DENIED")
    # Reject obvious secret material in the dossier bytes.
    lowered = raw.lower()
    for token in (b"begin private", b"password=", b"token=", b"secret=", b"api_key"):
        if token in lowered:
            raise HMLPreflightBundleError("HML_PREFLIGHT_SECRET_MATERIAL_DENIED")
    try:
        doc = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant,
        )
    except HMLPreflightBundleError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise HMLPreflightBundleError("HML_PREFLIGHT_JSON_INVALID") from None
    if type(doc) is not dict or set(doc) != _FIELDS:
        raise HMLPreflightBundleError("HML_PREFLIGHT_SCHEMA_DENIED")
    if (
        doc["schema"] != _SCHEMA
        or doc["host"] != "srv-api"
        or doc["environment"] != "hml"
        or type(doc["revision_sha"]) is not str
        or _SHA.fullmatch(doc["revision_sha"]) is None
        or type(doc["os_release_id"]) is not str
        or not 1 <= len(doc["os_release_id"]) <= 32
        or doc["secrets_redacted"] is not True
        or doc["prepare_enabled"] is not False
        or doc["act_enabled"] is not False
        or doc["mcp_tools"] != _MCP
    ):
        raise HMLPreflightBundleError("HML_PREFLIGHT_SCOPE_DENIED")

    users = _bool_map(doc["users_present"], frozenset({
        "atlas-hml", "atlas-hml-bridge", "atlas-hml-signer",
    }))
    groups = _bool_map(doc["groups_present"], frozenset({
        "atlas-hml", "atlas-hml-bridge", "atlas-hml-signer",
    }))
    paths = _bool_map(doc["paths"], _PATH_KEYS)
    sockets = _bool_map(doc["sockets"], _SOCKET_KEYS)
    units = _bool_map(doc["systemd_units"], _UNIT_KEYS)
    docker = _bool_map(doc["docker_endpoints"], _DOCKER)
    if type(doc["hml_container"]) is not dict or type(doc["prod_container"]) is not dict:
        raise HMLPreflightBundleError("HML_PREFLIGHT_CONTAINER_DENIED")
    for side in (doc["hml_container"], doc["prod_container"]):
        if set(side) != {"name", "running_claimed"} or type(side["name"]) is not str:
            raise HMLPreflightBundleError("HML_PREFLIGHT_CONTAINER_DENIED")
        if type(side["running_claimed"]) is not bool:
            raise HMLPreflightBundleError("HML_PREFLIGHT_CONTAINER_DENIED")
    if doc["hml_container"]["name"] != "delpi-hml-public-hub":
        raise HMLPreflightBundleError("HML_PREFLIGHT_HML_TARGET_DENIED")
    if doc["prod_container"]["name"] != "delpi-public-hub":
        raise HMLPreflightBundleError("HML_PREFLIGHT_PROD_TARGET_DENIED")
    caps = doc["capabilities"]
    if type(caps) is not dict or set(caps) != {"effective_empty_claimed", "bounding_empty_claimed"}:
        raise HMLPreflightBundleError("HML_PREFLIGHT_CAPS_DENIED")

    findings: list[HMLPreflightFinding] = []
    for label, present in users.items():
        if not present:
            findings.append(HMLPreflightFinding(
                f"USER_MISSING_{label.upper().replace('-', '_')}", "high", True,
            ))
    for label, present in groups.items():
        if not present:
            findings.append(HMLPreflightFinding(
                f"GROUP_MISSING_{label.upper().replace('-', '_')}", "high", True,
            ))
    for label, present in paths.items():
        if not present:
            findings.append(HMLPreflightFinding(
                f"PATH_MISSING_{label.upper()}", "high", True,
            ))
    if docker["tcp_endpoint_detected"]:
        findings.append(HMLPreflightFinding("DOCKER_TCP_ENDPOINT_DETECTED", "critical", True))
    if not doc["hml_container"]["running_claimed"]:
        findings.append(HMLPreflightFinding("HML_CONTAINER_NOT_RUNNING_CLAIM", "medium", True))
    if not any(units.values()):
        findings.append(HMLPreflightFinding("NO_SYSTEMD_UNITS_OBSERVED", "info", False))
    if not findings:
        findings.append(HMLPreflightFinding(
            "DOSSIER_COMPLETE_BUT_UNTRUSTED", "info", True,
        ))
    return HMLPreflightBundleReview(findings=tuple(findings))

"""ATLAS HML Architecture B: offline SEC-01..SEC-10 evidence index review.

This is a strict parser for an OPERATOR-SUPPLIED, UNTRUSTED index of references,
not a host observer, attestation service, or authorization gate. Its output is
ALWAYS blocked even if all ten rows *claim* COMPROVADO. An evidence digest is
only a claim until a separate reviewer independently resolves its source and
checks the bytes on the actual host, and records an authorized decision.

No systemd, Docker, filesystem, sockets, network, subprocess, credentials,
service execution, Keycloak, MCP wiring, PREPARE, ACT or local entrypoint.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_SCHEMA = "atlas.hml.architecture-b.preactivation-evidence.v1"
_SOURCE = "operator_supplied_untrusted"
_IDS = tuple(f"SEC-{n:02d}" for n in range(1, 11))
_MAX_INPUT_BYTES = 12_288
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_REF = re.compile(r"EVID-[A-Z0-9]{8,32}\Z")
_CLAIMS = frozenset({"PENDENTE", "REPROVADO", "COMPROVADO"})
_ORIGINS = {
    "SEC-01": frozenset({"human_independent_claim", "governance_exception_claim"}),
    "SEC-02": frozenset({"host_observation_claim"}),
    "SEC-03": frozenset({"host_observation_claim"}),
    "SEC-04": frozenset({"host_observation_claim"}),
    "SEC-05": frozenset({"host_observation_claim"}),
    "SEC-06": frozenset({"host_observation_claim"}),
    "SEC-07": frozenset({"host_observation_claim"}),
    "SEC-08": frozenset({"independent_verifier_claim"}),
    "SEC-09": frozenset({"change_authorization_claim"}),
    "SEC-10": frozenset({"control_plane_claim"}),
}
_INVARIANT_BLOCKS = (
    "HML_B_EVIDENCE_INDEX_IS_UNTRUSTED",
    "HML_B_DOCKER_PRODUCER_RETAINS_HOST_EQUIVALENT_RISK",
    "HML_B_SEC01_INDEPENDENT_HUMAN_REVIEW_NOT_ATTESTED",
    "HML_B_HOST_PROCESS_FD_AND_ALIAS_ISOLATION_NOT_ATTESTED",
    "HML_B_SNAPSHOT_ORIGIN_AND_REPLAY_NOT_ATTESTED",
    "HML_B_HOST_ROLLBACK_NOT_ATTESTED",
    "HML_B_OPERATIONAL_CHANGE_NOT_AUTHORIZED",
    "CORE_PREPARE_NOT_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLBPreactivationEvidenceError(ValueError):
    """Finite failure code, never a user-supplied field or host path."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLBPreactivationEvidenceReview:
    status: str
    environment: str
    service_id: str
    architecture: str
    source: str
    rows_reviewed: int
    pending_items: tuple[str, ...]
    rejected_items: tuple[str, ...]
    claimed_complete_items: tuple[str, ...]
    claimed_governance_exception: bool
    blocks: tuple[str, ...]
    # These are intentionally immutable FALSE, not derived from input claims.
    independent_human_attestation: bool = False
    host_isolation_attested: bool = False
    privileged_producer_attested: bool = False
    rollback_attested: bool = False
    operational_authorization_granted: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HMLBPreactivationEvidenceError(
                "HML_B_EVIDENCE_DUPLICATE_JSON_FIELD",
            )
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_JSON_INVALID")


def _decode(raw: bytes) -> object:
    if (
        type(raw) is not bytes
        or not 1 <= len(raw) <= _MAX_INPUT_BYTES
        or b"\x00" in raw
    ):
        raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_INPUT_INVALID")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
    except HMLBPreactivationEvidenceError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_JSON_INVALID") from None


def review_untrusted_b_preactivation_evidence(
    raw: bytes,
) -> HMLBPreactivationEvidenceReview:
    """Review only coverage/provenance *claims*, never independently verify them.

    This accepts no host/mount/FD/systemd/socket input and never reads or
    authenticates referenced files. Deliberately no 'approve' operation.
    """
    document = _decode(raw)
    if (
        type(document) is not dict
        or set(document) != {
            "schema", "source", "architecture", "environment",
            "compose_project", "service_id", "container_name",
            "host_claim", "checks",
        }
        or any(
            type(document[key]) is not str or document[key] != wanted
            for key, wanted in {
                "schema": _SCHEMA,
                "source": _SOURCE,
                "architecture": "B",
                "environment": "hml",
                "compose_project": "delpi-hml",
                "service_id": "public-hub",
                "container_name": "delpi-hml-public-hub",
                "host_claim": "srv-api",
            }.items()
        )
    ):
        raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_SCOPE_INVALID")

    checks = document["checks"]
    if type(checks) is not list or len(checks) != len(_IDS):
        raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_MATRIX_INVALID")

    seen: set[str] = set()
    references: set[str] = set()
    pending: list[str] = []
    rejected: list[str] = []
    claimed: list[str] = []
    exception_claimed = False

    for entry in checks:
        if (
            type(entry) is not dict
            or set(entry) != {
                "id", "claimed_result", "origin", "evidence_ref", "sha256",
            }
        ):
            raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_ROW_INVALID")
        key = entry["id"]
        value = entry["claimed_result"]
        origin = entry["origin"]
        reference = entry["evidence_ref"]
        digest = entry["sha256"]
        if (
            type(key) is not str or key not in _ORIGINS or key in seen
            or type(value) is not str or value not in _CLAIMS
            or type(origin) is not str
        ):
            raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_ROW_INVALID")
        seen.add(key)

        if value == "PENDENTE":
            if origin != "not_provided" or reference is not None or digest is not None:
                raise HMLBPreactivationEvidenceError(
                    "HML_B_EVIDENCE_PENDING_CONTRADICTION",
                )
            pending.append(key)
            continue

        if (
            origin not in _ORIGINS[key]
            or type(reference) is not str
            or _REF.fullmatch(reference) is None
            or reference in references
            or type(digest) is not str
            or _DIGEST.fullmatch(digest) is None
        ):
            # A CI result cannot be dressed up as host isolation or a human
            # signature, and mere free text cannot become an evidence ref.
            raise HMLBPreactivationEvidenceError(
                "HML_B_EVIDENCE_PROVENANCE_UNVERIFIABLE",
            )
        references.add(reference)
        if value == "REPROVADO":
            rejected.append(key)
        else:
            claimed.append(key)
        if key == "SEC-01" and origin == "governance_exception_claim":
            exception_claimed = True

    if seen != set(_IDS):
        raise HMLBPreactivationEvidenceError("HML_B_EVIDENCE_MATRIX_INVALID")

    blocks = list(_INVARIANT_BLOCKS)
    blocks.extend(f"HML_B_{key.replace('-', '_')}_PENDING" for key in sorted(pending))
    blocks.extend(f"HML_B_{key.replace('-', '_')}_REJECTED_CLAIM" for key in sorted(rejected))
    if exception_claimed:
        blocks.append("HML_B_SEC01_GOVERNANCE_EXCEPTION_UNVERIFIED")
    if len(claimed) == len(_IDS):
        blocks.append("HML_B_ALL_CLAIMS_SUBMITTED_BUT_NOT_ATTESTED")

    return HMLBPreactivationEvidenceReview(
        status="blocked",
        environment="hml",
        service_id="public-hub",
        architecture="B",
        source=_SOURCE,
        rows_reviewed=10,
        pending_items=tuple(sorted(pending)),
        rejected_items=tuple(sorted(rejected)),
        claimed_complete_items=tuple(sorted(claimed)),
        claimed_governance_exception=exception_claimed,
        blocks=tuple(blocks),
    )

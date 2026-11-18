"""Pilot HML pilot readiness matrix review (source-only, always blocked).

Parses an operator-supplied readiness claim. Never observes the host, never
approves installation and never treats governance risk acceptance as an
independent SEC-01 human review.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.pilot-readiness.v1"
_SOURCE = "operator_supplied_untrusted"
_MAX = 12288
_CATEGORIES = frozenset({
    "implemented_and_proven_in_ci",
    "proven_only_in_disposable_fixtures",
    "requires_real_linux_observation",
    "requires_explicit_authorization",
    "risk_accepted_by_owner",
    "unproven_residual_risk",
})
_REQUIRED_ACCEPTANCES = frozenset({
    "OWNER_GOVERNANCE_DECISIONS",
    "ROOT_DOCKER_PRODUCER_RISK_ACCEPTED",
    "LOCAL_ED25519_SAME_HOST_KEY_RISK_ACCEPTED",
    "EXTERNAL_SIGNER_DEFERRED",
    "ARCHITECTURE_B_FOR_HML_PILOT",
})
_FIELDS = frozenset({
    "schema", "source", "host", "environment", "architecture",
    "matrix", "owner_risk_acceptances", "governance_exception_pending",
    "prepare_eligible_claim", "can_execute_claim",
})
_BLOCKS = (
    "PILOT_READINESS_INDEX_IS_UNTRUSTED",
    "OWNER_RISK_ACCEPTANCE_IS_NOT_INDEPENDENT_SEC01",
    "GOVERNANCE_EXCEPTION_PENDING_IF_INDEPENDENCE_REQUIRED",
    "REAL_HOST_OBSERVATION_NOT_ATTESTED",
    "OPERATIONAL_CHANGE_NOT_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLPilotReadinessError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLPilotReadinessReview:
    status: str = "blocked"
    categories_reviewed: int = 0
    owner_acceptances: tuple[str, ...] = ()
    governance_exception_pending: bool = True
    independent_sec01_attested: bool = False
    host_observation_attested: bool = False
    operational_authorization_granted: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLPilotReadinessError("HML_PILOT_DUPLICATE_FIELD")
        out[key] = value
    return out


def review_untrusted_pilot_readiness(raw: bytes) -> HMLPilotReadinessReview:
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX or b"\x00" in raw:
        raise HMLPilotReadinessError("HML_PILOT_INPUT_INVALID")
    try:
        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique,
        )
    except (ValueError, UnicodeError, TypeError):
        raise HMLPilotReadinessError("HML_PILOT_JSON_INVALID") from None
    if type(document) is not dict or set(document) != _FIELDS:
        raise HMLPilotReadinessError("HML_PILOT_SCHEMA_INVALID")
    if (
        document["schema"] != _SCHEMA
        or document["source"] != _SOURCE
        or document["host"] != "srv-api"
        or document["environment"] != "hml"
        or document["architecture"] != "B"
        or document["prepare_eligible_claim"] is not False
        or document["can_execute_claim"] is not False
        or type(document["governance_exception_pending"]) is not bool
    ):
        raise HMLPilotReadinessError("HML_PILOT_SCOPE_DENIED")
    matrix = document["matrix"]
    acceptances = document["owner_risk_acceptances"]
    if type(matrix) is not dict or set(matrix) != _CATEGORIES:
        raise HMLPilotReadinessError("HML_PILOT_MATRIX_INVALID")
    for key, value in matrix.items():
        if type(value) is not list or not value:
            raise HMLPilotReadinessError("HML_PILOT_MATRIX_INVALID")
        if any(type(item) is not str or not 3 <= len(item) <= 128 for item in value):
            raise HMLPilotReadinessError("HML_PILOT_MATRIX_INVALID")
    if (
        type(acceptances) is not list
        or set(acceptances) != _REQUIRED_ACCEPTANCES
        or any(type(item) is not str for item in acceptances)
    ):
        raise HMLPilotReadinessError("HML_PILOT_ACCEPTANCE_INVALID")
    return HMLPilotReadinessReview(
        categories_reviewed=len(matrix),
        owner_acceptances=tuple(sorted(acceptances)),
        governance_exception_pending=bool(
            document["governance_exception_pending"],
        ),
        # Owner acceptance is recorded, never upgraded to independent SEC-01.
        independent_sec01_attested=False,
    )

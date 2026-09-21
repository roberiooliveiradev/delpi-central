"""Pure Evidence / epistemic invariants (C3-T2 conformance surface)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from app.domain.evidence.model import (
    AuthorityPolicySnapshot,
    EvidenceConflictSet,
    EvidenceItem,
    EvidencePresence,
    EvidenceRef,
    EpistemicClass,
    FactQualificationCriteria,
    FreshnessClass,
    SourceRef,
)

# Stronger → weaker. Derived synthesis inherits the weakest parent strength.
_EPISTEMIC_STRENGTH: dict[EpistemicClass, int] = {
    EpistemicClass.FACT: 60,
    EpistemicClass.CALCULATION: 50,
    EpistemicClass.CONCLUSION: 40,
    EpistemicClass.OBSERVATION: 30,
    EpistemicClass.HYPOTHESIS: 20,
    EpistemicClass.RECOMMENDATION: 10,
}

_SECRET_FIELD_MARKERS = frozenset(
    {
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "password",
        "passwd",
        "api_key",
        "apikey",
        "authorization",
        "client_secret",
        "bearer",
        "private_key",
        "credential",
        "credentials",
    }
)

_COT_FIELD_MARKERS = frozenset(
    {
        "chain_of_thought",
        "cot",
        "private_reasoning",
        "hidden_reasoning",
    }
)


class EvidenceDomainError(ValueError):
    """Domain invariant violation for Evidence / epistemic rules."""


class TypedResultPlaceholder(str, Enum):
    """Marks Prediction/Simulation defaults outside EpistemicClass."""

    PREDICTION = "PREDICTION"
    SIMULATION = "SIMULATION"


def epistemically_weaker(left: EpistemicClass, right: EpistemicClass) -> EpistemicClass:
    if _EPISTEMIC_STRENGTH[left] <= _EPISTEMIC_STRENGTH[right]:
        return left
    return right


def can_qualify_as_fact(criteria: FactQualificationCriteria) -> bool:
    """Epistemic FACT qualification — independent of current-user live AuthZ."""
    if criteria.contains_secret_or_token:
        return False
    return (
        criteria.source_identifiable
        and criteria.source_authoritative_for_proposition
        and criteria.source_contract_validated
        and criteria.freshness_sufficient
        and criteria.explicit_fact_class
        and criteria.limitations_preserved
    )


def create_evidence_item(
    *,
    evidence_id: str,
    epistemic_class: EpistemicClass,
    proposition: str,
    source_ref: SourceRef | None = None,
    freshness: FreshnessClass = FreshnessClass.UNKNOWN,
    limitations: Sequence[str] = (),
    entity_refs: Sequence[Any] = (),
    derived_from: Sequence[EvidenceRef] = (),
    source_lineage: Sequence[SourceRef] = (),
    model_ref: Any = None,
    prediction_ref: Any = None,
    transformation_kind: str | None = None,
    presence: EvidencePresence = EvidencePresence.PRESENT,
    payload: Mapping[str, Any] | None = None,
) -> EvidenceItem:
    """Build a coordinated Evidence item with secret/CoT guards."""
    if payload is not None:
        reject_secret_bearing_payload(payload)
        assert_no_chain_of_thought(payload)

    lineage = tuple(source_lineage)
    if source_ref is not None and source_ref not in lineage:
        lineage = (source_ref, *lineage)

    return EvidenceItem(
        evidence_ref=EvidenceRef(evidence_id=evidence_id),
        epistemic_class=epistemic_class,
        proposition=proposition,
        source_ref=source_ref,
        freshness=freshness,
        limitations=tuple(limitations),
        entity_refs=tuple(entity_refs),
        derived_from=tuple(derived_from),
        source_lineage=lineage,
        model_ref=model_ref,
        prediction_ref=prediction_ref,
        transformation_kind=transformation_kind,
        presence=presence,
    )


def try_automatic_observation_to_fact(item: EvidenceItem) -> EvidenceItem:
    """OBSERVATION must not auto-promote to FACT."""
    if item.epistemic_class is not EpistemicClass.OBSERVATION:
        raise EvidenceDomainError("automatic promotion applies only to OBSERVATION inputs")
    raise EvidenceDomainError("NO automatic OBSERVATION → FACT promotion")


def recommendation_authorizes_act(item: EvidenceItem) -> bool:
    """RECOMMENDATION is never authorization."""
    _ = item
    return False


def evidence_ref_grants_source_permission(_ref: EvidenceRef) -> bool:
    return False


def source_ref_grants_provider_access(_ref: SourceRef) -> bool:
    return False


def missing_means_negative_fact(presence: EvidencePresence) -> bool:
    """missing evidence != false; unknown != guessed negative."""
    _ = presence
    return False


def derive_evidence(
    *,
    evidence_id: str,
    parents: Sequence[EvidenceItem],
    proposition: str,
    transformation_kind: str,
    target_class: EpistemicClass | None = None,
    limitations: Sequence[str] = (),
) -> EvidenceItem:
    if not parents:
        raise EvidenceDomainError("derived Evidence requires parent lineage")

    weakest = parents[0].epistemic_class
    for parent in parents[1:]:
        weakest = epistemically_weaker(weakest, parent.epistemic_class)

    resolved_class = target_class if target_class is not None else weakest
    if _EPISTEMIC_STRENGTH[resolved_class] > _EPISTEMIC_STRENGTH[weakest]:
        raise EvidenceDomainError(
            "derived Evidence cannot strengthen epistemic class beyond weakest parent"
        )

    parent_refs = tuple(parent.evidence_ref for parent in parents)
    lineage: list[SourceRef] = []
    seen: set[str] = set()
    for parent in parents:
        sources = parent.source_lineage or (
            (parent.source_ref,) if parent.source_ref is not None else ()
        )
        for source in sources:
            if source is None:
                continue
            key = f"{source.source_system}:{source.source_id}"
            if key not in seen:
                seen.add(key)
                lineage.append(source)

    merged_limitations = tuple(
        dict.fromkeys([*limitations, *(lim for parent in parents for lim in parent.limitations)])
    )
    return create_evidence_item(
        evidence_id=evidence_id,
        epistemic_class=resolved_class,
        proposition=proposition,
        source_ref=lineage[0] if lineage else None,
        freshness=FreshnessClass.UNKNOWN,
        limitations=merged_limitations,
        derived_from=parent_refs,
        source_lineage=tuple(lineage),
        transformation_kind=transformation_kind,
    )


def build_conflict_set(items: Sequence[EvidenceItem]) -> EvidenceConflictSet:
    if len(items) < 2:
        raise EvidenceDomainError("conflict set requires at least two Evidence items")
    return EvidenceConflictSet(items=tuple(items), reconciled=False)


def rename_provider_preserves_semantics(
    original: SourceRef,
    *,
    renamed_provider_name: str,
) -> SourceRef:
    """Provider/display rename must not alter authority capability semantics."""
    return SourceRef(
        source_id=original.source_id,
        source_system=original.source_system,
        authority_capability=original.authority_capability,
        provider_name=renamed_provider_name,
        revision=original.revision,
        observed_at=original.observed_at,
    )


def reject_secret_bearing_payload(payload: Mapping[str, Any]) -> None:
    """Secrets/tokens cannot become Evidence or model context."""
    for key, value in payload.items():
        key_l = str(key).lower()
        if key_l in _SECRET_FIELD_MARKERS or any(
            marker in key_l for marker in ("token", "secret", "password")
        ):
            raise EvidenceDomainError(
                f"secret/token field '{key}' cannot become Evidence or model context"
            )
        if isinstance(value, Mapping):
            reject_secret_bearing_payload(value)


def assert_no_chain_of_thought(payload: Mapping[str, Any]) -> None:
    """No CoT persistence or CoT exposure on Evidence payloads."""
    for key, value in payload.items():
        key_l = str(key).lower()
        if key_l in _COT_FIELD_MARKERS:
            raise EvidenceDomainError(f"CoT field '{key}' must not be persisted on Evidence")
        if isinstance(value, Mapping):
            assert_no_chain_of_thought(value)


def absorb_external_content_into_authority(
    snapshot: AuthorityPolicySnapshot,
    external_payload: Mapping[str, Any],
) -> AuthorityPolicySnapshot:
    """External/prompt/tool injection content must not alter authority/policy."""
    _ = external_payload  # untrusted; intentionally ignored for authority mutation
    return AuthorityPolicySnapshot(
        policy_ids=snapshot.policy_ids,
        rbac_permission_codes=snapshot.rbac_permission_codes,
    )


def default_class_for_input_kind(
    input_kind: str,
) -> EpistemicClass | TypedResultPlaceholder:
    """Default epistemic treatment table (21 §4B.5) — subset used by conformance."""
    mapping: dict[str, EpistemicClass | TypedResultPlaceholder] = {
        "authoritative_domain_api": EpistemicClass.FACT,
        "external_webpage": EpistemicClass.OBSERVATION,
        "ocr_vlm_extraction": EpistemicClass.OBSERVATION,
        "model_inference": EpistemicClass.HYPOTHESIS,
        "recommendation": EpistemicClass.RECOMMENDATION,
        "user_statement": EpistemicClass.OBSERVATION,
        "prediction": TypedResultPlaceholder.PREDICTION,
        "simulation": TypedResultPlaceholder.SIMULATION,
    }
    try:
        return mapping[input_kind]
    except KeyError as exc:
        raise EvidenceDomainError(f"unknown input kind: {input_kind}") from exc

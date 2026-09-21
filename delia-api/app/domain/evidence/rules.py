"""Pure Evidence / epistemic invariants (C3-T2R1 conformance surface).

C3-T2R1 removes unauthorized total epistemic ordering, duplicate typed-result
discriminators, and SourceRef authority fields. Derivation uses explicit semantic kinds only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
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
    TypedResultKind,
)

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

_CALCULATION_TRANSFORMS = frozenset(
    {
        "calculation",
        "arithmetic",
        "identifiable_calculation",
    }
)

_CALCULATION_PARENT_CLASSES = frozenset(
    {
        EpistemicClass.OBSERVATION,
        EpistemicClass.FACT,
        EpistemicClass.CALCULATION,
    }
)


class EvidenceDomainError(ValueError):
    """Domain invariant violation for Evidence / epistemic rules."""


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
    target_class: EpistemicClass,
    limitations: Sequence[str] = (),
) -> EvidenceItem:
    """Derive Evidence by explicit semantic kind — no numeric epistemic ranking.

    Epistemic classes are kinds, not a global ordinal strength scale.
    Derived outputs preserve parent EvidenceRef[] / SourceRef lineage and limitations.
    FACT is never produced by this helper; use FactQualificationCriteria.
    """
    if not parents:
        raise EvidenceDomainError("derived Evidence requires parent lineage")
    if not transformation_kind.strip():
        raise EvidenceDomainError("transformation_kind is required")

    if target_class is EpistemicClass.FACT:
        raise EvidenceDomainError(
            "derive_evidence cannot produce FACT; use FactQualificationCriteria"
        )

    if target_class is EpistemicClass.CALCULATION:
        if transformation_kind not in _CALCULATION_TRANSFORMS:
            raise EvidenceDomainError(
                "CALCULATION requires an identifiable calculation transformation_kind"
            )
        for parent in parents:
            if parent.epistemic_class not in _CALCULATION_PARENT_CLASSES:
                raise EvidenceDomainError(
                    "CALCULATION parents must be OBSERVATION, FACT, or CALCULATION"
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
        epistemic_class=target_class,
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


def rename_provider_preserves_identity(
    original: SourceRef,
    *,
    renamed_provider_name: str,
) -> SourceRef:
    """Provider/display rename must not alter SourceRef identity fields."""
    return SourceRef(
        source_id=original.source_id,
        source_system=original.source_system,
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
) -> EpistemicClass | TypedResultKind:
    """Default epistemic treatment table (21 §4B.5) — subset used by conformance."""
    mapping: dict[str, EpistemicClass | TypedResultKind] = {
        "authoritative_domain_api": EpistemicClass.FACT,
        "external_webpage": EpistemicClass.OBSERVATION,
        "ocr_vlm_extraction": EpistemicClass.OBSERVATION,
        "model_inference": EpistemicClass.HYPOTHESIS,
        "recommendation": EpistemicClass.RECOMMENDATION,
        "user_statement": EpistemicClass.OBSERVATION,
        "prediction": TypedResultKind.PREDICTION,
        "simulation": TypedResultKind.SIMULATION,
    }
    try:
        return mapping[input_kind]
    except KeyError as exc:
        raise EvidenceDomainError(f"unknown input kind: {input_kind}") from exc

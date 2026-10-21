"""Deterministic supplier snapshot comparison engine (S1).

Rules:
- compare only mapped fields; unmapped canonical/external keys are ignored;
- CNPJ identity must match before any field is compared (fail-closed);
- CPF / non-``J`` entities are outside the CNPJ enrichment flow;
- a missing external value never proposes clearing the canonical value;
- ``DIFFERENT`` never implies ``ELIGIBLE_TO_APPLY``;
- municipality fields (state/city/city_code) are an indivisible group and are
  only eligible after canonical CC2 conciliation;
- no network, no clock, no randomness — same input yields same output.
"""

from __future__ import annotations

import unicodedata
from typing import Mapping

from app.domain.exceptions import (
    EnrichmentIdentityMismatchError,
    EnrichmentUnsupportedDocumentError,
)
from app.domain.supplier_enrichment.field_mapping import (
    CNPJ_SA2_MAPPING_V1,
    MUNICIPALITY_GROUP,
    NORMALIZATION_VERSION_V1,
    FieldClass,
    FieldMappingPolicy,
    FieldSpec,
    Normalizer,
)
from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    ComparisonState,
    EligibilityState,
    ExternalRegistrySnapshot,
    SupplierEnrichmentComparison,
    SupplierEnrichmentReview,
    SupplierFieldProposal,
    digits_only,
)

# (uf, normalized city name) -> canonical Protheus city code (CC2).
MunicipalityIndex = Mapping[tuple[str, str], str]


def _collapse_spaces(value: str) -> str:
    return " ".join(value.split())


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _normalize(value: str | None, normalizer: Normalizer) -> str | None:
    if value is None:
        return None
    text = str(value)
    if normalizer is Normalizer.DIGITS:
        normalized = digits_only(text)
        return normalized if normalized else None
    if normalizer is Normalizer.UF:
        normalized = _collapse_spaces(text).upper()
        return normalized if normalized else None
    if normalizer is Normalizer.EMAIL:
        normalized = text.strip().casefold()
        return normalized if normalized else None
    normalized = _strip_accents(_collapse_spaces(text)).casefold()
    return normalized if normalized else None


def _is_present(value: str | None) -> bool:
    return value is not None and str(value).strip() != ""


def compare_supplier_snapshots(
    canonical: CanonicalSupplierSnapshot,
    external: ExternalRegistrySnapshot,
    *,
    policy: FieldMappingPolicy = CNPJ_SA2_MAPPING_V1,
    municipality_index: MunicipalityIndex | None = None,
) -> SupplierEnrichmentReview:
    """Compare canonical SA2 vs external registry snapshots, per field.

    ``municipality_index`` is the application-provided canonical CC2
    conciliation ``{(uf, normalized_city_name): city_code}``; without it,
    municipality differences stay ``PENDING_VALIDATION``.
    """
    canonical_tax = digits_only(canonical.tax_id)
    external_tax = digits_only(external.tax_id)

    person_type = (canonical.person_type or "").strip().upper()
    if person_type != "J" or len(canonical_tax) == 11:
        raise EnrichmentUnsupportedDocumentError()
    if len(external_tax) != 14 or external_tax != canonical_tax:
        raise EnrichmentIdentityMismatchError()

    municipality_resolution = _resolve_municipality(external, municipality_index)

    proposals = tuple(
        _compare_spec(spec, canonical, external, municipality_resolution)
        for spec in policy.specs
    )
    summary = _summarize(proposals)
    comparison = SupplierEnrichmentComparison(
        supplier=canonical.supplier,
        source_id=external.source_id,
        retrieved_at=external.retrieved_at,
        mapping_version=policy.version,
        baseline_reference=canonical.baseline_reference,
        proposals=proposals,
        summary=summary,
    )
    return SupplierEnrichmentReview(comparison=comparison)


def _compare_spec(
    spec: FieldSpec,
    canonical: CanonicalSupplierSnapshot,
    external: ExternalRegistrySnapshot,
    municipality_resolution: dict,
) -> SupplierFieldProposal:
    current = canonical.fields.get(spec.field_key)
    source_field = spec.source_field
    has_external = source_field is not None and source_field in external.fields
    raw_external = external.fields.get(source_field) if source_field else None

    base = dict(
        field_key=spec.field_key,
        section_key=spec.section_key,
        source_field=source_field,
        source_reference=external.source_reference,
        normalization_version=NORMALIZATION_VERSION_V1,
    )

    if spec.field_class is FieldClass.PROTECTED:
        return SupplierFieldProposal(
            current_value=current,
            suggested_value=None,
            comparison=ComparisonState.PROTECTED,
            eligibility=EligibilityState.PROTECTED,
            eligibility_reason="protected_identity_field",
            **base,
        )

    if not has_external:
        comparison_state = ComparisonState.SOURCE_MISSING
        reason = "source_field_absent"
    elif not _is_present(raw_external):
        comparison_state = ComparisonState.SOURCE_MISSING
        reason = "source_field_empty"
    elif not _is_present(current):
        comparison_state = ComparisonState.CURRENT_MISSING
        reason = None
    else:
        normalized_current = _normalize(current, spec.normalizer)
        normalized_external = _normalize(raw_external, spec.normalizer)
        if normalized_external is None:
            comparison_state = ComparisonState.SOURCE_MISSING
            reason = "source_field_empty"
        elif normalized_current == normalized_external:
            comparison_state = ComparisonState.MATCH
            reason = None
        else:
            comparison_state = ComparisonState.DIFFERENT
            reason = None

    suggested = _suggested_value(spec, raw_external, municipality_resolution)

    if spec.field_class is FieldClass.INFORMATION_ONLY:
        eligibility, reason = (
            EligibilityState.NOT_APPLICABLE,
            reason or "informational_only",
        )
    elif comparison_state is ComparisonState.MATCH:
        eligibility, reason = EligibilityState.NOT_APPLICABLE, "values_equal"
    elif comparison_state is ComparisonState.SOURCE_MISSING:
        eligibility = EligibilityState.NOT_APPLICABLE
    elif comparison_state in (
        ComparisonState.CURRENT_MISSING,
        ComparisonState.DIFFERENT,
    ):
        eligibility, reason = _apply_eligibility(
            spec, raw_external, municipality_resolution
        )
    else:
        eligibility, reason = EligibilityState.NOT_APPLICABLE, reason

    return SupplierFieldProposal(
        current_value=current,
        suggested_value=suggested,
        comparison=comparison_state,
        eligibility=eligibility,
        eligibility_reason=reason,
        **base,
    )


def _suggested_value(
    spec: FieldSpec,
    raw_external: str | None,
    municipality_resolution: dict,
) -> str | None:
    if spec.field_class is not FieldClass.COMPARABLE or not _is_present(raw_external):
        return None
    if spec.field_key == "city_code":
        resolved = municipality_resolution.get("city_code")
        return resolved if resolved is not None else None
    return str(raw_external).strip()


def _apply_eligibility(
    spec: FieldSpec,
    raw_external: str | None,
    municipality_resolution: dict,
) -> tuple[EligibilityState, str | None]:
    normalized = _normalize(raw_external, spec.normalizer)
    if normalized is None:
        return EligibilityState.NOT_APPLICABLE, "source_field_empty"
    if spec.dependency_group == MUNICIPALITY_GROUP:
        group_eligibility = municipality_resolution["eligibility"]
        if group_eligibility is not EligibilityState.ELIGIBLE_TO_APPLY:
            return group_eligibility, municipality_resolution["reason"]
        if spec.field_key == "city_code":
            # Suggested value is the resolved canonical CC2 code, not the
            # external IBGE code — its own limit does not apply.
            return EligibilityState.ELIGIBLE_TO_APPLY, None
        if spec.max_length is not None and len(normalized) > spec.max_length:
            return EligibilityState.PENDING_VALIDATION, "exceeds_sa2_limit"
        return EligibilityState.ELIGIBLE_TO_APPLY, None
    if spec.max_length is not None and len(normalized) > spec.max_length:
        return EligibilityState.PENDING_VALIDATION, "exceeds_sa2_limit"
    if spec.normalizer is Normalizer.EMAIL and "@" not in normalized:
        return EligibilityState.PENDING_VALIDATION, "invalid_suggested_value"
    if spec.field_key == "postal_code" and len(normalized) != 8:
        return EligibilityState.PENDING_VALIDATION, "invalid_suggested_value"
    if spec.requires_equivalence_rule:
        return EligibilityState.PENDING_VALIDATION, "equivalence_rule_pending"
    if spec.requires_trusted_source_policy:
        return EligibilityState.PENDING_VALIDATION, "trusted_source_policy_pending"
    return EligibilityState.ELIGIBLE_TO_APPLY, None


def _resolve_municipality(
    external: ExternalRegistrySnapshot,
    municipality_index: MunicipalityIndex | None,
) -> dict:
    """Resolve the indivisible state/city/city_code group via CC2 index.

    The external IBGE code is never copied to A2_COD_MUN; the suggested
    city_code is the canonical code returned by the conciliation index.
    """
    if municipality_index is None:
        return {
            "eligibility": EligibilityState.PENDING_VALIDATION,
            "reason": "municipality_reconciliation_unavailable",
            "city_code": None,
        }
    uf = _normalize(external.fields.get("address.state"), Normalizer.UF)
    city = _normalize(external.fields.get("address.city"), Normalizer.TEXT)
    ibge = digits_only(external.fields.get("address.ibge_city_code"))
    if not uf or not city or not ibge:
        return {
            "eligibility": EligibilityState.PENDING_VALIDATION,
            "reason": "municipality_source_incomplete",
            "city_code": None,
        }
    resolved = municipality_index.get((uf, city))
    if resolved is None:
        return {
            "eligibility": EligibilityState.PENDING_VALIDATION,
            "reason": "municipality_not_conciliated",
            "city_code": None,
        }
    return {
        "eligibility": EligibilityState.ELIGIBLE_TO_APPLY,
        "reason": None,
        "city_code": digits_only(resolved) or None,
    }


def _summarize(proposals: tuple[SupplierFieldProposal, ...]) -> dict[str, int]:
    summary: dict[str, int] = {
        "total_fields": len(proposals),
        "compared_fields": 0,
        "different": 0,
        "match": 0,
        "source_missing": 0,
        "current_missing": 0,
        "protected": 0,
        "informational": 0,
        "eligible_to_apply": 0,
        "pending_validation": 0,
        "not_applicable": 0,
    }
    for proposal in proposals:
        state = proposal.comparison
        if state is ComparisonState.MATCH:
            summary["match"] += 1
            summary["compared_fields"] += 1
        elif state is ComparisonState.DIFFERENT:
            summary["different"] += 1
            summary["compared_fields"] += 1
        elif state is ComparisonState.SOURCE_MISSING:
            summary["source_missing"] += 1
        elif state is ComparisonState.CURRENT_MISSING:
            summary["current_missing"] += 1
            summary["compared_fields"] += 1
        elif state is ComparisonState.PROTECTED:
            summary["protected"] += 1
        if proposal.eligibility is EligibilityState.ELIGIBLE_TO_APPLY:
            summary["eligible_to_apply"] += 1
        elif proposal.eligibility is EligibilityState.PENDING_VALIDATION:
            summary["pending_validation"] += 1
        elif proposal.eligibility is EligibilityState.NOT_APPLICABLE:
            summary["not_applicable"] += 1
    summary["informational"] = (
        summary["total_fields"]
        - summary["compared_fields"]
        - summary["source_missing"]
        - summary["protected"]
    )
    return summary

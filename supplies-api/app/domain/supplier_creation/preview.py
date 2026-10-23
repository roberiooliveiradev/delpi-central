"""Supplier creation preview — pure domain rules (X4.UX-R1.S1).

Turns an ``ExternalRegistrySnapshot`` into prefill suggestions for the
supplier creation draft. No I/O, no framework: the application service
orchestrates provider + duplicate check; this module decides *what may be
suggested* and *how the duplicate check is classified*.

Policy (frozen in X4.UX-R1.P0):

- only ``FieldClass.COMPARABLE`` specs from ``CNPJ_SA2_MAPPING_V1`` whose
  source value is present may produce a suggestion;
- ``requires_trusted_source_policy`` fields (contact.*) are never surfaced —
  the LGPD minimization contract withholds them upstream anyway;
- ``requires_equivalence_rule`` fields (trade name → A2_NREDUZ) are returned
  with ``applicable=False`` — visible for review, never auto-applied;
- values are normalized for *display* (no case-folding) and truncated to the
  SA2 ``max_length`` — the same ceiling Protheus would apply;
- internal purchasing/financial fields are never suggested: they have no
  source mapping at all, so they simply never appear here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from app.domain.supplier_enrichment.field_mapping import (
    CNPJ_SA2_MAPPING_V1,
    FieldClass,
    Normalizer,
)
from app.domain.supplier_enrichment.models import digits_only


class DuplicateStatus(str, Enum):
    """Honest duplicate-check outcome.

    ``CLEAR`` is only emitted after a *successful exact-match* canonical
    search returning zero rows — never from a textual ``LIKE`` search or a
    failed integration.
    """

    CLEAR = "CLEAR"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class CreationSuggestion:
    field_key: str
    suggested_value: str
    applicable: bool


def is_valid_cnpj(digits: str) -> bool:
    """Validate a 14-digit CNPJ including both check digits."""

    if len(digits) != 14 or not digits.isdigit():
        return False
    if digits == digits[0] * 14:
        return False

    def _digit(base: str, weights: tuple[int, ...]) -> int:
        total = sum(int(d) * w for d, w in zip(base, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    first = _digit(digits[:12], (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    second = _digit(digits[:13], (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    return int(digits[12]) == first and int(digits[13]) == second


def mask_tax_id(digits: str) -> str:
    """Mask a CNPJ for display — root/branch visible, check digits hidden."""

    if len(digits) != 14:
        return "***"
    return f"{digits[:2]}.***.***/{digits[8:12]}-**"


def classify_duplicate(total: int | None) -> DuplicateStatus:
    """Classify a completed canonical search; ``None`` means it never ran."""

    if total is None:
        return DuplicateStatus.INCONCLUSIVE
    if total > 0:
        return DuplicateStatus.POSSIBLE_MATCH
    return DuplicateStatus.CLEAR


def _collapse_spaces(value: str) -> str:
    return " ".join(str(value).split())


def _display_value(raw: object, normalizer: Normalizer) -> str | None:
    if raw is None:
        return None
    text = str(raw)
    if normalizer is Normalizer.DIGITS:
        digits = digits_only(text)
        return digits or None
    if normalizer is Normalizer.UF:
        normalized = _collapse_spaces(text).upper()
        return normalized or None
    if normalizer is Normalizer.EMAIL:
        normalized = text.strip().casefold()
        return normalized or None
    normalized = _collapse_spaces(text)
    return normalized or None


def build_creation_suggestions(
    fields: Mapping[str, str | None],
) -> tuple[CreationSuggestion, ...]:
    """Map an external snapshot onto suggestible draft fields.

    ``fields`` is the snapshot's source_field-keyed map (dotted keys such as
    ``"company.legal_name"``). Fields without a usable external value simply
    do not appear — the caller turns them into ``unavailable_fields``.
    """

    suggestions: list[CreationSuggestion] = []
    for spec in CNPJ_SA2_MAPPING_V1.specs:
        if spec.field_class is not FieldClass.COMPARABLE:
            continue
        if spec.requires_trusted_source_policy:
            # Contact data stays withheld (X1/X2 minimization contract).
            continue
        if spec.source_field is None:
            continue
        value = _display_value(fields.get(spec.source_field), spec.normalizer)
        if value is None:
            continue
        if spec.max_length:
            value = value[: spec.max_length]
        suggestions.append(
            CreationSuggestion(
                field_key=spec.field_key,
                suggested_value=value,
                applicable=not spec.requires_equivalence_rule,
            )
        )
    return tuple(suggestions)

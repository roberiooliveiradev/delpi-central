"""Enrichment domain models — typed snapshots, proposals and review.

No persistence: S1 models are immutable in-memory values. A repository port
will only be materialized when a use case requires it (S2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class ComparisonState(str, Enum):
    """Per-field outcome of comparing canonical vs external values."""

    MATCH = "MATCH"
    DIFFERENT = "DIFFERENT"
    SOURCE_MISSING = "SOURCE_MISSING"
    CURRENT_MISSING = "CURRENT_MISSING"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    PROTECTED = "PROTECTED"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


class EligibilityState(str, Enum):
    """Whether a field suggestion may ever reach the draft/PUT stage.

    ``DIFFERENT`` never implies ``ELIGIBLE_TO_APPLY`` — eligibility requires
    a proven canonical rule (limits, equivalence, conciliation, source trust).
    """

    ELIGIBLE_TO_APPLY = "ELIGIBLE_TO_APPLY"
    PROTECTED = "PROTECTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING_VALIDATION = "PENDING_VALIDATION"


class FieldDecisionState(str, Enum):
    """Decision lifecycle of a proposal. Modelled only — no decision API in S1."""

    PENDING = "PENDING"
    ACCEPTED_FOR_DRAFT = "ACCEPTED_FOR_DRAFT"
    REJECTED_SUGGESTION = "REJECTED_SUGGESTION"


_DIGITS = re.compile(r"\D")


def digits_only(value: object) -> str:
    return _DIGITS.sub("", str(value or ""))


@dataclass(frozen=True)
class SupplierRef:
    """SA2 identity: 6-digit code + 2-digit store."""

    code: str
    store: str

    def __post_init__(self) -> None:
        code = digits_only(self.code)
        store = digits_only(self.store)
        if not code or len(code) > 6:
            raise ValueError("supplier code must be 1-6 digits")
        if not store or len(store) > 2:
            raise ValueError("supplier store must be 1-2 digits")
        object.__setattr__(self, "code", code.zfill(6))
        object.__setattr__(self, "store", store.zfill(2))


@dataclass(frozen=True)
class CanonicalSupplierSnapshot:
    """Current supplier state as read from the canonical source (api-delpi).

    ``fields`` maps canonical SA2 contract field_keys to raw current values;
    absent key or ``None`` means the canonical projection has no value —
    never treated as "must be cleared".
    """

    supplier: SupplierRef
    tax_id: str
    person_type: str
    fields: Mapping[str, str | None] = field(default_factory=dict)
    baseline_reference: str | None = None


@dataclass(frozen=True)
class ExternalRegistrySnapshot:
    """Company-registry (CNPJ) data from an authorized provider.

    ``fields`` maps external source_field keys (dotted, e.g.
    ``"address.district"``) to raw values exactly as returned.
    """

    tax_id: str
    source_id: str
    retrieved_at: str
    fields: Mapping[str, str | None] = field(default_factory=dict)
    source_reference: str | None = None


@dataclass(frozen=True)
class SupplierFieldProposal:
    """One mapped field of a comparison. Raw values preserved for display."""

    field_key: str
    section_key: str
    current_value: str | None
    suggested_value: str | None
    comparison: ComparisonState
    eligibility: EligibilityState
    eligibility_reason: str | None
    source_field: str | None
    source_reference: str | None
    normalization_version: str
    decision: FieldDecisionState = FieldDecisionState.PENDING


@dataclass(frozen=True)
class SupplierEnrichmentComparison:
    """Deterministic result of comparing two snapshots field by field."""

    supplier: SupplierRef
    source_id: str
    retrieved_at: str
    mapping_version: str
    baseline_reference: str | None
    proposals: tuple[SupplierFieldProposal, ...]
    summary: Mapping[str, int]


@dataclass(frozen=True)
class SupplierEnrichmentReview:
    """A comparison review between canonical and external snapshots.

    ``review_id`` and ``unit_context`` are assigned by the application layer
    (persistence/authorization), never by the domain engine.
    """

    comparison: SupplierEnrichmentComparison
    review_id: str | None = None
    unit_context: str | None = None

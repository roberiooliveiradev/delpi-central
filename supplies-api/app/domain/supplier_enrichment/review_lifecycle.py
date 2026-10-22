"""Enrichment review lifecycle — statuses, decision rules and draft assembly.

Domain-pure module: no Flask, no persistence, no I/O. The application layer
owns actors, clocks and storage; the domain owns which transitions and
decisions are valid and which proposals may reach an update draft.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from app.domain.exceptions import EnrichmentError
from app.domain.supplier_enrichment.field_mapping import (
    CNPJ_SA2_MAPPING_V1,
    FieldClass,
)
from app.domain.supplier_enrichment.models import (
    EligibilityState,
    FieldDecisionState,
    SupplierFieldProposal,
)


class ReviewStatus(str, Enum):
    """Explicit review state machine owned by use cases.

    ``IN_REVIEW``   — review is open for decisions.
    ``DECIDED``     — every proposal has a terminal decision.
    ``EXPIRED``     — ``expires_at`` elapsed (lazy transition on access).
    ``CANCELLED``   — reserved; no transition implemented in S2.
    ``STALE``       — canonical baseline changed since comparison.
    """

    IN_REVIEW = "IN_REVIEW"
    DECIDED = "DECIDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    STALE = "STALE"


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


DECISION_OUTCOME = {
    Decision.ACCEPT: FieldDecisionState.ACCEPTED_FOR_DRAFT,
    Decision.REJECT: FieldDecisionState.REJECTED_SUGGESTION,
}

# Statuses that still allow decisions.
_ACTIONABLE = frozenset({ReviewStatus.IN_REVIEW, ReviewStatus.DECIDED})


class EnrichmentReviewNotActionableError(EnrichmentError):
    """Review is expired, cancelled or stale — no decisions allowed."""

    def __init__(self, status: ReviewStatus):
        self.status = status
        super().__init__(f"review is {status.value}")


class EnrichmentProposalNotPendingError(EnrichmentError):
    """Proposal already has a terminal decision."""

    def __init__(self, field_key: str):
        self.field_key = field_key
        super().__init__(f"proposal already decided: {field_key}")


class EnrichmentProposalNotEligibleError(EnrichmentError):
    """ACCEPT attempted on a proposal that is not eligible to apply."""

    def __init__(self, field_key: str, eligibility: EligibilityState):
        self.field_key = field_key
        self.eligibility = eligibility
        super().__init__(f"proposal not eligible for acceptance: {field_key}")


class EnrichmentStaleBaselineError(EnrichmentError):
    """Canonical baseline changed since the review was created."""


def assert_decidable(status: ReviewStatus) -> None:
    if status not in _ACTIONABLE:
        raise EnrichmentReviewNotActionableError(status)


def assert_valid_decision(
    proposal: SupplierFieldProposal,
    decision: Decision,
) -> None:
    """Validate one decision against a single proposal (domain rules only)."""
    if proposal.decision is not FieldDecisionState.PENDING:
        raise EnrichmentProposalNotPendingError(proposal.field_key)
    if decision is Decision.ACCEPT:
        if proposal.eligibility is not EligibilityState.ELIGIBLE_TO_APPLY:
            raise EnrichmentProposalNotEligibleError(
                proposal.field_key, proposal.eligibility
            )
        spec = CNPJ_SA2_MAPPING_V1.spec_for(proposal.field_key)
        if spec is None or spec.field_class is not FieldClass.COMPARABLE:
            raise EnrichmentProposalNotEligibleError(
                proposal.field_key, EligibilityState.PROTECTED
            )


def next_review_status(
    status: ReviewStatus,
    proposals: Sequence[SupplierFieldProposal],
) -> ReviewStatus:
    """Derive the status after a decision batch.

    Only ``IN_REVIEW``/``DECIDED`` reviews reach this point; terminal states
    are preserved and never reopened by a decision.
    """
    if status not in _ACTIONABLE:
        return status
    pending = any(
        p.decision is FieldDecisionState.PENDING for p in proposals
    )
    return ReviewStatus.IN_REVIEW if pending else ReviewStatus.DECIDED


@dataclass(frozen=True)
class DraftField:
    """One accepted change selected for a future governed update."""

    field_key: str
    current_value: str | None
    proposed_value: str | None
    proposal_id: str | None = None
    decision_id: str | None = None


def assemble_update_draft(
    proposals: Sequence[SupplierFieldProposal],
) -> tuple[DraftField, ...]:
    """Build the update draft from proposals — draft only, never a write.

    Fail-closed double check: a field reaches the draft only when it is
    ``ACCEPTED_FOR_DRAFT`` *and* ``ELIGIBLE_TO_APPLY`` *and* classified
    ``COMPARABLE`` in the mapping — ``tax_id``, identity keys, informational
    fields and pending-validation fields can never leak into a draft even if
    a decision record were corrupted.
    """
    draft: list[DraftField] = []
    for proposal in proposals:
        if proposal.decision is not FieldDecisionState.ACCEPTED_FOR_DRAFT:
            continue
        spec = CNPJ_SA2_MAPPING_V1.spec_for(proposal.field_key)
        if spec is None or spec.field_class is not FieldClass.COMPARABLE:
            continue
        if proposal.eligibility is not EligibilityState.ELIGIBLE_TO_APPLY:
            continue
        draft.append(
            DraftField(
                field_key=proposal.field_key,
                current_value=proposal.current_value,
                proposed_value=proposal.suggested_value,
            )
        )
    return tuple(draft)


def baseline_fingerprint(
    *,
    supplier_code: str,
    supplier_store: str,
    tax_id: str,
    fields: Mapping[str, str | None],
) -> str:
    """Deterministic fingerprint of the canonical baseline used for
    stale-baseline detection. Pure function — same input, same hash."""
    payload = {
        "supplier_code": supplier_code,
        "supplier_store": supplier_store,
        "tax_id": tax_id,
        "fields": {k: fields.get(k) for k in sorted(fields)},
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def assert_baseline_current(
    stored_reference: str,
    current_reference: str,
) -> None:
    if stored_reference != current_reference:
        raise EnrichmentStaleBaselineError("canonical baseline changed")

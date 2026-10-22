"""Application contracts for the supplier enrichment review flow (S2).

Protocols are consumed by the review service and materialized by adapters:
a Postgres repository, the existing api-delpi canonical reader and an
external registry provider port (unavailable in production in S2 —
fixtures/test adapters only).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, Sequence

from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    ExternalRegistrySnapshot,
)
from app.domain.supplier_enrichment.review_lifecycle import Decision


# --- persisted records ----------------------------------------------------


@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    supplier_code: str
    supplier_store: str
    unit_context: str | None
    actor_subject: str
    source_id: str | None
    source_reference: str | None
    source_retrieved_at: datetime | None
    mapping_version: str
    normalization_version: str
    baseline_reference: str
    status: str
    revision: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class ProposalRecord:
    proposal_id: str
    review_id: str
    field_key: str
    section_key: str
    comparison_state: str
    eligibility_state: str
    eligibility_reason: str | None
    source_field: str | None
    source_reference: str | None
    current_value: str | None
    suggested_value: str | None
    decision_state: str


@dataclass(frozen=True)
class OperationRecord:
    """One idempotent decision *request* — single or bulk."""

    operation_id: str
    review_id: str
    actor_subject: str
    decision: str
    reason_code: str | None
    idempotency_key: str
    request_hash: str
    review_revision: int
    decided_at: datetime


@dataclass(frozen=True)
class DecisionRecord:
    """One per-field decision, linked to its request operation."""

    decision_id: str
    review_id: str
    proposal_id: str
    operation_id: str
    field_key: str
    actor_subject: str
    decision: str
    reason_code: str | None
    decided_at: datetime
    review_revision: int


@dataclass(frozen=True)
class DecisionItem:
    """One decision validated by the application layer."""

    proposal_id: str
    decision: Decision
    reason_code: str | None


# --- application errors ---------------------------------------------------


class ReviewNotFoundError(Exception):
    pass


class ReviewAccessDeniedError(Exception):
    pass


class SupplierNotFoundError(Exception):
    pass


class EnrichmentSourceUnavailableError(Exception):
    """No trusted external registry source is configured."""


class RegistryTaxIdNotFoundError(Exception):
    """Provider returned 404 — CNPJ not present in its data source."""


class RegistryTaxIdInvalidError(Exception):
    """Provider rejected the queried identifier as invalid (upstream 400)."""


class RegistryRateLimitedError(Exception):
    """Local query cap or provider throttling (429) was hit."""

    def __init__(self, message: str, *, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class RegistryLimiterUnavailableError(Exception):
    """The configured rate-limit backend is unavailable — fail closed, no
    external query may be issued."""


class RegistryAccessDeniedError(Exception):
    """Provider denied access (403 / anti-bot block)."""


class RegistryResponseInvalidError(Exception):
    """Provider response cannot be trusted: bad JSON, schema mismatch or
    divergent CNPJ identity."""


class ReviewRevisionConflictError(Exception):
    """expected_revision does not match the persisted revision."""


class IdempotencyConflictError(Exception):
    """Idempotency key reused with a different payload."""


class DuplicateKeyIdempotencyReplay(Exception):
    """Internal signal: idempotent replay of an already applied batch."""

    def __init__(self, record: DecisionRecord):
        self.record = record


# --- ports ----------------------------------------------------------------


class SupplierEnrichmentReviewRepository(Protocol):
    """Port for review persistence. Implementations own transactions."""

    def create_review(
        self,
        *,
        review: ReviewRecord,
        proposals: Sequence[ProposalRecord],
    ) -> ReviewRecord: ...

    def get_review(self, review_id: str) -> ReviewRecord | None: ...

    def list_reviews(
        self,
        *,
        supplier_code: str,
        supplier_store: str,
        actor_subject: str,
        limit: int,
        offset: int,
    ) -> tuple[list[ReviewRecord], int]: ...

    def get_proposals(self, review_id: str) -> list[ProposalRecord]: ...

    def get_decisions(self, review_id: str) -> list[DecisionRecord]: ...

    def find_operation_by_idempotency_key(
        self, *, review_id: str, idempotency_key: str
    ) -> OperationRecord | None: ...

    def apply_decisions(
        self,
        *,
        review_id: str,
        actor_subject: str,
        decision: Decision,
        reason_code: str | None,
        decisions: Sequence[DecisionItem],
        expected_revision: int,
        idempotency_key: str,
        request_hash: str,
        new_status: str,
        event_type: str,
        decided_at: datetime,
    ) -> tuple[ReviewRecord, list[ProposalRecord]]: ...

    def mark_status(
        self,
        *,
        review_id: str,
        status: str,
        expected_revision: int,
    ) -> None: ...

    def append_event(
        self,
        *,
        review_id: str,
        actor_subject: str | None,
        event_type: str,
        metadata: dict[str, Any] | None,
    ) -> None: ...


class CanonicalSupplierReader(Protocol):
    """Port for the canonical supplier read (api-delpi SA2 projection)."""

    def read(
        self, supplier_code: str, supplier_store: str, *, access_token: str
    ) -> CanonicalSupplierSnapshot | None: ...


class CompanyRegistryProvider(Protocol):
    """Port for external company-registry snapshots.

    S2 ships no real provider: the production adapter is fail-closed and
    raises ``EnrichmentSourceUnavailableError``. Test fixtures implement
    this port with synthetic data only.
    """

    def fetch(self, tax_id: str) -> ExternalRegistrySnapshot: ...

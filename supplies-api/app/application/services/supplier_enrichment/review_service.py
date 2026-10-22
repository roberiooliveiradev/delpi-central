"""Supplier enrichment review service — S2 use cases.

Orchestrates review creation (canonical read + external snapshot +
S1 comparison engine), per-field and bulk decisions, history and the
prepare-update draft. All authorization beyond capability is
actor-ownership bound (resource scope contract); no ERP write exists
anywhere in this service.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence

from app.domain.entities import EffectiveUser
from app.domain.exceptions import EnrichmentUnsupportedDocumentError
from app.domain.supplier_enrichment.comparison import compare_supplier_snapshots
from app.domain.supplier_enrichment.field_mapping import (
    CNPJ_SA2_MAPPING_V1,
    NORMALIZATION_VERSION_V1,
)
from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    FieldDecisionState,
    SupplierFieldProposal,
)
from app.domain.supplier_enrichment.review_lifecycle import (
    DECISION_OUTCOME,
    Decision,
    EnrichmentStaleBaselineError,
    ReviewStatus,
    assert_baseline_current,
    assert_decidable,
    assert_valid_decision,
    assemble_update_draft,
    baseline_fingerprint,
    next_review_status,
)

from app.application.services.supplier_enrichment.contracts import (
    CanonicalSupplierReader,
    CompanyRegistryProvider,
    DecisionItem,
    DecisionRecord,
    IdempotencyConflictError,
    ProposalRecord,
    ReviewAccessDeniedError,
    ReviewNotFoundError,
    ReviewRecord,
    ReviewRevisionConflictError,
    SupplierEnrichmentReviewRepository,
    SupplierNotFoundError,
)


class ProposalNotFoundError(Exception):
    """field_key not present among the review proposals."""


class InvalidDecisionRequestError(Exception):
    """Malformed or inconsistent decision request (validation, 422)."""


EVENT_REVIEW_CREATED = "REVIEW_CREATED"
EVENT_FIELD_DECISION = "FIELD_DECISION"
EVENT_BULK_DECISION = "BULK_DECISION"
EVENT_REVIEW_EXPIRED = "REVIEW_EXPIRED"
EVENT_DRAFT_PREPARED = "DRAFT_PREPARED"


@dataclass
class _DecisionContext:
    review: ReviewRecord
    proposals: list[ProposalRecord]
    replayed: bool = False


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _request_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _canonical_fingerprint(canonical: CanonicalSupplierSnapshot) -> str:
    return baseline_fingerprint(
        supplier_code=canonical.supplier.code,
        supplier_store=canonical.supplier.store,
        tax_id=canonical.tax_id,
        fields=canonical.fields,
    )


class SupplierEnrichmentReviewService:
    """Review lifecycle use cases — server-side, actor-scoped."""

    def __init__(
        self,
        *,
        repository: SupplierEnrichmentReviewRepository,
        canonical_reader: CanonicalSupplierReader,
        registry_provider: CompanyRegistryProvider,
        clock: Callable[[], datetime] = _utcnow,
        review_ttl_seconds: int = 24 * 3600,
    ) -> None:
        self._repository = repository
        self._canonical_reader = canonical_reader
        self._registry_provider = registry_provider
        self._clock = clock
        self._review_ttl = timedelta(seconds=review_ttl_seconds)

    # -- create ----------------------------------------------------------

    def create_review(
        self,
        *,
        user: EffectiveUser,
        supplier_code: str,
        supplier_store: str,
        access_token: str,
    ) -> tuple[ReviewRecord, list[ProposalRecord]]:
        canonical = self._canonical_reader.read(
            supplier_code, supplier_store, access_token=access_token
        )
        if canonical is None:
            raise SupplierNotFoundError("supplier not found")
        if canonical.person_type != "J":
            raise EnrichmentUnsupportedDocumentError()

        # S2 ships no real provider — the production adapter is fail-closed
        # and raises EnrichmentSourceUnavailableError before this point.
        external = self._registry_provider.fetch(canonical.tax_id)

        # No canonical CC2 municipality index is wired in S2 — municipality
        # differences conservatively stay PENDING_VALIDATION.
        comparison = compare_supplier_snapshots(
            canonical, external, policy=CNPJ_SA2_MAPPING_V1
        ).comparison
        now = self._clock()
        review = ReviewRecord(
            review_id=str(uuid.uuid4()),
            supplier_code=comparison.supplier.code,
            supplier_store=comparison.supplier.store,
            unit_context=None,
            actor_subject=user.id,
            source_id=comparison.source_id,
            source_reference=external.source_reference,
            source_retrieved_at=_parse_timestamp(external.retrieved_at) or now,
            mapping_version=comparison.mapping_version,
            normalization_version=NORMALIZATION_VERSION_V1,
            baseline_reference=_canonical_fingerprint(canonical),
            status=ReviewStatus.IN_REVIEW.value,
            revision=1,
            created_at=now,
            updated_at=now,
            expires_at=now + self._review_ttl,
        )
        proposals = [
            self._proposal_record(review.review_id, p)
            for p in comparison.proposals
        ]
        stored = self._repository.create_review(
            review=review, proposals=proposals
        )
        return stored, proposals

    @staticmethod
    def _proposal_record(
        review_id: str, proposal: SupplierFieldProposal
    ) -> ProposalRecord:
        # tax_id values are never persisted — protected identity field.
        protected = proposal.field_key == "tax_id"
        return ProposalRecord(
            proposal_id=str(uuid.uuid4()),
            review_id=review_id,
            field_key=proposal.field_key,
            section_key=proposal.section_key,
            comparison_state=proposal.comparison.value,
            eligibility_state=proposal.eligibility.value,
            eligibility_reason=proposal.eligibility_reason,
            source_field=proposal.source_field,
            source_reference=proposal.source_reference,
            current_value=None if protected else proposal.current_value,
            suggested_value=None if protected else proposal.suggested_value,
            decision_state=FieldDecisionState.PENDING.value,
        )

    # -- queries ----------------------------------------------------------

    def get_review(
        self, *, user: EffectiveUser, review_id: str
    ) -> tuple[ReviewRecord, list[ProposalRecord]]:
        review = self._load_owned_review(user=user, review_id=review_id)
        return review, self._repository.get_proposals(review.review_id)

    def list_reviews(
        self,
        *,
        user: EffectiveUser,
        supplier_code: str,
        supplier_store: str,
        page: int,
        page_size: int,
    ) -> tuple[list[ReviewRecord], int]:
        offset = (page - 1) * page_size
        return self._repository.list_reviews(
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            actor_subject=user.id,
            limit=page_size,
            offset=offset,
        )

    def list_decisions(
        self, *, user: EffectiveUser, review_id: str
    ) -> list[DecisionRecord]:
        review = self._load_owned_review(user=user, review_id=review_id)
        return self._repository.get_decisions(review.review_id)

    # -- decisions ---------------------------------------------------------

    def decide(
        self,
        *,
        user: EffectiveUser,
        review_id: str,
        field_key: str,
        decision: Decision,
        expected_revision: int,
        idempotency_key: str,
        reason_code: str | None = None,
    ) -> tuple[ReviewRecord, list[ProposalRecord], bool]:
        payload = {
            "kind": "single",
            "field_key": field_key,
            "decision": decision.value,
            "expected_revision": expected_revision,
            "reason_code": reason_code,
        }
        ctx = self._load_for_decision(
            user=user,
            review_id=review_id,
            idempotency_key=idempotency_key,
            request_payload=payload,
        )
        if ctx.replayed:
            return ctx.review, ctx.proposals, True
        review, proposals = ctx.review, ctx.proposals
        proposal = _find_proposal(proposals, field_key)
        if proposal is None:
            raise ProposalNotFoundError(field_key)
        assert_valid_decision(_to_domain_proposal(proposal), decision)
        items = [
            DecisionItem(
                proposal_id=proposal.proposal_id,
                decision=decision,
                reason_code=reason_code,
            )
        ]
        return self._apply(
            user=user,
            review=review,
            proposals=proposals,
            decisions=items,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            request_payload=payload,
            event_type=EVENT_FIELD_DECISION,
        )

    def decide_bulk(
        self,
        *,
        user: EffectiveUser,
        review_id: str,
        decision: Decision,
        field_keys: Sequence[str],
        expected_revision: int,
        idempotency_key: str,
        reason_code: str | None = None,
    ) -> tuple[ReviewRecord, list[ProposalRecord], bool]:
        keys = list(field_keys)
        if not keys or len(set(keys)) != len(keys):
            raise InvalidDecisionRequestError(
                "field_keys must be a non-empty list without duplicates"
            )
        payload = {
            "kind": "bulk",
            "field_keys": sorted(keys),
            "decision": decision.value,
            "expected_revision": expected_revision,
            "reason_code": reason_code,
        }
        ctx = self._load_for_decision(
            user=user,
            review_id=review_id,
            idempotency_key=idempotency_key,
            request_payload=payload,
        )
        if ctx.replayed:
            return ctx.review, ctx.proposals, True
        review, proposals = ctx.review, ctx.proposals
        items: list[DecisionItem] = []
        for key in keys:
            proposal = _find_proposal(proposals, key)
            if proposal is None:
                raise ProposalNotFoundError(key)
            assert_valid_decision(_to_domain_proposal(proposal), decision)
            items.append(
                DecisionItem(
                    proposal_id=proposal.proposal_id,
                    decision=decision,
                    reason_code=reason_code,
                )
            )
        return self._apply(
            user=user,
            review=review,
            proposals=proposals,
            decisions=items,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            request_payload=payload,
            event_type=EVENT_BULK_DECISION,
        )

    def _apply(
        self,
        *,
        user: EffectiveUser,
        review: ReviewRecord,
        proposals: list[ProposalRecord],
        decisions: Sequence[DecisionItem],
        expected_revision: int,
        idempotency_key: str,
        request_payload: dict[str, Any],
        event_type: str,
    ) -> tuple[ReviewRecord, list[ProposalRecord], bool]:
        request_hash = _request_hash(request_payload)

        new_proposals = _apply_decision_states(proposals, decisions)
        new_status = next_review_status(
            ReviewStatus(review.status),
            [_to_domain_proposal(p) for p in new_proposals],
        ).value
        updated_review, updated_proposals = self._repository.apply_decisions(
            review_id=review.review_id,
            actor_subject=user.id,
            decision=decisions[0].decision,
            reason_code=decisions[0].reason_code,
            decisions=decisions,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            new_status=new_status,
            event_type=event_type,
            decided_at=self._clock(),
        )
        return updated_review, updated_proposals, False

    # -- prepare update ----------------------------------------------------

    def prepare_update(
        self,
        *,
        user: EffectiveUser,
        review_id: str,
        expected_revision: int,
        access_token: str,
    ) -> tuple[ReviewRecord, list[Any]]:
        review, proposals = self._load_actionable(
            user=user, review_id=review_id
        )
        if review.revision != expected_revision:
            raise ReviewRevisionConflictError(
                f"expected revision {expected_revision}, found {review.revision}"
            )

        canonical = self._canonical_reader.read(
            review.supplier_code, review.supplier_store, access_token=access_token
        )
        if canonical is None:
            raise SupplierNotFoundError("supplier not found")
        try:
            assert_baseline_current(
                review.baseline_reference, _canonical_fingerprint(canonical)
            )
        except EnrichmentStaleBaselineError:
            self._repository.mark_status(
                review_id=review.review_id,
                status=ReviewStatus.STALE.value,
                expected_revision=review.revision,
            )
            raise

        draft = assemble_update_draft(
            [_to_domain_proposal(p) for p in proposals]
        )
        decisions = self._repository.get_decisions(review.review_id)
        decision_by_proposal = {d.proposal_id: d.decision_id for d in decisions}
        linked = [
            replace(
                item,
                proposal_id=_proposal_id(proposals, item.field_key),
                decision_id=decision_by_proposal.get(
                    _proposal_id(proposals, item.field_key)
                ),
            )
            for item in draft
        ]
        self._repository.append_event(
            review_id=review.review_id,
            actor_subject=user.id,
            event_type=EVENT_DRAFT_PREPARED,
            metadata={"draft_fields": [d.field_key for d in linked]},
        )
        return review, linked

    # -- helpers ------------------------------------------------------------

    def _load_owned_review(
        self, *, user: EffectiveUser, review_id: str
    ) -> ReviewRecord:
        review = self._repository.get_review(review_id)
        if review is None:
            raise ReviewNotFoundError(review_id)
        if review.actor_subject != user.id:
            raise ReviewAccessDeniedError(review_id)
        return self._expire_if_due(review)

    def _expire_if_due(self, review: ReviewRecord) -> ReviewRecord:
        if (
            review.status == ReviewStatus.IN_REVIEW.value
            and review.expires_at <= self._clock()
        ):
            self._repository.mark_status(
                review_id=review.review_id,
                status=ReviewStatus.EXPIRED.value,
                expected_revision=review.revision,
            )
            self._repository.append_event(
                review_id=review.review_id,
                actor_subject=None,
                event_type=EVENT_REVIEW_EXPIRED,
                metadata=None,
            )
            review = replace(
                review,
                status=ReviewStatus.EXPIRED.value,
                revision=review.revision + 1,
            )
        return review

    def _load_actionable(
        self, *, user: EffectiveUser, review_id: str
    ) -> tuple[ReviewRecord, list[ProposalRecord]]:
        review = self._load_owned_review(user=user, review_id=review_id)
        assert_decidable(ReviewStatus(review.status))
        return review, self._repository.get_proposals(review.review_id)

    def _load_for_decision(
        self,
        *,
        user: EffectiveUser,
        review_id: str,
        idempotency_key: str,
        request_payload: dict[str, Any],
    ) -> _DecisionContext:
        """Ownership + expiry + idempotency check, in that order.

        On idempotent replay the context is flagged ``replayed`` —
        short-circuiting proposal validation: an already-applied batch
        returns the recorded outcome even though its proposals are no
        longer pending.
        """
        review = self._load_owned_review(user=user, review_id=review_id)
        proposals = self._repository.get_proposals(review.review_id)
        prior = self._repository.find_operation_by_idempotency_key(
            review_id=review.review_id, idempotency_key=idempotency_key
        )
        if prior is not None:
            if prior.request_hash != _request_hash(request_payload):
                raise IdempotencyConflictError(idempotency_key)
            return _DecisionContext(review=review, proposals=proposals, replayed=True)
        assert_decidable(ReviewStatus(review.status))
        return _DecisionContext(review=review, proposals=proposals)


# --- record helpers ---------------------------------------------------------


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _find_proposal(
    proposals: Sequence[ProposalRecord], field_key: str
) -> ProposalRecord | None:
    for proposal in proposals:
        if proposal.field_key == field_key:
            return proposal
    return None


def _proposal_id(proposals: Sequence[ProposalRecord], field_key: str) -> str | None:
    proposal = _find_proposal(proposals, field_key)
    return proposal.proposal_id if proposal else None


def _to_domain_proposal(record: ProposalRecord) -> SupplierFieldProposal:
    from app.domain.supplier_enrichment.models import (
        ComparisonState,
        EligibilityState,
    )

    return SupplierFieldProposal(
        field_key=record.field_key,
        section_key=record.section_key,
        current_value=record.current_value,
        suggested_value=record.suggested_value,
        comparison=ComparisonState(record.comparison_state),
        eligibility=EligibilityState(record.eligibility_state),
        eligibility_reason=record.eligibility_reason,
        source_field=record.source_field,
        source_reference=record.source_reference,
        normalization_version=NORMALIZATION_VERSION_V1,
        decision=FieldDecisionState(record.decision_state),
    )


def _apply_decision_states(
    proposals: Sequence[ProposalRecord],
    decisions: Sequence[DecisionItem],
) -> list[ProposalRecord]:
    outcome = {item.proposal_id: item.decision for item in decisions}
    updated: list[ProposalRecord] = []
    for proposal in proposals:
        decision = outcome.get(proposal.proposal_id)
        if decision is None:
            updated.append(proposal)
            continue
        updated.append(
            replace(proposal, decision_state=DECISION_OUTCOME[decision].value)
        )
    return updated

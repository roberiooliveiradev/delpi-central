"""S2 application tests — supplier enrichment review service.

Synthetic fixtures only. No network, no Postgres, no real CNPJ, no Protheus.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    IdempotencyConflictError,
    ProposalRecord,
    ReviewAccessDeniedError,
    ReviewNotFoundError,
    ReviewRecord,
    ReviewRevisionConflictError,
    SupplierNotFoundError,
)
from app.application.services.supplier_enrichment.review_service import (
    InvalidDecisionRequestError,
    ProposalNotFoundError,
    SupplierEnrichmentReviewService,
)
from app.domain.entities import EffectiveUser
from app.domain.exceptions import EnrichmentUnsupportedDocumentError
from app.domain.supplier_enrichment.models import (
    CanonicalSupplierSnapshot,
    ExternalRegistrySnapshot,
    SupplierRef,
)
from app.domain.supplier_enrichment.review_lifecycle import (
    Decision,
    EnrichmentProposalNotEligibleError,
    EnrichmentProposalNotPendingError,
    EnrichmentReviewNotActionableError,
    EnrichmentStaleBaselineError,
    ReviewStatus,
)

# Synthetic values — not real registry data.
TAX_ID = "11222333000144"
NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

CANONICAL_FIELDS = {
    "supplier_name": "ACME BRASIL LTDA",
    "supplier_short_name": "ACME",
    "address": "RUA ANTIGA, 1",
    "district": "CENTRO",
    "postal_code": "89010000",
    "city": "BLUMENAU",
    "state": "SC",
    "city_code": "02404",
    "area_code": "47",
    "phone": "4733221100",
    "email": "contato@acme.example",
}

EXTERNAL_FIELDS = {
    "company.tax_id": TAX_ID,
    "company.legal_name": "ACME BRASIL SOCIEDADE LTDA",
    "company.trade_name": "ACME",
    "address.street": "RUA DAS FLORES, 100",
    "address.district": "CENTRO",
    "address.postal_code": "89010000",
    "address.city": "BLUMENAU",
    "address.state": "SC",
    "address.ibge_city_code": "4202404",
    "contact.area_code": "47",
    "contact.phone": "33221100",
    "contact.email": "contato@acme.example",
}


def _canonical(**overrides) -> CanonicalSupplierSnapshot:
    return CanonicalSupplierSnapshot(
        supplier=overrides.pop("supplier", SupplierRef(code="003878", store="01")),
        tax_id=overrides.pop("tax_id", TAX_ID),
        person_type=overrides.pop("person_type", "J"),
        fields=overrides.pop("fields", dict(CANONICAL_FIELDS)),
    )


def _external(**overrides) -> ExternalRegistrySnapshot:
    return ExternalRegistrySnapshot(
        tax_id=overrides.pop("tax_id", TAX_ID),
        source_id=overrides.pop("source_id", "FIXTURE_REGISTRY"),
        retrieved_at=overrides.pop("retrieved_at", "2026-06-01T10:00:00+00:00"),
        fields=overrides.pop("fields", dict(EXTERNAL_FIELDS)),
        source_reference=overrides.pop("source_reference", "fixture://cnpj/1"),
    )


class FakeCanonicalReader:
    def __init__(self, snapshot=None):
        self.snapshot = snapshot
        self.calls = 0

    def read(self, supplier_code, supplier_store, *, access_token):
        self.calls += 1
        return self.snapshot() if callable(self.snapshot) else self.snapshot


class FakeRegistryProvider:
    def __init__(self, snapshot=None):
        self.snapshot = snapshot or _external()

    def fetch(self, tax_id):
        return self.snapshot


class UnavailableProvider:
    def fetch(self, tax_id):
        raise EnrichmentSourceUnavailableError("unavailable")


class InMemoryReviewRepository:
    """Test double implementing the repository port with the same
    optimistic-concurrency and idempotency semantics as Postgres."""

    def __init__(self):
        self.reviews: dict[str, ReviewRecord] = {}
        self.proposals: dict[str, list[ProposalRecord]] = {}
        self.decisions: list = []
        self.operations: list = []
        self.events: list[dict] = []

    def create_review(self, *, review, proposals):
        self.reviews[review.review_id] = review
        self.proposals[review.review_id] = list(proposals)
        self.events.append({"review_id": review.review_id, "type": "REVIEW_CREATED"})
        return review

    def get_review(self, review_id):
        return self.reviews.get(review_id)

    def list_reviews(self, *, supplier_code, supplier_store, actor_subject,
                     limit, offset):
        items = [
            r for r in self.reviews.values()
            if r.supplier_code == supplier_code
            and r.supplier_store == supplier_store
            and r.actor_subject == actor_subject
        ]
        items.sort(key=lambda r: (r.created_at, r.review_id), reverse=True)
        return items[offset:offset + limit], len(items)

    def get_proposals(self, review_id):
        return list(self.proposals.get(review_id, []))

    def get_decisions(self, review_id):
        return [d for d in self.decisions if d.review_id == review_id]

    def find_operation_by_idempotency_key(self, *, review_id, idempotency_key):
        for op in self.operations:
            if op.review_id == review_id and op.idempotency_key == idempotency_key:
                return op
        return None

    def apply_decisions(self, *, review_id, actor_subject, decision, reason_code,
                        decisions, expected_revision, idempotency_key,
                        request_hash, new_status, event_type, decided_at):
        review = self.reviews[review_id]
        if review.revision != expected_revision:
            raise ReviewRevisionConflictError("revision mismatch")
        # Atomicity: validate all proposals still pending before any update.
        for item in decisions:
            prop = next(
                p for p in self.proposals[review_id]
                if p.proposal_id == item.proposal_id
            )
            if prop.decision_state != "PENDING":
                raise ReviewRevisionConflictError("proposal no longer pending")
        operation_id = f"op-{len(self.operations)+1}"
        self.operations.append(
            type("O", (), dict(
                operation_id=operation_id, review_id=review_id,
                actor_subject=actor_subject, decision=decision.value,
                reason_code=reason_code, decided_at=decided_at,
                review_revision=expected_revision,
                idempotency_key=idempotency_key, request_hash=request_hash,
            ))()
        )
        for item in decisions:
            prop = next(
                p for p in self.proposals[review_id]
                if p.proposal_id == item.proposal_id
            )
            state = "ACCEPTED_FOR_DRAFT" if item.decision is Decision.ACCEPT \
                else "REJECTED_SUGGESTION"
            self.proposals[review_id] = [
                replace(p, decision_state=state)
                if p.proposal_id == item.proposal_id else p
                for p in self.proposals[review_id]
            ]
            self.decisions.append(
                type("D", (), dict(
                    decision_id=f"dec-{len(self.decisions)+1}",
                    review_id=review_id, proposal_id=item.proposal_id,
                    operation_id=operation_id, field_key=prop.field_key,
                    actor_subject=actor_subject, decision=item.decision.value,
                    reason_code=reason_code, decided_at=decided_at,
                    review_revision=expected_revision,
                ))()
            )
            self.events.append({"review_id": review_id, "type": event_type})
        updated = replace(
            review, status=new_status, revision=review.revision + 1,
            updated_at=decided_at,
        )
        self.reviews[review_id] = updated
        return updated, self.proposals[review_id]

    def mark_status(self, *, review_id, status, expected_revision):
        review = self.reviews[review_id]
        if review.revision != expected_revision:
            raise ReviewRevisionConflictError("revision mismatch")
        self.reviews[review_id] = replace(
            review, status=status, revision=review.revision + 1
        )

    def append_event(self, *, review_id, actor_subject, event_type, metadata):
        self.events.append({"review_id": review_id, "type": event_type})


def _user(user_id="22222222-2222-2222-2222-222222222222"):
    return EffectiveUser(
        id=user_id, email="buyer@delpi.com.br", name="Buyer",
        permissions={"supplies.access"}, access_token="tok",
    )


def _service(repo=None, canonical=None, provider=None, clock=lambda: NOW):
    repo = repo or InMemoryReviewRepository()
    svc = SupplierEnrichmentReviewService(
        repository=repo,
        canonical_reader=canonical or FakeCanonicalReader(_canonical()),
        registry_provider=provider or FakeRegistryProvider(),
        clock=clock,
        review_ttl_seconds=3600,
    )
    return svc, repo


def _created(service):
    return service.create_review(
        user=_user(), supplier_code="003878", supplier_store="01",
        access_token="tok",
    )


def _proposal(service, review_id, field_key):
    props = service._repository.get_proposals(review_id)
    return next(p for p in props if p.field_key == field_key)


class TestCreateReview:
    def test_happy_path_persists_review_and_proposals(self):
        svc, repo = _service()
        review, proposals = _created(svc)
        assert review.status == "IN_REVIEW"
        assert review.revision == 1
        assert review.actor_subject == "22222222-2222-2222-2222-222222222222"
        assert len(proposals) == 16
        assert repo.events[0]["type"] == "REVIEW_CREATED"
        assert repo.get_review(review.review_id).review_id == review.review_id

    def test_tax_id_values_never_persisted(self):
        svc, _ = _service()
        _, proposals = _created(svc)
        tax = next(p for p in proposals if p.field_key == "tax_id")
        assert tax.current_value is None
        assert tax.suggested_value is None
        assert tax.eligibility_state == "PROTECTED"

    def test_supplier_not_found(self):
        svc, _ = _service(canonical=FakeCanonicalReader(None))
        with pytest.raises(SupplierNotFoundError):
            _created(svc)

    def test_non_legal_entity_rejected(self):
        svc, _ = _service(
            canonical=FakeCanonicalReader(_canonical(person_type="F", tax_id="12345678901"))
        )
        with pytest.raises(EnrichmentUnsupportedDocumentError):
            _created(svc)

    @pytest.mark.parametrize("person_type", ["", " ", None])
    def test_missing_or_blank_person_type_rejected(self, person_type):
        # Gate PJ é fail-closed: campo ausente/vazio nunca é presumido "J".
        svc, repo = _service(
            canonical=FakeCanonicalReader(_canonical(person_type=person_type))
        )
        with pytest.raises(EnrichmentUnsupportedDocumentError):
            _created(svc)
        assert not repo.reviews

    def test_provider_unavailable_blocks_creation(self):
        svc, repo = _service(provider=UnavailableProvider())
        with pytest.raises(EnrichmentSourceUnavailableError):
            _created(svc)
        assert not repo.reviews  # nothing persisted


class TestGetAndList:
    def test_owner_reads_review(self):
        svc, _ = _service()
        review, _ = _created(svc)
        loaded, proposals = svc.get_review(user=_user(), review_id=review.review_id)
        assert loaded.review_id == review.review_id
        assert proposals

    def test_cross_actor_denied(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(ReviewAccessDeniedError):
            svc.get_review(
                user=_user("33333333-3333-3333-3333-333333333333"),
                review_id=review.review_id,
            )

    def test_unknown_review_404(self):
        svc, _ = _service()
        with pytest.raises(ReviewNotFoundError):
            svc.get_review(user=_user(), review_id=str(__import__("uuid").uuid4()))

    def test_list_is_actor_scoped_and_paginated(self):
        svc, repo = _service()
        _created(svc)
        _created(svc)
        _created(svc)
        # Other actor's review on the same supplier must not appear.
        other_repo_review = ReviewRecord(
            review_id="99999999-9999-9999-9999-999999999999",
            supplier_code="003878", supplier_store="01", unit_context=None,
            actor_subject="33333333-3333-3333-3333-333333333333",
            source_id="S", source_reference=None, source_retrieved_at=None,
            mapping_version="v1", normalization_version="n1",
            baseline_reference="x", status="IN_REVIEW", revision=1,
            created_at=NOW, updated_at=NOW,
            expires_at=NOW + timedelta(hours=1),
        )
        repo.reviews[other_repo_review.review_id] = other_repo_review
        items, total = svc.list_reviews(
            user=_user(), supplier_code="003878", supplier_store="01",
            page=1, page_size=2,
        )
        assert total == 3 and len(items) == 2
        items2, _ = svc.list_reviews(
            user=_user(), supplier_code="003878", supplier_store="01",
            page=2, page_size=2,
        )
        assert len(items2) == 1

    def test_lazy_expiry(self):
        clock_holder = {"t": NOW}
        svc, repo = _service(clock=lambda: clock_holder["t"])
        review, _ = _created(svc)
        clock_holder["t"] = NOW + timedelta(hours=2)
        loaded, _ = svc.get_review(user=_user(), review_id=review.review_id)
        assert loaded.status == "EXPIRED"
        assert repo.reviews[review.review_id].status == "EXPIRED"
        assert any(e["type"] == "REVIEW_EXPIRED" for e in repo.events)


class TestIndividualDecision:
    def test_accept_eligible(self):
        svc, _ = _service()
        review, _ = _created(svc)
        updated, proposals, replayed = svc.decide(
            user=_user(), review_id=review.review_id, field_key="supplier_name",
            decision=Decision.ACCEPT, expected_revision=1,
            idempotency_key="k-1",
        )
        assert updated.revision == 2
        assert replayed is False
        prop = next(p for p in proposals if p.field_key == "supplier_name")
        assert prop.decision_state == "ACCEPTED_FOR_DRAFT"

    def test_reject_pending(self):
        svc, _ = _service()
        review, _ = _created(svc)
        _, proposals, _ = svc.decide(
            user=_user(), review_id=review.review_id, field_key="address",
            decision=Decision.REJECT, expected_revision=1,
            idempotency_key="k-2",
        )
        prop = next(p for p in proposals if p.field_key == "address")
        assert prop.decision_state == "REJECTED_SUGGESTION"

    def test_accept_non_eligible_blocked(self):
        svc, _ = _service()
        review, _ = _created(svc)
        # short_name has requires_equivalence_rule → PENDING_VALIDATION
        with pytest.raises(EnrichmentProposalNotEligibleError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="supplier_short_name",
                decision=Decision.ACCEPT, expected_revision=1,
                idempotency_key="k-3",
            )

    def test_accept_protected_blocked(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(EnrichmentProposalNotEligibleError):
            svc.decide(
                user=_user(), review_id=review.review_id, field_key="tax_id",
                decision=Decision.ACCEPT, expected_revision=1,
                idempotency_key="k-4",
            )

    def test_unknown_field_key(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(ProposalNotFoundError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="nonexistent", decision=Decision.REJECT,
                expected_revision=1, idempotency_key="k-5",
            )

    def test_revision_conflict(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(ReviewRevisionConflictError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="supplier_name", decision=Decision.ACCEPT,
                expected_revision=99, idempotency_key="k-6",
            )

    def test_already_decided_conflict(self):
        svc, _ = _service()
        review, _ = _created(svc)
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="k-7",
        )
        with pytest.raises(EnrichmentProposalNotPendingError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="supplier_name", decision=Decision.REJECT,
                expected_revision=2, idempotency_key="k-8",
            )

    def test_idempotent_replay_same_payload(self):
        svc, repo = _service()
        review, _ = _created(svc)
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="k-9",
        )
        _, _, replayed = svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="k-9",
        )
        assert replayed is True
        assert len(repo.decisions) == 1

    def test_idempotency_key_reuse_different_payload_conflicts(self):
        svc, _ = _service()
        review, _ = _created(svc)
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="k-10",
        )
        with pytest.raises(IdempotencyConflictError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="district", decision=Decision.REJECT,
                expected_revision=1, idempotency_key="k-10",
            )

    def test_expired_review_rejects_decisions(self):
        clock_holder = {"t": NOW}
        svc, _ = _service(clock=lambda: clock_holder["t"])
        review, _ = _created(svc)
        clock_holder["t"] = NOW + timedelta(hours=2)
        with pytest.raises(EnrichmentReviewNotActionableError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="supplier_name", decision=Decision.ACCEPT,
                expected_revision=1, idempotency_key="k-11",
            )

    def test_decision_history_recorded(self):
        svc, _ = _service()
        review, _ = _created(svc)
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="k-12", reason_code="manual_check",
        )
        history = svc.list_decisions(user=_user(), review_id=review.review_id)
        assert len(history) == 1
        assert history[0].decision == "ACCEPT"
        assert history[0].actor_subject == _user().id
        assert history[0].review_revision == 1


class TestBulkDecisions:
    def test_bulk_accept_eligible(self):
        svc, _ = _service()
        review, _ = _created(svc)
        updated, proposals, _ = svc.decide_bulk(
            user=_user(), review_id=review.review_id,
            decision=Decision.ACCEPT,
            field_keys=["supplier_name", "address"],
            expected_revision=1, idempotency_key="b-1",
        )
        assert updated.revision == 2
        decided = {p.field_key for p in proposals if p.decision_state == "ACCEPTED_FOR_DRAFT"}
        assert decided == {"supplier_name", "address"}

    def test_bulk_all_validated_before_apply(self):
        svc, repo = _service()
        review, _ = _created(svc)
        with pytest.raises(EnrichmentProposalNotEligibleError):
            svc.decide_bulk(
                user=_user(), review_id=review.review_id,
                decision=Decision.ACCEPT,
                field_keys=["supplier_name", "tax_id"],
                expected_revision=1, idempotency_key="b-2",
            )
        # Nothing changed — atomic validation.
        assert all(p.decision_state == "PENDING" for p in repo.proposals[review.review_id])
        assert not repo.decisions

    def test_bulk_empty_or_duplicates_rejected(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(InvalidDecisionRequestError):
            svc.decide_bulk(
                user=_user(), review_id=review.review_id,
                decision=Decision.REJECT, field_keys=[],
                expected_revision=1, idempotency_key="b-3",
            )
        with pytest.raises(InvalidDecisionRequestError):
            svc.decide_bulk(
                user=_user(), review_id=review.review_id,
                decision=Decision.REJECT, field_keys=["address", "address"],
                expected_revision=1, idempotency_key="b-4",
            )

    def test_bulk_reject_non_eligible_allowed(self):
        svc, _ = _service()
        review, _ = _created(svc)
        _, proposals, _ = svc.decide_bulk(
            user=_user(), review_id=review.review_id,
            decision=Decision.REJECT,
            field_keys=["supplier_short_name", "phone"],
            expected_revision=1, idempotency_key="b-5",
        )
        assert all(
            p.decision_state == "REJECTED_SUGGESTION"
            for p in proposals if p.field_key in {"supplier_short_name", "phone"}
        )

    def test_review_becomes_decided_when_all_resolved(self):
        svc, _ = _service()
        review, _ = _created(svc)
        all_keys = [p.field_key for p in svc._repository.get_proposals(review.review_id)]
        # Reject everything (reject allowed regardless of eligibility).
        updated, proposals, _ = svc.decide_bulk(
            user=_user(), review_id=review.review_id,
            decision=Decision.REJECT, field_keys=all_keys,
            expected_revision=1, idempotency_key="b-6",
        )
        assert updated.status == "DECIDED"
        assert all(p.decision_state != "PENDING" for p in proposals)

    def test_review_stays_in_review_with_pending(self):
        svc, _ = _service()
        review, _ = _created(svc)
        updated, _, _ = svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="b-7",
        )
        assert updated.status == "IN_REVIEW"

    def test_bulk_idempotent_replay_same_payload(self):
        svc, repo = _service()
        review, _ = _created(svc)
        svc.decide_bulk(
            user=_user(), review_id=review.review_id,
            decision=Decision.REJECT,
            field_keys=["supplier_name", "address"],
            expected_revision=1, idempotency_key="b-8",
        )
        _, _, replayed = svc.decide_bulk(
            user=_user(), review_id=review.review_id,
            decision=Decision.REJECT,
            field_keys=["address", "supplier_name"],  # order-insensitive payload
            expected_revision=1, idempotency_key="b-8",
        )
        assert replayed is True
        assert len(repo.decisions) == 2
        assert len(repo.operations) == 1

    def test_bulk_idempotency_key_reuse_different_payload_conflicts(self):
        svc, _ = _service()
        review, _ = _created(svc)
        svc.decide_bulk(
            user=_user(), review_id=review.review_id,
            decision=Decision.REJECT, field_keys=["supplier_name"],
            expected_revision=1, idempotency_key="b-9",
        )
        with pytest.raises(IdempotencyConflictError):
            svc.decide_bulk(
                user=_user(), review_id=review.review_id,
                decision=Decision.ACCEPT, field_keys=["supplier_name"],
                expected_revision=1, idempotency_key="b-9",
            )

    def test_stale_expected_revision_conflicts(self):
        # B3 — a concurrent apply bumps the revision; a subsequent decide
        # carrying the stale expectation must conflict, not silently apply.
        svc, _ = _service()
        review, _ = _created(svc)
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="r-1",
        )
        with pytest.raises(ReviewRevisionConflictError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="address", decision=Decision.REJECT,
                expected_revision=1, idempotency_key="r-2",
            )


class TestPrepareUpdate:
    def test_draft_contains_only_accepted_eligible(self):
        svc, _ = _service()
        review, _ = _created(svc)
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="supplier_name", decision=Decision.ACCEPT,
            expected_revision=1, idempotency_key="p-1",
        )
        svc.decide(
            user=_user(), review_id=review.review_id,
            field_key="address", decision=Decision.REJECT,
            expected_revision=2, idempotency_key="p-2",
        )
        review, draft = svc.prepare_update(
            user=_user(), review_id=review.review_id,
            expected_revision=3, access_token="tok",
        )
        keys = [d.field_key for d in draft]
        assert keys == ["supplier_name"]
        assert "tax_id" not in keys and "address" not in keys
        assert draft[0].proposed_value == "ACME BRASIL SOCIEDADE LTDA"
        assert draft[0].decision_id and draft[0].proposal_id
        assert any(e["type"] == "DRAFT_PREPARED" for e in svc._repository.events)

    def test_stale_baseline_blocks_and_marks(self):
        svc, repo = _service()
        review, _ = _created(svc)
        # Canonical changed — different fingerprint.
        svc._canonical_reader = FakeCanonicalReader(
            _canonical(fields={**CANONICAL_FIELDS, "supplier_name": "MUDOU LTDA"})
        )
        with pytest.raises(EnrichmentStaleBaselineError):
            svc.prepare_update(
                user=_user(), review_id=review.review_id,
                expected_revision=1, access_token="tok",
            )
        assert repo.reviews[review.review_id].status == "STALE"
        # STALE review blocks further decisions.
        with pytest.raises(EnrichmentReviewNotActionableError):
            svc.decide(
                user=_user(), review_id=review.review_id,
                field_key="supplier_name", decision=Decision.ACCEPT,
                expected_revision=2, idempotency_key="p-3",
            )

    def test_prepare_revision_conflict(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(ReviewRevisionConflictError):
            svc.prepare_update(
                user=_user(), review_id=review.review_id,
                expected_revision=42, access_token="tok",
            )

    def test_prepare_cross_actor_denied(self):
        svc, _ = _service()
        review, _ = _created(svc)
        with pytest.raises(ReviewAccessDeniedError):
            svc.prepare_update(
                user=_user("33333333-3333-3333-3333-333333333333"),
                review_id=review.review_id, expected_revision=1,
                access_token="tok",
            )

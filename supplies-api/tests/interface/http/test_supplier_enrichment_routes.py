"""S2 HTTP tests — supplier enrichment review routes.

AuthZ, input validation, error mapping and server-owned-field rejection.
Service layer is patched; fixtures are synthetic only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    IdempotencyConflictError,
    ReviewAccessDeniedError,
    ReviewNotFoundError,
    ReviewRevisionConflictError,
    SupplierNotFoundError,
)
from app.application.services.supplier_enrichment.review_service import (
    ProposalNotFoundError,
)
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.supplier_enrichment.review_lifecycle import (
    EnrichmentProposalNotEligibleError,
    EnrichmentReviewNotActionableError,
    EnrichmentStaleBaselineError,
    ReviewStatus,
)

BASE = "/suppliers/003878/01/enrichment-reviews"
REVIEW_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


@pytest.fixture()
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    with app.test_client() as test_client:
        yield test_client


def _identity():
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def _user(*, permissions: set[str]) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="user-jwt",
    )


def _auth(*, permissions={"supplies.access"}):
    return (
        patch(
            "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate",
            return_value=_identity(),
        ),
        patch(
            "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user",
            return_value=_user(permissions=permissions),
        ),
    )


def _review(**over):
    base = dict(
        review_id=REVIEW_ID,
        supplier_code="003878",
        supplier_store="01",
        unit_context=None,
        actor_subject="22222222-2222-2222-2222-222222222222",
        source_id="FIXTURE_REGISTRY",
        source_reference="fixture://cnpj/1",
        source_retrieved_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        mapping_version="cnpj-sa2-v1",
        normalization_version="norm-v1",
        baseline_reference="abc",
        status="IN_REVIEW",
        revision=1,
        created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        expires_at=datetime(2026, 6, 2, tzinfo=timezone.utc),
    )
    base.update(over)
    return SimpleNamespace(**base)


def _service_mock(**over):
    svc = MagicMock()
    svc.get_review.return_value = (_review(), [])
    svc.list_decisions.return_value = []
    svc.list_reviews.return_value = ([_review()], 1)
    svc.create_review.return_value = (_review(), [])
    svc.decide.return_value = (_review(revision=2), [], False)
    svc.decide_bulk.return_value = (_review(revision=2), [], False)
    svc.prepare_update.return_value = (_review(), [])
    for name, value in over.items():
        getattr(svc, name).side_effect = value
    return svc


def _patch_service(svc):
    return patch(
        "app.interfaces.http.routes.supplier_enrichment_routes._service",
        return_value=svc,
    )


HEADERS = {"Authorization": "Bearer t"}


class TestAuth:
    def test_missing_token_401(self, client):
        assert client.get(BASE).status_code == 401

    def test_no_capability_403(self, client):
        v, r = _auth(permissions={"supplies.manage"})
        with v, r, _patch_service(_service_mock()):
            assert client.get(BASE, headers=HEADERS).status_code == 403

    def test_cross_actor_forbidden(self, client):
        v, r = _auth()
        svc = _service_mock(get_review=ReviewAccessDeniedError("x"))
        with v, r, _patch_service(svc):
            resp = client.get(f"{BASE}/{REVIEW_ID}", headers=HEADERS)
        assert resp.status_code == 403
        assert resp.get_json()["code"] == "forbidden"


class TestCreate:
    def test_create_returns_201(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.post(BASE, headers=HEADERS, json={})
        assert resp.status_code == 201
        assert resp.get_json()["review"]["review_id"] == REVIEW_ID

    def test_source_unavailable_503(self, client):
        """Production default — no real provider configured."""
        v, r = _auth()
        svc = _service_mock(create_review=EnrichmentSourceUnavailableError("x"))
        with v, r, _patch_service(svc):
            resp = client.post(BASE, headers=HEADERS, json={})
        assert resp.status_code == 503
        assert resp.get_json()["code"] == "ENRICHMENT_SOURCE_UNAVAILABLE"

    def test_supplier_not_found_404(self, client):
        v, r = _auth()
        svc = _service_mock(create_review=SupplierNotFoundError("x"))
        with v, r, _patch_service(svc):
            resp = client.post(BASE, headers=HEADERS, json={})
        assert resp.status_code == 404

    def test_browser_cannot_declare_actor_or_source(self, client):
        v, r = _auth()
        svc = _service_mock()
        with v, r, _patch_service(svc):
            resp = client.post(
                BASE, headers=HEADERS,
                json={"actor_subject": "spoofed", "source_id": "GOVERNMENT_API"},
            )
        assert resp.status_code == 422
        svc.create_review.assert_not_called()

    def test_browser_cannot_send_snapshot(self, client):
        v, r = _auth()
        svc = _service_mock()
        with v, r, _patch_service(svc):
            resp = client.post(
                BASE, headers=HEADERS,
                json={"snapshot": {"company.tax_id": "00000000000000"}},
            )
        assert resp.status_code == 422
        svc.create_review.assert_not_called()


class TestList:
    def test_list_paginated(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.get(f"{BASE}?page=2&page_size=10", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["page"] == 2 and body["total"] == 1

    def test_list_invalid_pagination_422(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.get(f"{BASE}?page=abc", headers=HEADERS)
        assert resp.status_code == 422


class TestGet:
    def test_get_happy_path(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.get(f"{BASE}/{REVIEW_ID}", headers=HEADERS)
        assert resp.status_code == 200

    def test_get_404(self, client):
        v, r = _auth()
        svc = _service_mock(get_review=ReviewNotFoundError("x"))
        with v, r, _patch_service(svc):
            assert client.get(f"{BASE}/{REVIEW_ID}", headers=HEADERS).status_code == 404

    def test_invalid_review_id_422(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.get(f"{BASE}/not-a-uuid", headers=HEADERS)
        assert resp.status_code == 422

    def test_arbitrary_review_id_not_found(self, client):
        v, r = _auth()
        svc = _service_mock(get_review=ReviewNotFoundError("x"))
        with v, r, _patch_service(svc):
            resp = client.get(
                f"{BASE}/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", headers=HEADERS
            )
        assert resp.status_code == 404


class TestDecisions:
    def _payload(self, **over):
        body = {
            "field_key": "supplier_name",
            "decision": "ACCEPT",
            "expected_revision": 1,
            "idempotency_key": "k-1",
        }
        body.update(over)
        return body

    def test_accept_happy_path(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 200
        assert resp.get_json()["review"]["revision"] == 2

    def test_missing_field_key_422(self, client):
        v, r = _auth()
        body = self._payload()
        del body["field_key"]
        with v, r, _patch_service(_service_mock()):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions", headers=HEADERS, json=body
            )
        assert resp.status_code == 422

    def test_bad_decision_422(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions", headers=HEADERS,
                json=self._payload(decision="MAYBE"),
            )
        assert resp.status_code == 422

    def test_missing_idempotency_key_422(self, client):
        v, r = _auth()
        body = self._payload()
        del body["idempotency_key"]
        with v, r, _patch_service(_service_mock()):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions", headers=HEADERS, json=body
            )
        assert resp.status_code == 422

    def test_actor_spoofing_rejected(self, client):
        v, r = _auth()
        svc = _service_mock()
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions", headers=HEADERS,
                json=self._payload(actor_subject="other-user"),
            )
        assert resp.status_code == 422
        svc.decide.assert_not_called()

    def test_already_decided_409(self, client):
        v, r = _auth()
        from app.domain.supplier_enrichment.review_lifecycle import (
            EnrichmentProposalNotPendingError,
        )

        svc = _service_mock(decide=EnrichmentProposalNotPendingError("f"))
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "ENRICHMENT_PROPOSAL_ALREADY_DECIDED"

    def test_not_eligible_422(self, client):
        v, r = _auth()
        svc = _service_mock(
            decide=EnrichmentProposalNotEligibleError("f", MagicMock())
        )
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 422
        assert resp.get_json()["code"] == "ENRICHMENT_PROPOSAL_NOT_ELIGIBLE"

    def test_revision_conflict_409(self, client):
        v, r = _auth()
        svc = _service_mock(decide=ReviewRevisionConflictError("x"))
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "ENRICHMENT_REVISION_CONFLICT"

    def test_idempotency_conflict_409(self, client):
        v, r = _auth()
        svc = _service_mock(decide=IdempotencyConflictError("k"))
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "ENRICHMENT_IDEMPOTENCY_CONFLICT"

    def test_expired_review_410(self, client):
        v, r = _auth()
        svc = _service_mock(
            decide=EnrichmentReviewNotActionableError(ReviewStatus.EXPIRED)
        )
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 410
        assert resp.get_json()["code"] == "ENRICHMENT_REVIEW_EXPIRED"

    def test_proposal_not_found_404(self, client):
        v, r = _auth()
        svc = _service_mock(decide=ProposalNotFoundError("f"))
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/decisions",
                headers=HEADERS, json=self._payload(),
            )
        assert resp.status_code == 404

    def test_bulk_happy_path(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/bulk-decisions", headers=HEADERS,
                json={
                    "decision": "REJECT",
                    "field_keys": ["address", "district"],
                    "expected_revision": 1,
                    "idempotency_key": "b-1",
                },
            )
        assert resp.status_code == 200

    def test_bulk_empty_keys_422(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/bulk-decisions", headers=HEADERS,
                json={
                    "decision": "REJECT", "field_keys": [],
                    "expected_revision": 1, "idempotency_key": "b-2",
                },
            )
        assert resp.status_code == 422

    def test_decision_history(self, client):
        v, r = _auth()
        with v, r, _patch_service(_service_mock()):
            resp = client.get(f"{BASE}/{REVIEW_ID}/decisions", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.get_json()["items"] == []


class TestPrepareUpdate:
    def test_prepare_happy_path_no_write(self, client):
        v, r = _auth()
        svc = _service_mock()
        svc.prepare_update.return_value = (
            _review(),
            [SimpleNamespace(
                field_key="supplier_name", current_value="A",
                proposed_value="B", proposal_id="p1", decision_id="d1",
            )],
        )
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/prepare-update", headers=HEADERS,
                json={"expected_revision": 2},
            )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["write_gate_enabled"] is False
        assert body["baseline_status"] == "CURRENT"
        assert body["draft_fields"][0]["field_key"] == "supplier_name"
        assert "tax_id" not in str(body["draft_fields"])

    def test_prepare_stale_baseline_409(self, client):
        v, r = _auth()
        svc = _service_mock(prepare_update=EnrichmentStaleBaselineError("x"))
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/prepare-update", headers=HEADERS,
                json={"expected_revision": 1},
            )
        assert resp.status_code == 409
        assert resp.get_json()["code"] == "ENRICHMENT_STALE_BASELINE"

    def test_prepare_expired_410(self, client):
        v, r = _auth()
        svc = _service_mock(
            prepare_update=EnrichmentReviewNotActionableError(ReviewStatus.EXPIRED)
        )
        with v, r, _patch_service(svc):
            resp = client.post(
                f"{BASE}/{REVIEW_ID}/prepare-update", headers=HEADERS,
                json={"expected_revision": 1},
            )
        assert resp.status_code == 410

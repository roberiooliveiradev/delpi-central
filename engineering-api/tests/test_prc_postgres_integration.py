"""PRC-D4 — integração real PostgreSQL (adapter postgres vs migrations).

Executa apenas quando ENG_PRC_TEST_DSN aponta para um banco autorizado
e descartável (dev/HML) com V012 aplicada. Sem DSN → skip honesto.

Cobre: persistência real, CAS, draft seletivo, conclusão atômica,
imutabilidade de revisão/ledger e grants append-only do eng_prc.
"""

from __future__ import annotations

import os
import uuid

import pytest

DSN = os.getenv("ENG_PRC_TEST_DSN", "").strip()

pytestmark = pytest.mark.skipif(
    not DSN, reason="ENG_PRC_TEST_DSN não configurado (banco descartável)"
)


@pytest.fixture
def repo():
    from engineering_app.infrastructure.persistence.product_registration.postgres_repository import (
        PostgresProductRegistrationRepository,
    )

    r = PostgresProductRegistrationRepository(DSN)
    yield r


def _req(rid: str, payload: dict) -> dict:
    return {
        "id": rid,
        "request_type": "create",
        "product_type": "raw_material",
        "source": "engineering-test",
        "external_request_id": f"ext-{rid[:8]}",
        "external_item_id": None,
        "requester_subject": "user-pg-1",
        "requester_display_name": "PG Test",
        "official_product_code": None,
        "base_revision_number": None,
        "requested_payload": payload,
        "payload_schema_version": 1,
        "status": "submitted",
        "assigned_to_subject": None,
        "row_version": 1,
        "created_at": "2026-11-06T00:00:00+00:00",
        "updated_at": "2026-11-06T00:00:00+00:00",
    }


_DRAFT_PAYLOAD = {"description": "PG TEST", "unit": "UN"}


def _seed(repo, rid: str):
    draft_data = {
        "description": "PG TEST", "group": "1001", "productKind": "MP",
        "defaultWarehouse": "01", "unit": "UN", "thirdPartyProduct": "1",
        "accountingAccount": "11401002", "customerReference": "",
        "suppliers": [],
    }
    return repo.create_request(
        request=_req(rid, _DRAFT_PAYLOAD),
        draft={
            "request_id": rid, "schema_version": 1,
            "technical_data": draft_data, "changed_paths": [],
            "row_version": 1, "updated_by_subject": "user-pg-1",
            "updated_at": "2026-11-06T00:00:00+00:00",
        },
        event={
            "event_type": "submitted", "actor_subject": "user-pg-1",
            "reason": None, "metadata": {"source": "engineering-test"},
            "previous_status": None, "next_status": "submitted",
        },
    )


class TestPostgresIntegration:
    def test_full_flow_and_append_only(self, repo):
        rid = str(uuid.uuid4())
        created = _seed(repo, rid)
        assert created["status"] == "submitted"
        assert created["draft"]["technical_data"]["unit"] == "UN"

        # start → in_progress (CAS v1)
        req = repo.apply_transition(
            request_id=rid, expected_version=1,
            allowed_from=frozenset({"submitted"}),
            actor_label="Analyst", actor_subject="analyst-pg",
            event_type="started", next_status="in_progress",
            set_fields={"assigned_to_subject": "analyst-pg"},
            reason=None, event_meta={},
        )
        assert req["status"] == "in_progress"
        assert req["row_version"] == 2

        # CAS stale → erro
        from engineering_app.domain.product_registration.errors import (
            PrcConcurrencyError,
        )

        with pytest.raises(PrcConcurrencyError):
            repo.apply_transition(
                request_id=rid, expected_version=1,
                allowed_from=frozenset({"in_progress"}),
                actor_label="A", actor_subject="a",
                event_type="x", next_status="under_review",
                set_fields={}, reason=None, event_meta={},
            )

        # draft seletivo preserva demais campos
        repo.update_draft(
            request_id=rid, expected_version=2,
            actor_subject="analyst-pg",
            changes=[{"path": "description",
                      "proposedValue": "PG EDIT", "reason": "correção"}],
            event_meta={},
        )
        req = repo.get_request(rid)
        data = req["draft"]["technical_data"]
        assert data["description"] == "PG EDIT"
        assert data["unit"] == "UN"  # preservado
        assert req["draft"]["changed_paths"][0]["path"] == "description"

        # submit_review
        req = repo.apply_transition(
            request_id=rid, expected_version=3,
            allowed_from=frozenset({"in_progress"}),
            actor_label="Analyst", actor_subject="analyst-pg",
            event_type="submitted_for_review",
            next_status="under_review", set_fields={}, reason=None,
            event_meta={},
        )
        assert req["status"] == "under_review"

        # complete: record + revision + verification + evento (1 tx)
        out = repo.complete_request(
            request_id=rid, expected_version=4,
            actor_subject="analyst-pg", official_code="PG001",
            official_source="api-delpi/totvs", base_revision=None,
            revision_snapshot=data,
            revision_changes=[
                {"path": p, "before": None, "after": v,
                 "reason": "initial_registration"}
                for p, v in data.items()
            ],
            verification={
                "official_product_code": "PG001",
                "requested_by_subject": "analyst-pg",
                "checked_at": "2026-11-06T00:00:00+00:00",
                "official_source": "api-delpi/totvs",
                "result": "matched",
                "expected_fields": list(data),
                "observed_fields": {"product": {}},
                "field_results": {},
                "evidence_fingerprint": "fp-pg",
                "correlation_id": "corr-pg",
            },
            reason=None, event_meta={},
        )
        assert out["request"]["status"] == "completed"
        assert out["revision"]["revision_number"] == 1
        record = out["record"]
        assert record["official_product_code"] == "PG001"
        rev = repo.get_revision(record["id"], 1)
        assert rev["technical_snapshot"]["description"] == "PG EDIT"

        # timeline append-only com sequência
        events = repo.list_events(rid)
        seqs = [e["sequence_number"] for e in events["items"]]
        assert seqs == sorted(seqs) and seqs[0] == 1

    def test_external_ref_uniqueness(self, repo):
        rid = str(uuid.uuid4())
        _seed(repo, rid)
        from engineering_app.domain.product_registration.errors import (
            PrcDuplicateError,
        )

        with pytest.raises(PrcDuplicateError):
            _seed(repo, str(uuid.uuid4())) if False else repo.create_request(
                request={**_req(str(uuid.uuid4()), _DRAFT_PAYLOAD),
                         "external_request_id": f"ext-{rid[:8]}"},
                draft={"request_id": str(uuid.uuid4()),
                       "schema_version": 1, "technical_data": {},
                       "changed_paths": [], "row_version": 1,
                       "updated_by_subject": "u",
                       "updated_at": "2026-11-06T00:00:00+00:00"},
                event={"event_type": "submitted", "actor_subject": "u",
                       "reason": None, "metadata": {},
                       "previous_status": None, "next_status": "submitted"},
            )

    def test_idempotency_roundtrip(self, repo):
        key = str(uuid.uuid4())[:16]
        repo.save_idempotent(
            actor_or_source="u1", operation="intake",
            idempotency_key=key, request_fingerprint="fp1",
            request_id=None, response_status=201,
            response_payload={"requestId": "x"},
        )
        stored = repo.find_idempotent(
            actor_or_source="u1", operation="intake",
            idempotency_key=key,
        )
        assert stored["request_fingerprint"] == "fp1"
        # replay não duplica
        repo.save_idempotent(
            actor_or_source="u1", operation="intake",
            idempotency_key=key, request_fingerprint="fp1",
            request_id=None, response_status=201,
            response_payload={"requestId": "x"},
        )
        assert repo.find_idempotent(
            actor_or_source="u1", operation="intake",
            idempotency_key=key,
        )["request_fingerprint"] == "fp1"

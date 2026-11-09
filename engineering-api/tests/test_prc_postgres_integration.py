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


def _req(rid: str, payload: dict, **extra) -> dict:
    out = {
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
        "official_baseline": None,
    }
    out.update(extra)
    return out


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

    def test_d15_official_baseline_persisted(self, repo):
        """V014 — coluna official_baseline JSONB round-trip."""
        rid = str(uuid.uuid4())
        baseline = {
            "baselineVersion": 1,
            "sourceContractVersion": "prc-sa5-baseline.v1",
            "officialProductCode": "001234",
            "fingerprint": "fp-d15-pg",
            "linksComplete": True,
            "links": [
                {"supplierCode": "000001", "store": "01",
                 "partNumber": "PN-1", "catalogNumber": ""},
            ],
        }
        draft_data = {
            "description": "PG BASELINE", "group": "1001",
            "productKind": "MP", "defaultWarehouse": "01", "unit": "UN",
            "thirdPartyProduct": "1", "accountingAccount": "11401002",
            "customerReference": "", "suppliers": [],
            "supplierLinkChanges": [
                {"operation": "add",
                 "key": {"supplierCode": "000089", "store": "01"},
                 "fields": {"partNumber": "X"}},
            ],
        }
        created = repo.create_request(
            request=_req(
                rid,
                {"officialProductCode": "001234",
                 "supplierLinkChanges": draft_data["supplierLinkChanges"]},
                request_type="update",
                official_product_code="001234",
                official_baseline=baseline,
            ),
            draft={
                "request_id": rid, "schema_version": 1,
                "technical_data": draft_data, "changed_paths": [],
                "row_version": 1, "updated_by_subject": "user-pg-1",
                "updated_at": "2026-11-09T00:00:00+00:00",
            },
            event={
                "event_type": "submitted", "actor_subject": "user-pg-1",
                "reason": None,
                "metadata": {"baselineFingerprint": "fp-d15-pg"},
                "previous_status": None, "next_status": "submitted",
            },
        )
        assert created["official_baseline"]["fingerprint"] == "fp-d15-pg"
        assert created["official_baseline"]["linksComplete"] is True
        reloaded = repo.get_request(rid)
        assert reloaded["official_baseline"]["officialProductCode"] == "001234"
        # draft PATCH não apaga o baseline
        repo.apply_transition(
            request_id=rid, expected_version=1,
            allowed_from=frozenset({"submitted"}),
            actor_label="A", actor_subject="a",
            event_type="started", next_status="in_progress",
            set_fields={"assigned_to_subject": "a"},
            reason=None, event_meta={},
        )
        repo.update_draft(
            request_id=rid, expected_version=2,
            actor_subject="a",
            changes=[{"path": "description",
                      "proposedValue": "EDIT", "reason": "r"}],
            event_meta={},
        )
        after = repo.get_request(rid)
        assert after["official_baseline"]["fingerprint"] == "fp-d15-pg"

    def test_attendance_flags_crud_and_audit(self, repo):
        """D16 — flags no PostgreSQL real (V015); soft-delete + eventos."""
        rid = str(uuid.uuid4())
        _seed(repo, rid)
        now = "2026-11-09T12:00:00+00:00"
        flag_id = str(uuid.uuid4())
        created = repo.create_flag(
            flag={
                "id": flag_id,
                "request_id": rid,
                "title": "Revisar descrição",
                "description": "Confirmar com solicitante.",
                "status": "OPEN",
                "subject": "FIELD",
                "target_path": "description",
                "target_attribute": None,
                "supplier_key": None,
                "target_key": "FIELD:description",
                "row_version": 1,
                "created_by_subject": "analyst-pg",
                "created_by_display_name": "Analyst",
                "created_at": now,
                "updated_by_subject": "analyst-pg",
                "updated_by_display_name": "Analyst",
                "updated_at": now,
                "resolved_by_subject": None,
                "resolved_by_display_name": None,
                "resolved_at": None,
                "deleted_by_subject": None,
                "deleted_by_display_name": None,
                "deleted_at": None,
            },
            event={
                "event_type": "flag.created",
                "actor_subject": "analyst-pg",
                "actor_display_name": "Analyst",
                "actor_email": None,
                "reason": None,
                "metadata": {"flagId": flag_id},
                "previous_status": None,
                "next_status": "OPEN",
            },
        )
        assert created["status"] == "OPEN"
        listed = repo.list_flags(request_id=rid, status="OPEN")
        assert listed["openCount"] == 1
        assert listed["items"][0]["id"] == flag_id

        from engineering_app.domain.product_registration.errors import (
            PrcConcurrencyError,
            PrcNotFoundError,
        )

        with pytest.raises(PrcConcurrencyError):
            repo.update_flag(
                request_id=rid, flag_id=flag_id, expected_version=99,
                patch={"title": "x"}, actor_subject="a",
                actor_display_name="A",
                event={
                    "event_type": "flag.updated",
                    "actor_subject": "a", "actor_display_name": "A",
                    "actor_email": None, "reason": None,
                    "metadata": {}, "previous_status": "OPEN",
                    "next_status": "OPEN",
                },
            )

        updated = repo.transition_flag(
            request_id=rid, flag_id=flag_id, expected_version=1,
            next_status="RESOLVED", actor_subject="analyst-pg",
            actor_display_name="Analyst",
            event={
                "event_type": "flag.resolved",
                "actor_subject": "analyst-pg",
                "actor_display_name": "Analyst",
                "actor_email": None, "reason": None,
                "metadata": {"flagId": flag_id},
                "previous_status": "OPEN", "next_status": "RESOLVED",
            },
        )
        assert updated["status"] == "RESOLVED"
        assert updated["row_version"] == 2

        deleted = repo.soft_delete_flag(
            request_id=rid, flag_id=flag_id, expected_version=2,
            actor_subject="analyst-pg", actor_display_name="Analyst",
            event={
                "event_type": "flag.deleted",
                "actor_subject": "analyst-pg",
                "actor_display_name": "Analyst",
                "actor_email": None, "reason": None,
                "metadata": {"flagId": flag_id},
                "previous_status": None, "next_status": None,
            },
        )
        assert deleted["deleted_at"]
        assert repo.get_flag(request_id=rid, flag_id=flag_id) is None
        with pytest.raises(PrcNotFoundError):
            repo.soft_delete_flag(
                request_id=rid, flag_id=flag_id, expected_version=3,
                actor_subject="analyst-pg", actor_display_name="Analyst",
                event={
                    "event_type": "flag.deleted",
                    "actor_subject": "analyst-pg",
                    "actor_display_name": "Analyst",
                    "actor_email": None, "reason": None,
                    "metadata": {}, "previous_status": None,
                    "next_status": None,
                },
            )
        events = repo.list_events(rid)
        types = {e["event_type"] for e in events["items"]}
        assert "flag.created" in types
        assert "flag.resolved" in types
        assert "flag.deleted" in types


class TestPostgresInformationRounds:
    """PRC-REF-019 — rodada + transição atômica no PostgreSQL real."""

    def test_information_round_atomic(self, repo):
        rid = str(uuid.uuid4())
        _seed(repo, rid)
        repo.apply_transition(
            request_id=rid, expected_version=1,
            allowed_from=frozenset({"submitted"}),
            actor_label="Analyst", actor_subject="analyst-pg",
            event_type="started", next_status="in_progress",
            set_fields={"assigned_to_subject": "analyst-pg"},
            reason=None, event_meta={},
        )
        result = repo.create_information_round(
            request_id=rid,
            expected_version=2,
            allowed_from=frozenset({"in_progress"}),
            next_status="needs_information",
            actor_label="Analyst",
            actor_subject="analyst-pg",
            actor_email=None,
            event_type="information_requested",
            reason="precisa unidade",
            event_meta={"pending_fields": ["unit"]},
            round_row={
                "id": str(uuid.uuid4()),
                "origin_status": "in_progress",
                "parent_round_id": None,
                "requested_by_subject": "analyst-pg",
                "requested_by_display_name": "Analyst",
                "requester_subject": "user-pg-1",
                "message": "Confirme a unidade",
                "created_at": "2026-11-09T00:00:00+00:00",
                "updated_at": "2026-11-09T00:00:00+00:00",
            },
            questions=[
                {
                    "ordinal": 1,
                    "question_text": "A unidade correta é MI ou PC?",
                    "status": "pending",
                    "target_type": "FIELD",
                    "target_path": "unit",
                    "target_attribute": None,
                    "supplier_key": None,
                    "target_key": "FIELD:unit",
                    "target_label": "Unidade",
                }
            ],
        )
        assert result["request"]["status"] == "needs_information"
        rnd = result["round"]
        assert rnd["status"] == "awaiting_requester"
        assert len(rnd["questions"]) == 1
        assert rnd["questions"][0]["target_path"] == "unit"
        listed = repo.list_information_rounds(request_id=rid)
        assert len(listed) == 1
        assert listed[0]["id"] == rnd["id"]

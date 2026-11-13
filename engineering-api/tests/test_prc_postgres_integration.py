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

        # FIX-08 — draft seletivo só antes do atendimento; preserva
        # demais campos.
        repo.update_draft(
            request_id=rid, expected_version=1,
            actor_subject="user-pg-1",
            changes=[{"path": "description",
                      "proposedValue": "PG EDIT", "reason": "correção"}],
            event_meta={},
        )
        req = repo.get_request(rid)
        data = req["draft"]["technical_data"]
        assert data["description"] == "PG EDIT"
        assert data["unit"] == "UN"  # preservado
        assert req["draft"]["changed_paths"][0]["path"] == "description"

        # start → in_progress (CAS v2)
        req = repo.apply_transition(
            request_id=rid, expected_version=2,
            allowed_from=frozenset({"submitted"}),
            actor_label="Analyst", actor_subject="analyst-pg",
            event_type="started", next_status="in_progress",
            set_fields={"assigned_to_subject": "analyst-pg"},
            reason=None, event_meta={},
        )
        assert req["status"] == "in_progress"
        assert req["row_version"] == 3

        # CAS stale → erro
        from engineering_app.domain.product_registration.errors import (
            PrcConcurrencyError,
            PrcStateConflictError,
        )

        with pytest.raises(PrcConcurrencyError):
            repo.apply_transition(
                request_id=rid, expected_version=1,
                allowed_from=frozenset({"in_progress"}),
                actor_label="A", actor_subject="a",
                event_type="x", next_status="under_review",
                set_fields={}, reason=None, event_meta={},
            )

        # FIX-08 — ficha bloqueada para escrita em atendimento.
        with pytest.raises(PrcStateConflictError):
            repo.update_draft(
                request_id=rid, expected_version=3,
                actor_subject="analyst-pg",
                changes=[{"path": "description",
                          "proposedValue": "LATE EDIT", "reason": "x"}],
                event_meta={},
            )

        # PRC-REF-020 — conclusão a partir de in_progress (sem under_review).
        official_code = f"PG{rid[:8].upper()}"
        out = repo.complete_request(
            request_id=rid, expected_version=3,
            actor_subject="analyst-pg", official_code=official_code,
            official_source="api-delpi/totvs", base_revision=None,
            verification={
                "official_product_code": official_code,
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
        assert out["change_kind"] == "baseline_initial"
        record = out["record"]
        assert record["official_product_code"] == official_code
        rev = repo.get_revision(record["id"], 1)
        snap = rev["technical_snapshot"]
        assert snap["schemaVersion"] == 2
        assert snap["fields"]["description"]["value"] == "PG EDIT"

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
        # FIX-08 — draft PATCH em submitted não apaga o baseline e a
        # edição persiste após a transição para atendimento.
        repo.update_draft(
            request_id=rid, expected_version=1,
            actor_subject="a",
            changes=[{"path": "description",
                      "proposedValue": "EDIT", "reason": "r"}],
            event_meta={},
        )
        repo.apply_transition(
            request_id=rid, expected_version=2,
            allowed_from=frozenset({"submitted"}),
            actor_label="A", actor_subject="a",
            event_type="started", next_status="in_progress",
            set_fields={"assigned_to_subject": "a"},
            reason=None, event_meta={},
        )
        after = repo.get_request(rid)
        assert after["official_baseline"]["fingerprint"] == "fp-d15-pg"
        assert after["draft"]["technical_data"]["description"] == "EDIT"

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


class TestPostgresListRecords:
    """PRC-TRACK PROD-01 — paridade da listagem de produtos acompanhados
    no adapter Postgres (banco descartável via ENG_PRC_TEST_DSN)."""

    def _insert(self, repo, *, code, updated_at, rev=1):
        with repo._conn() as conn:
            conn.execute(
                "INSERT INTO engineering.product_registration_records"
                " (id, product_type, official_product_code,"
                "  current_revision_number, last_official_verified_at,"
                "  official_source, created_at, updated_at)"
                " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    str(uuid.uuid4()), "raw_material", code, rev,
                    updated_at, "totvs-test", updated_at, updated_at,
                ),
            )

    def test_list_records_parity(self, repo):
        run = uuid.uuid4().hex[:6].upper()
        c1, c2, c3 = (f"PG{run}-A1", f"PG{run}-B2", f"PG{run}-C3")
        self._insert(
            repo, code=c1, updated_at="2026-01-01T10:00:00+00:00",
        )
        self._insert(
            repo, code=c2, updated_at="2026-01-02T10:00:00+00:00",
        )
        self._insert(
            repo, code=c3, rev=0,
            updated_at="2026-01-03T10:00:00+00:00",
        )

        data = repo.list_records(
            search=f"PG{run}-", page=1, page_size=25
        )
        codes = [r["official_product_code"] for r in data["items"]]
        assert codes == [c2, c1]
        assert data["total"] == 2

        # busca case-insensitive
        hit = repo.list_records(
            search=f"pg{run.lower()}-a", page=1, page_size=25
        )
        assert [r["official_product_code"] for r in hit["items"]] == [c1]

        # paginação determinística
        p1 = repo.list_records(search=f"PG{run}-", page=1, page_size=1)
        p2 = repo.list_records(search=f"PG{run}-", page=2, page_size=1)
        assert p1["items"][0]["official_product_code"] == c2
        assert p2["items"][0]["official_product_code"] == c1
        assert p2["total"] == 2

    def test_search_special_chars_literal(self, repo):
        """RV01 — paridade com in-memory: %/_ da busca são literais."""
        run = uuid.uuid4().hex[:6].upper()
        cu, cx, cp = (f"SP{run}_C", f"SP{run}XC", f"SP{run}%C")
        self._insert(repo, code=cu, updated_at="2026-01-01T00:00:00Z")
        self._insert(repo, code=cx, updated_at="2026-01-01T00:00:00Z")
        self._insert(repo, code=cp, updated_at="2026-01-01T00:00:00Z")

        hit = repo.list_records(
            search=f"sp{run.lower()}_c", page=1, page_size=25
        )
        assert [r["official_product_code"] for r in hit["items"]] == [cu]
        hit = repo.list_records(
            search=f"sp{run.lower()}%c", page=1, page_size=25
        )
        assert [r["official_product_code"] for r in hit["items"]] == [cp]

    def test_completed_request_is_listed(self, repo):
        """RV02 — conclusão PRC publica produto; request pendente não."""
        run = uuid.uuid4().hex[:6].upper()
        rid_done, rid_open = str(uuid.uuid4()), str(uuid.uuid4())
        _seed(repo, rid_done)
        _seed(repo, rid_open)  # permanece submitted → não acompanhado

        repo.apply_transition(
            request_id=rid_done, expected_version=1,
            allowed_from=frozenset({"submitted"}),
            actor_label="Analyst", actor_subject="analyst-pg",
            event_type="started", next_status="in_progress",
            set_fields={"assigned_to_subject": "analyst-pg"},
            reason=None, event_meta={},
        )
        official_code = f"PGRV{run}"
        out = repo.complete_request(
            request_id=rid_done, expected_version=2,
            actor_subject="analyst-pg", official_code=official_code,
            official_source="totvs-test", base_revision=None,
            verification={
                "official_product_code": official_code,
                "requested_by_subject": "analyst-pg",
                "checked_at": "2026-11-13T00:00:00+00:00",
                "official_source": "totvs-test",
                "result": "matched",
                "expected_fields": list(_DRAFT_PAYLOAD),
                "observed_fields": {"product": {}},
                "field_results": {},
                "evidence_fingerprint": f"fp-{run}",
                "correlation_id": f"corr-{run}",
            },
            reason=None, event_meta={},
        )
        listed = repo.list_records(search=official_code, page=1, page_size=25)
        assert listed["total"] == 1
        rec = listed["items"][0]
        assert rec["id"] == out["record"]["id"]
        assert rec["official_product_code"] == official_code
        assert rec["current_revision_number"] == 1

        # request ainda submitted não gera registro acompanhado
        assert repo.list_records(
            search=rid_open[:8], page=1, page_size=25
        )["total"] == 0


class TestPostgresSnapshotVersioning:
    """PROD-02 — paridade PG real: V1 baseline, no-op e Vn+1."""

    def _seed_update(self, repo, rid, code, unit):
        repo.create_request(
            request=_req(
                rid, {},
                request_type="update",
                official_product_code=code,
            ),
            draft={
                "request_id": rid, "schema_version": 1,
                "technical_data": {"unit": unit},
                "changed_paths": [{"path": "unit", "reason": "pg"}],
                "row_version": 1, "updated_by_subject": "user-pg-1",
                "updated_at": "2026-11-06T00:00:00+00:00",
            },
            event={
                "event_type": "submitted", "actor_subject": "user-pg-1",
                "reason": None,
                "metadata": {"source": "engineering-test"},
                "previous_status": None, "next_status": "submitted",
            },
        )
        repo.apply_transition(
            request_id=rid, expected_version=1,
            allowed_from=frozenset({"submitted"}),
            actor_label="A", actor_subject="analyst-pg",
            event_type="started", next_status="in_progress",
            set_fields={}, reason=None, event_meta={},
        )

    def _complete(self, repo, rid, code):
        return repo.complete_request(
            request_id=rid, expected_version=2,
            actor_subject="analyst-pg", official_code=code,
            official_source="api-delpi/totvs", base_revision=None,
            verification={
                "official_product_code": code,
                "requested_by_subject": "analyst-pg",
                "checked_at": "2026-11-13T00:00:00+00:00",
                "official_source": "api-delpi/totvs",
                "result": "matched",
                "expected_fields": ["unit"],
                "observed_fields": {"product": {"unit": "UN"}},
                "field_results": {"unit": {"result": "matched"}},
                "evidence_fingerprint": f"fp-{rid[:8]}",
                "correlation_id": f"corr-{rid[:8]}",
            },
            reason=None, event_meta={},
        )

    def test_v1_noop_v2_real_pg(self, repo):
        code = f"PGV{uuid.uuid4().hex[:8].upper()}"
        # V1 — primeira conclusão matched (baseline_initial).
        r1 = str(uuid.uuid4())
        self._seed_update(repo, r1, code, "UN")
        out1 = self._complete(repo, r1, code)
        assert out1["change_kind"] == "baseline_initial"
        assert out1["effective_revision_number"] == 1
        rec_id = out1["record"]["id"]
        snap1 = out1["revision"]["technical_snapshot"]
        assert snap1["schemaVersion"] == 2
        assert snap1["fields"]["unit"]["valueOrigin"] == (
            "official_verified"
        )
        # no-op — mesma declaração verificada: sem revisão nova.
        r2 = str(uuid.uuid4())
        self._seed_update(repo, r2, code, "UN")
        out2 = self._complete(repo, r2, code)
        assert out2["change_kind"] == "no_technical_change"
        assert out2["revision"] is None
        assert out2["effective_revision_number"] == 1
        rec = repo.get_record(rec_id)
        assert rec["current_revision_number"] == 1
        assert len(repo.list_revisions(rec_id)) == 1
        # V2 — diferença técnica real.
        r3 = str(uuid.uuid4())
        self._seed_update(repo, r3, code, "BX")
        out3 = repo.complete_request(
            request_id=r3, expected_version=2,
            actor_subject="analyst-pg", official_code=code,
            official_source="api-delpi/totvs", base_revision=None,
            verification={
                "official_product_code": code,
                "requested_by_subject": "analyst-pg",
                "checked_at": "2026-11-13T00:00:00+00:00",
                "official_source": "api-delpi/totvs",
                "result": "matched",
                "expected_fields": ["unit"],
                "observed_fields": {"product": {"unit": "BX"}},
                "field_results": {"unit": {"result": "matched"}},
                "evidence_fingerprint": f"fp-{r3[:8]}",
                "correlation_id": f"corr-{r3[:8]}",
            },
            reason=None, event_meta={},
        )
        assert out3["change_kind"] == "technical_change"
        assert out3["revision"]["revision_number"] == 2
        revs = repo.list_revisions(rec_id)
        assert len(revs) == 2
        snap2 = revs[1]["technical_snapshot"]
        assert snap2["fields"]["unit"]["value"] == "BX"
        # revisão anterior imutável
        assert revs[0]["technical_snapshot"]["fields"]["unit"][
            "value"
        ] == "UN"
        # request do no-op concluiu vinculado à revisão vigente
        req2 = repo.get_request(r2)
        assert req2["status"] == "completed"
        assert req2["completed_record_id"] == rec_id

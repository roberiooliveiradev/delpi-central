"""U12 W1 — previous null + ordenação server-side com whitelist."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from controllership_finance_app.application.entry_audit.errors import EntryAuditError
from controllership_finance_app.application.entry_audit.service import EntryAuditService
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from controllership_finance_app.infrastructure.entry_audit.memory_store import (
    MemoryEntryAuditStore,
)


class _Ports:
    def documents(self, **_kwargs):
        return []

    def documents_by_access_keys(self, **_kwargs):
        return []

    def items(self, **_kwargs):
        return []

    def fiscal_book(self, **_kwargs):
        return []

    def tes(self):
        return []

    def branches(self):
        return []

    def download_by_key(self, **_kwargs):
        return None

    def list_issued(self, **_kwargs):
        return []

    def find_open(self, **_kwargs):
        return None


def _service(store: MemoryEntryAuditStore) -> EntryAuditService:
    ports = _Ports()
    return EntryAuditService(store, ports, ports, ports, AuditConfig(), lookback_days=30)


def _add_analysis(
    store: MemoryEntryAuditStore,
    *,
    date_from: date,
    date_to: date,
    branches: list[str] | None = None,
    document_types: list[str] | None = None,
    status: str = "done",
) -> str:
    analysis_id = str(uuid4())
    run_id = str(uuid4())
    now = datetime.now(timezone.utc)
    store.analyses[analysis_id] = {
        "id": analysis_id,
        "status": status,
        "date_from": date_from,
        "date_to": date_to,
        "document_types": document_types or ["nfe", "cte"],
        "branches": branches or ["01", "02"],
        "requested_via": "user",
        "created_at": now,
        "finished_at": now,
    }
    for branch in branches or ["01", "02"]:
        rid = str(uuid4()) if branch != (branches or ["01", "02"])[0] else run_id
        store.runs[rid] = {
            "id": rid,
            "analysis_id": analysis_id,
            "branch_code": branch,
            "status": "done",
            "stage": "done",
            "error_message": "",
            "counts": {},
        }
    return analysis_id


def _add_occurrence(store: MemoryEntryAuditStore, analysis_id: str, **fields) -> None:
    run = next(r for r in store.runs.values() if r["analysis_id"] == analysis_id)
    store.occurrences.append(
        {
            "analysis_id": analysis_id,
            "run_id": run["id"],
            "stable_key": fields.get("stable_key") or str(uuid4()),
            "severity": fields.get("severity", "Média"),
            "theme": fields.get("theme", "valor"),
            "supplier_name": fields.get("supplier_name", "Fornecedor"),
            "tes": fields.get("tes", "001"),
            "document_type": "nfe",
            "document_number": fields.get("document_number", "1"),
            "series": "1",
            "branch": "01",
            "received_date": fields.get("received_date", "2026-11-12"),
            "difference": fields.get("difference", "10"),
            "title": "x",
            "field": "gross",
            "access_key": "",
        }
    )


def test_previous_null_when_no_prior_analysis():
    store = MemoryEntryAuditStore()
    current = _add_analysis(store, date_from=date(2026, 11, 1), date_to=date(2026, 11, 15))
    payload = _service(store).summary(current, {})
    assert payload["previous"] is None


def test_previous_null_when_span_differs():
    store = MemoryEntryAuditStore()
    # 15 dias atuais → anterior deveria ser 17/10–31/10 (15 dias), não out/01–31
    _add_analysis(store, date_from=date(2026, 10, 1), date_to=date(2026, 10, 31))
    current = _add_analysis(store, date_from=date(2026, 11, 1), date_to=date(2026, 11, 15))
    payload = _service(store).summary(current, {})
    assert payload["previous"] is None


def test_previous_null_when_branches_differ():
    store = MemoryEntryAuditStore()
    span_to = date(2026, 10, 31)
    span_from = date(2026, 10, 17)
    _add_analysis(
        store,
        date_from=span_from,
        date_to=span_to,
        branches=["01"],
        document_types=["nfe", "cte"],
    )
    current = _add_analysis(
        store,
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 15),
        branches=["01", "02"],
        document_types=["nfe", "cte"],
    )
    assert _service(store).summary(current, {})["previous"] is None


def test_previous_kpis_when_exact_match():
    store = MemoryEntryAuditStore()
    previous_id = _add_analysis(
        store,
        date_from=date(2026, 10, 17),
        date_to=date(2026, 10, 31),
        branches=["01", "02"],
        document_types=["nfe", "cte"],
    )
    for i in range(3):
        _add_occurrence(
            store,
            previous_id,
            stable_key=f"p-{i}",
            severity="Alta",
            document_number=str(i),
            received_date="2026-10-20",
        )
    current = _add_analysis(
        store,
        date_from=date(2026, 11, 1),
        date_to=date(2026, 11, 15),
        branches=["01", "02"],
        document_types=["nfe", "cte"],
    )
    payload = _service(store).summary(current, {})
    assert payload["previous"] is not None
    assert payload["previous"]["occurrences"] == 3
    assert payload["previous"]["high"] == 3


def test_occurrences_default_sort_severity_compatible():
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(store, date_from=date(2026, 11, 12), date_to=date(2026, 11, 12), branches=["01"])
    _add_occurrence(store, analysis_id, severity="Baixa", document_number="2", stable_key="b")
    _add_occurrence(store, analysis_id, severity="Alta", document_number="1", stable_key="a")
    page = _service(store).occurrences(analysis_id, {}, page=1, page_size=50)
    assert [row["severity"] for row in page["items"]] == ["Alta", "Baixa"]


def test_occurrences_sort_desc_and_invalid():
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(store, date_from=date(2026, 11, 12), date_to=date(2026, 11, 12), branches=["01"])
    _add_occurrence(store, analysis_id, supplier_name="AAA", document_number="1", stable_key="1")
    _add_occurrence(store, analysis_id, supplier_name="ZZZ", document_number="2", stable_key="2")
    page = _service(store).occurrences(
        analysis_id, {}, page=1, page_size=50, sort="supplier", order="desc"
    )
    assert [row["supplier_name"] for row in page["items"]] == ["ZZZ", "AAA"]
    with pytest.raises(EntryAuditError) as exc:
        _service(store).occurrences(analysis_id, {}, page=1, page_size=10, sort="not_a_column")
    assert exc.value.status_code == 422
    assert exc.value.code == "INVALID_SORT"


def test_list_analyses_sort_and_invalid():
    store = MemoryEntryAuditStore()
    older = _add_analysis(store, date_from=date(2026, 10, 1), date_to=date(2026, 10, 5))
    newer = _add_analysis(store, date_from=date(2026, 11, 1), date_to=date(2026, 11, 5))
    store.analyses[older]["created_at"] = datetime(2026, 10, 6, tzinfo=timezone.utc)
    store.analyses[newer]["created_at"] = datetime(2026, 11, 6, tzinfo=timezone.utc)
    service = _service(store)
    default = service.list_analyses(
        date_from=None, date_to=None, branch=None, status=None, page=1, page_size=20
    )
    assert default["items"][0]["id"] == newer
    asc = service.list_analyses(
        date_from=None,
        date_to=None,
        branch=None,
        status=None,
        page=1,
        page_size=20,
        sort="created_at",
        order="asc",
    )
    assert asc["items"][0]["id"] == older
    with pytest.raises(EntryAuditError) as exc:
        service.list_analyses(
            date_from=None,
            date_to=None,
            branch=None,
            status=None,
            page=1,
            page_size=20,
            sort="nope",
        )
    assert exc.value.status_code == 422


def test_documents_sort_whitelist():
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(store, date_from=date(2026, 11, 1), date_to=date(2026, 11, 2), branches=["01"])
    run = next(r for r in store.runs.values() if r["analysis_id"] == analysis_id)
    for number, day in (("10", "2026-11-02"), ("1", "2026-11-01")):
        store.documents.append(
            {
                "analysis_id": analysis_id,
                "run_id": run["id"],
                "branch": "01",
                "document_number": number,
                "series": "1",
                "received_date": day,
                "supplier_name": "F",
                "situation": "period",
                "gross_amount": number,
            }
        )
    page = _service(store).documents(
        analysis_id, {}, page=1, page_size=50, sort="document_number", order="asc"
    )
    assert [row["document_number"] for row in page["items"]] == ["1", "10"]
    with pytest.raises(EntryAuditError):
        _service(store).documents(analysis_id, {}, page=1, page_size=10, sort="hack")


def test_occurrences_sort_by_status_from_store():
    """R1: ordenar por status usa o mapa de status, não a linha bruta."""
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(
        store, date_from=date(2026, 11, 12), date_to=date(2026, 11, 12), branches=["01"]
    )
    _add_occurrence(store, analysis_id, document_number="1", stable_key="pending-key", severity="Alta")
    _add_occurrence(store, analysis_id, document_number="2", stable_key="resolved-key", severity="Alta")
    store.upsert_status(
        "resolved-key",
        status="resolved",
        kind="occurrence",
        user_id="u1",
        user_name="Tester",
    )
    service = _service(store)
    asc = service.occurrences(
        analysis_id, {}, page=1, page_size=50, sort="status", order="asc"
    )
    assert [row["status"] for row in asc["items"]] == ["pending", "resolved"]
    desc = service.occurrences(
        analysis_id, {}, page=1, page_size=50, sort="status", order="desc"
    )
    assert [row["status"] for row in desc["items"]] == ["resolved", "pending"]


def test_occurrences_sort_whitelist_includes_rule_and_field():
    """R2: colunas Regra/Campo da tela entram na lista branca."""
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(
        store, date_from=date(2026, 11, 12), date_to=date(2026, 11, 12), branches=["01"]
    )
    _add_occurrence(
        store,
        analysis_id,
        document_number="1",
        stable_key="a",
        title="Zebra",
        field="total",
    )
    _add_occurrence(
        store,
        analysis_id,
        document_number="2",
        stable_key="b",
        title="Alpha",
        field="cfop",
    )
    # patch titles into store rows
    for row in store.occurrences:
        if row["stable_key"] == "a":
            row["title"] = "Zebra"
            row["field"] = "total"
        if row["stable_key"] == "b":
            row["title"] = "Alpha"
            row["field"] = "cfop"
    service = _service(store)
    by_rule = service.occurrences(
        analysis_id, {}, page=1, page_size=50, sort="rule", order="asc"
    )
    assert [row["rule_name"] for row in by_rule["items"]] == ["Alpha", "Zebra"]
    by_field = service.occurrences(
        analysis_id, {}, page=1, page_size=50, sort="field", order="asc"
    )
    assert [row["field"] for row in by_field["items"]] == ["cfop", "total"]
    with pytest.raises(EntryAuditError) as exc:
        service.occurrences(analysis_id, {}, page=1, page_size=10, sort="hack")
    assert exc.value.status_code == 422

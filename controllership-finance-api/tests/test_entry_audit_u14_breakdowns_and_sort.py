"""U14 F2 — AC-BFF-1..3: sort branches/document_types, TES label, breakdowns sem próprio filtro."""

from __future__ import annotations

from datetime import date, datetime, timezone
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
    branches: list[str] | None = None,
    document_types: list[str] | None = None,
) -> str:
    analysis_id = str(uuid4())
    now = datetime.now(timezone.utc)
    store.analyses[analysis_id] = {
        "id": analysis_id,
        "status": "done",
        "date_from": date(2026, 11, 7),
        "date_to": date(2026, 11, 13),
        "document_types": document_types or ["nfe", "cte"],
        "branches": branches or ["01", "02"],
        "requested_via": "user",
        "created_at": now,
        "finished_at": now,
    }
    for branch in branches or ["01", "02"]:
        rid = str(uuid4())
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
            "difference": "10",
            "title": "x",
            "field": "gross",
            "access_key": "",
        }
    )


def test_list_analyses_sort_by_branches_and_document_types():
    store = MemoryEntryAuditStore()
    a01 = _add_analysis(store, branches=["01"], document_types=["nfe"])
    a02 = _add_analysis(store, branches=["02"], document_types=["cte"])
    service = _service(store)
    by_branch = service.list_analyses(
        date_from=None,
        date_to=None,
        branch=None,
        status=None,
        page=1,
        page_size=20,
        sort="branches",
        order="asc",
    )
    assert [row["id"] for row in by_branch["items"]] == [a01, a02]
    by_types = service.list_analyses(
        date_from=None,
        date_to=None,
        branch=None,
        status=None,
        page=1,
        page_size=20,
        sort="document_types",
        order="asc",
    )
    assert [row["id"] for row in by_types["items"]] == [a02, a01]
    with pytest.raises(EntryAuditError) as exc:
        service.list_analyses(
            date_from=None,
            date_to=None,
            branch=None,
            status=None,
            page=1,
            page_size=20,
            sort="hack",
        )
    assert exc.value.status_code == 422


def test_breakdowns_exclude_own_dimension_filter():
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(store, branches=["01"])
    _add_occurrence(store, analysis_id, severity="Alta", theme="itens", supplier_name="A", tes="148")
    _add_occurrence(store, analysis_id, severity="Baixa", theme="cabecalho", supplier_name="B", tes="031")
    payload = _service(store).breakdowns(analysis_id, {"severity": "Alta"})
    # Com severity=Alta, a rosca ainda mostra Alta e Baixa (sem o próprio filtro).
    names = {row["name"] for row in payload["by_severity"]}
    assert names == {"Alta", "Baixa"}
    # Tema/fornecedor/TES seguem filtrados por severity=Alta.
    assert {row["name"] for row in payload["by_theme"]} == {"itens"}
    assert {row["name"] for row in payload["suppliers"]} == {"A"}
    assert {row["name"] for row in payload["tes"]} == {"148"}


def test_daily_excludes_own_day_filter():
    """U15 P2: com day= selecionado, a série ainda tem todos os dias > 0 pertinentes."""
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(store, branches=["01"])
    _add_occurrence(store, analysis_id, received_date="2026-11-10", severity="Alta")
    _add_occurrence(store, analysis_id, received_date="2026-11-11", severity="Baixa")
    _add_occurrence(store, analysis_id, received_date="2026-11-12", severity="Alta")
    service = _service(store)
    with_day = service.daily(analysis_id, {"day": "2026-11-10"})
    without = service.daily(analysis_id, {})
    by_day_filtered = {row["name"]: row["count"] for row in with_day["series"]}
    by_day_full = {row["name"]: row["count"] for row in without["series"]}
    assert by_day_filtered == by_day_full
    assert by_day_filtered.get("2026-11-10", 0) >= 1
    assert by_day_filtered.get("2026-11-11", 0) >= 1
    assert sum(1 for c in by_day_filtered.values() if c > 0) == sum(
        1 for c in by_day_full.values() if c > 0
    )


def test_breakdowns_tes_includes_sf4_label_without_protheus():
    store = MemoryEntryAuditStore()
    analysis_id = _add_analysis(store, branches=["01"])
    run = next(r for r in store.runs.values() if r["analysis_id"] == analysis_id)
    _add_occurrence(store, analysis_id, tes="148", severity="Alta")
    store.tes_used.append(
        {
            "analysis_id": analysis_id,
            "run_id": run["id"],
            "branch": "01",
            "tes_code": "148",
            "document_type": "nfe",
            "sf4": {"description": "Compra para industrialização", "items": 1},
        }
    )
    payload = _service(store).breakdowns(analysis_id, {})
    tes_row = next(row for row in payload["tes"] if row["name"] == "148")
    assert tes_row["label"] == "Compra para industrialização"

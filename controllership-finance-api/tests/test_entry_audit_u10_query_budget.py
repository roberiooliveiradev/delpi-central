"""U10 — consultas de summary/breakdowns/occurrences não crescem com N linhas."""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from controllership_finance_app.application.entry_audit.service import EntryAuditService
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from controllership_finance_app.infrastructure.entry_audit.memory_store import (
    MemoryEntryAuditStore,
)


class CountingStore:
    """Proxy que conta leituras — prova anti-N+1 sem Postgres."""

    def __init__(self, inner: MemoryEntryAuditStore) -> None:
        self.inner = inner
        self.calls: dict[str, int] = {
            "rows": 0,
            "runs_of": 0,
            "status_of": 0,
            "statuses_of": 0,
            "get_analysis": 0,
            "list_analyses": 0,
        }

    def __getattr__(self, name: str):
        return getattr(self.inner, name)

    def rows(self, kind: str, analysis_id: str):
        self.calls["rows"] += 1
        return self.inner.rows(kind, analysis_id)

    def runs_of(self, analysis_id: str):
        self.calls["runs_of"] += 1
        return self.inner.runs_of(analysis_id)

    def status_of(self, stable_key: str):
        self.calls["status_of"] += 1
        return self.inner.status_of(stable_key)

    def statuses_of(self, stable_keys: list[str]):
        self.calls["statuses_of"] += 1
        return self.inner.statuses_of(stable_keys)

    def get_analysis(self, analysis_id: str):
        self.calls["get_analysis"] += 1
        return self.inner.get_analysis(analysis_id)

    def list_analyses(self, **kwargs):
        self.calls["list_analyses"] += 1
        return self.inner.list_analyses(**kwargs)


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


def _seed(store: MemoryEntryAuditStore, *, n_occurrences: int) -> str:
    analysis_id = str(uuid4())
    run_id = str(uuid4())
    day = date(2026, 11, 12)
    now = datetime.now(timezone.utc)
    store.analyses[analysis_id] = {
        "id": analysis_id,
        "status": "done",
        "date_from": day,
        "date_to": day,
        "document_types": ["nfe"],
        "branches": ["01"],
        "created_at": now,
        "finished_at": now,
    }
    store.runs[run_id] = {
        "id": run_id,
        "analysis_id": analysis_id,
        "branch_code": "01",
        "status": "done",
        "stage": "done",
        "error_message": "",
    }
    for index in range(n_occurrences):
        key = f"occ-{n_occurrences}-{index}"
        store.occurrences.append(
            {
                "analysis_id": analysis_id,
                "run_id": run_id,
                "stable_key": key,
                "severity": "Alta" if index % 5 == 0 else "Média",
                "theme": "valor",
                "supplier_name": f"Fornecedor {index % 3}",
                "tes": "001",
                "document_type": "nfe",
                "document_number": str(1000 + index),
                "series": "1",
                "branch": "01",
                "received_date": "2026-11-12",
                "difference": "1.00",
                "title": f"Ocorrência {index}",
                "field": "gross",
                "access_key": "",
            }
        )
        if index % 4 == 0:
            store.statuses[key] = {
                "stable_key": key,
                "kind": "occurrence",
                "status": "resolved",
                "id": str(uuid4()),
            }
    store.documents.append(
        {
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": "01",
            "situation": "period",
            "document_type": "nfe",
            "document_number": "1",
            "series": "1",
            "supplier_name": "Fornecedor",
            "access_key": "",
            "gross_amount": 100,
            "comparison": {"gross": 100},
            "received_date": "2026-11-12",
            "issue_date": "2026-11-12",
        }
    )
    return analysis_id


def _service(store: CountingStore) -> EntryAuditService:
    ports = _Ports()
    return EntryAuditService(
        store, ports, ports, ports, AuditConfig(), lookback_days=30
    )


def test_summary_query_budget_does_not_grow_with_occurrence_count():
    budgets = []
    for n in (20, 80, 160):
        inner = MemoryEntryAuditStore()
        analysis_id = _seed(inner, n_occurrences=n)
        store = CountingStore(inner)
        service = _service(store)
        payload = service.summary(analysis_id, {})
        assert payload["kpis"]["occurrences"] == n
        assert store.calls["status_of"] == 0
        budgets.append(dict(store.calls))

    # statuses_of: no máximo 2 (atual + previous vazio ou com mapa) — constante.
    for calls in budgets:
        assert calls["statuses_of"] <= 2
        assert calls["status_of"] == 0
    # rows/runs não crescem com N (memo + lote).
    assert budgets[0]["rows"] == budgets[1]["rows"] == budgets[2]["rows"]
    assert budgets[0]["runs_of"] == budgets[1]["runs_of"] == budgets[2]["runs_of"]


def test_breakdowns_and_occurrences_avoid_per_row_status():
    inner = MemoryEntryAuditStore()
    analysis_id = _seed(inner, n_occurrences=100)
    store = CountingStore(inner)
    service = _service(store)

    breakdowns = service.breakdowns(analysis_id, {})
    assert breakdowns["by_severity"]
    assert store.calls["status_of"] == 0

    store.calls["status_of"] = 0
    store.calls["statuses_of"] = 0
    page = service.occurrences(
        analysis_id, {}, page=1, page_size=50, sort="severity"
    )
    assert len(page["items"]) == 50
    assert store.calls["status_of"] == 0
    assert store.calls["statuses_of"] == 1


def test_status_filter_uses_batch_map():
    inner = MemoryEntryAuditStore()
    analysis_id = _seed(inner, n_occurrences=40)
    store = CountingStore(inner)
    service = _service(store)
    rows = service.occurrences(
        analysis_id, {"status": "resolved"}, page=1, page_size=100, sort="severity"
    )
    assert rows["total"] > 0
    assert store.calls["status_of"] == 0
    assert store.calls["statuses_of"] >= 1


def test_previous_kpis_also_batch_status():
    inner = MemoryEntryAuditStore()
    current_id = _seed(inner, n_occurrences=30)
    # Análise anterior com o mesmo tamanho de janela (1 dia).
    previous_day = date(2026, 11, 11)
    previous_id = str(uuid4())
    run_id = str(uuid4())
    now = datetime.now(timezone.utc)
    inner.analyses[previous_id] = {
        "id": previous_id,
        "status": "done",
        "date_from": previous_day,
        "date_to": previous_day,
        "document_types": ["nfe"],
        "branches": ["01"],
        "created_at": now,
        "finished_at": now,
    }
    inner.runs[run_id] = {
        "id": run_id,
        "analysis_id": previous_id,
        "branch_code": "01",
        "status": "done",
        "stage": "done",
        "error_message": "",
    }
    for index in range(10):
        key = f"prev-{index}"
        inner.occurrences.append(
            {
                "analysis_id": previous_id,
                "run_id": run_id,
                "stable_key": key,
                "severity": "Alta",
                "theme": "valor",
                "supplier_name": "F",
                "tes": "001",
                "document_type": "nfe",
                "document_number": str(index),
                "series": "1",
                "branch": "01",
                "received_date": "2026-11-11",
                "difference": "1",
                "title": "x",
                "field": "gross",
                "access_key": "",
            }
        )
    store = CountingStore(inner)
    service = _service(store)
    payload = service.summary(current_id, {})
    assert payload["previous"]["occurrences"] == 10
    assert store.calls["status_of"] == 0
    assert store.calls["statuses_of"] <= 2

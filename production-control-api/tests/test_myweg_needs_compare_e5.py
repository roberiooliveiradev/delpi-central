"""E5 — serviço/rota de comparação (sem Protheus)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.application.services.myweg_needs_compare_service import (
    MyWegNeedsCompareService,
)
from production_control_app.application.services.myweg_needs_service import MyWegNeedsService
from production_control_app.core.security import (
    PC_ACCESS,
    PC_MYWEG_NEEDS_VIEW,
    PC_VIEW_FILIAL_01,
    PC_VIEW_FILIAL_02,
)
from production_control_app.domain.errors import DelpiGatewayError, MyWegNeedsValidationFailed
from production_control_app.interface.http.routes import myweg_needs_routes
from tests.test_myweg_needs_e2 import InMemoryMyWegNeedsRepository, _build_payload
from tests.test_myweg_sb1_resolve_e4 import _mini_records


class CompareRepo(InMemoryMyWegNeedsRepository):
    def list_batch_records_for_compare(self, *, batch_id: str) -> list[dict]:
        rows = list(self.records.get(batch_id, []))
        out = []
        for row in rows:
            item = dict(row)
            if "sb1_resolution" not in item:
                item["sb1_resolution"] = {
                    "status": "confirmed",
                    "protheus_product_code": (row.get("codigo_referencia_weg") or "P-FALLBACK"),
                }
            out.append(item)
        return out


def _seed_two_batches(repo: CompareRepo) -> tuple[dict, dict]:
    service = MyWegNeedsService(repo)
    first = service.ingest_batch(
        _build_payload(_mini_records(3), collection_id="col-e5-a"),
        idempotency_key=None,
        caller_app="test",
    )
    # segunda coleta com quantidade diferente
    records = _mini_records(3)
    records[0]["quantidade"] = "500"
    second = service.ingest_batch(
        _build_payload(records, collection_id="col-e5-b"),
        idempotency_key=None,
        caller_app="test",
    )
    # ajustar collected_at/collection_date para dias distintos no fake
    with repo._lock:
        repo.batches[first["id"]]["collected_at"] = "2026-11-03T08:00:00-03:00"
        repo.batches[first["id"]]["collection_date"] = "2026-11-03"
        repo.batches[second["id"]]["collected_at"] = "2026-11-04T08:00:00-03:00"
        repo.batches[second["id"]]["collection_date"] = "2026-11-04"
    return first, second


def test_compare_detects_quantity_change() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    user = SimpleNamespace(
        permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
        is_superadmin=False,
    )
    result = MyWegNeedsCompareService(repo, gateway=object()).compare(
        user,
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="none",
    )
    assert result["observed"]["summary"]["increased"] + result["observed"]["summary"][
        "decreased"
    ] + result["observed"]["summary"]["appeared"] + result["observed"]["summary"][
        "disappeared"
    ] >= 1
    assert result["billing"]["status"] == "skipped"


def test_compare_billing_failure_keeps_observed() -> None:
    class FailGateway:
        def list_customer_outbound_invoice_line_items(self, **kwargs):
            raise DelpiGatewayError("down", status_code=503)

    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    user = SimpleNamespace(
        permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
        is_superadmin=False,
    )
    result = MyWegNeedsCompareService(repo, gateway=FailGateway()).compare(
        user,
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="indicative",
    )
    assert result["observed"]["summary"] is not None
    assert result["billing"]["status"] == "unavailable"
    assert "zero" in result["billing"]["disclaimer"].lower() or "zero" in (
        result["billing"].get("disclaimer") or ""
    ).lower()


def test_compare_insufficient_batches() -> None:
    repo = CompareRepo()
    service = MyWegNeedsService(repo)
    service.ingest_batch(
        _build_payload(_mini_records(2), collection_id="col-e5-only"),
        idempotency_key=None,
    )
    user = SimpleNamespace(
        permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
        is_superadmin=False,
    )
    with pytest.raises(MyWegNeedsValidationFailed) as exc:
        MyWegNeedsCompareService(repo).compare(
            user, from_batch_id=None, to_batch_id=None, billing_mode="none"
        )
    assert any(i.get("code") == "insufficient_batches" for i in exc.value.issues)


def test_compare_route_permission_negative(monkeypatch) -> None:
    repo = CompareRepo()
    _seed_two_batches(repo)
    service = MyWegNeedsCompareService(repo)

    app = FastAPI()
    app.include_router(myweg_needs_routes.router)
    monkeypatch.setattr(
        myweg_needs_routes, "build_myweg_needs_compare_service", lambda: service
    )
    monkeypatch.setattr(
        myweg_needs_routes,
        "resolve_user",
        lambda request: SimpleNamespace(
            permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_01},
            is_superadmin=False,
        ),
    )
    client = TestClient(app)
    response = client.get("/myweg/need-batches/compare")
    assert response.status_code == 403

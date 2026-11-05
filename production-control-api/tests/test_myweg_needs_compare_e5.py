"""E5 — serviço/rota de comparação (sem Protheus) + rework janela/cronologia."""

from __future__ import annotations

from datetime import date
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
            code = (row.get("codigo_referencia_weg") or "").strip() or "P-FALLBACK"
            # Ingest E4 grava pending; nos testes de compare forçamos vínculo confirmado.
            item["sb1_resolution"] = {
                "status": "confirmed",
                "protheus_product_code": code,
            }
            out.append(item)
        return out


def _user():
    return SimpleNamespace(
        permissions={PC_ACCESS, PC_MYWEG_NEEDS_VIEW, PC_VIEW_FILIAL_02},
        is_superadmin=False,
    )


def _seed_two_batches(repo: CompareRepo) -> tuple[dict, dict]:
    service = MyWegNeedsService(repo)
    first = service.ingest_batch(
        _build_payload(_mini_records(3), collection_id="col-e5-a"),
        idempotency_key=None,
        caller_app="test",
    )
    records = _mini_records(3)
    records[0]["quantidade"] = "500"
    second = service.ingest_batch(
        _build_payload(records, collection_id="col-e5-b"),
        idempotency_key=None,
        caller_app="test",
    )
    with repo._lock:
        repo.batches[first["id"]]["collected_at"] = "2026-11-03T08:00:00-03:00"
        repo.batches[first["id"]]["collection_date"] = "2026-11-03"
        repo.batches[second["id"]]["collected_at"] = "2026-11-04T08:00:00-03:00"
        repo.batches[second["id"]]["collection_date"] = "2026-11-04"
    return first, second


def test_compare_detects_quantity_change() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    result = MyWegNeedsCompareService(repo, gateway=object()).compare(
        _user(),
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
    assert "totalChanges" in result
    assert "totalCompared" in result


def test_compare_billing_failure_keeps_observed() -> None:
    class FailGateway:
        called = False

        def list_customer_outbound_invoice_line_items(self, **kwargs):
            FailGateway.called = True
            raise DelpiGatewayError("down", status_code=503)

    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    result = MyWegNeedsCompareService(repo, gateway=FailGateway()).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="indicative",
    )
    assert FailGateway.called is True
    assert result["observed"]["summary"] is not None
    assert result["billing"]["status"] == "unavailable"
    assert result["billing"]["reason"] == "api_delpi_error"
    assert result["billing"]["totalsByProduct"] == []
    assert "zero" in (result["billing"].get("disclaimer") or "").lower()
    assert result["billing"]["period"]["start"] == "2026-11-03"
    assert result["billing"]["period"]["end"] == "2026-11-03"


def test_ac01_fiscal_window_tied_to_pair_not_45_days() -> None:
    class CaptureGateway:
        last: dict = {}

        def list_customer_outbound_invoice_line_items(self, **kwargs):
            CaptureGateway.last = kwargs
            return {
                "data": {
                    "totals_by_product": [],
                    "returned_item_count": 0,
                    "coverage": {},
                }
            }

    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    MyWegNeedsCompareService(repo, gateway=CaptureGateway()).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="indicative",
    )
    assert CaptureGateway.last["issue_date_start"] == "2026-11-03"
    assert CaptureGateway.last["issue_date_end"] == "2026-11-03"
    delta = (
        date.fromisoformat(CaptureGateway.last["issue_date_end"])
        - date.fromisoformat(CaptureGateway.last["issue_date_start"])
    ).days
    assert delta < 45


def test_ac02_historical_window_independent_of_today() -> None:
    window = MyWegNeedsCompareService.resolve_fiscal_window(
        {"collection_date": "2025-01-10", "collected_at": "2025-01-10T08:00:00-03:00"},
        {"collection_date": "2025-01-12", "collected_at": "2025-01-12T08:00:00-03:00"},
    )
    assert window["start"] == "2025-01-10"
    assert window["end"] == "2025-01-11"
    assert "today" not in window["criterion"]


def test_compare_insufficient_batches() -> None:
    repo = CompareRepo()
    service = MyWegNeedsService(repo)
    service.ingest_batch(
        _build_payload(_mini_records(2), collection_id="col-e5-only"),
        idempotency_key=None,
    )
    with pytest.raises(MyWegNeedsValidationFailed) as exc:
        MyWegNeedsCompareService(repo).compare(
            _user(), from_batch_id=None, to_batch_id=None, billing_mode="none"
        )
    assert any(i.get("code") == "insufficient_batches" for i in exc.value.issues)


def test_ac08_inverted_chronology_rejected() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    with pytest.raises(MyWegNeedsValidationFailed) as exc:
        MyWegNeedsCompareService(repo).compare(
            _user(),
            from_batch_id=second["id"],
            to_batch_id=first["id"],
            billing_mode="none",
        )
    assert any(i.get("code") == "chronological_order_invalid" for i in exc.value.issues)


def test_ac08_same_batch_rejected() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    with pytest.raises(MyWegNeedsValidationFailed) as exc:
        MyWegNeedsCompareService(repo).compare(
            _user(),
            from_batch_id=first["id"],
            to_batch_id=first["id"],
            billing_mode="none",
        )
    assert any(i.get("code") == "same_batch" for i in exc.value.issues)


def test_ac09_auto_requires_distinct_operational_days() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    with repo._lock:
        # duas coletas no mesmo dia operacional
        repo.batches[first["id"]]["collection_date"] = "2026-11-04"
        repo.batches[first["id"]]["collected_at"] = "2026-11-04T07:00:00-03:00"
        repo.batches[second["id"]]["collection_date"] = "2026-11-04"
        repo.batches[second["id"]]["collected_at"] = "2026-11-04T09:00:00-03:00"
    with pytest.raises(MyWegNeedsValidationFailed) as exc:
        MyWegNeedsCompareService(repo).compare(
            _user(), from_batch_id=None, to_batch_id=None, billing_mode="none"
        )
    assert any(i.get("code") == "insufficient_operational_days" for i in exc.value.issues)

    # Manual same-day ainda permitido se ordem temporal válida
    result = MyWegNeedsCompareService(repo).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="none",
    )
    assert result["fromBatch"]["id"] == first["id"]


def test_ac09_auto_picks_distinct_days() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    result = MyWegNeedsCompareService(repo).compare(
        _user(), from_batch_id=None, to_batch_id=None, billing_mode="none"
    )
    assert result["toBatch"]["id"] == second["id"]
    assert result["fromBatch"]["id"] == first["id"]


def test_changes_only_pagination_and_search() -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    full = MyWegNeedsCompareService(repo).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="none",
        changes_only=False,
        page=1,
        page_size=1,
    )
    assert full["totalCompared"] >= full["totalChanges"]
    assert full["pageSize"] == 1
    assert len(full["items"]) == 1

    only = MyWegNeedsCompareService(repo).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="none",
        changes_only=True,
        page=1,
        page_size=50,
    )
    assert only["total"] == only["totalChanges"]
    assert all(row["movement"] != "unchanged" for row in only["items"])


def test_indicative_billing_builds_fifo_products() -> None:
    class OkGateway:
        def list_customer_outbound_invoice_line_items(self, **kwargs):
            codes = list(kwargs.get("product_codes") or [])
            return {
                "data": {
                    "totals_by_product": [
                        {
                            "product_code": codes[0],
                            "quantity": "10",
                            "unit": "UN",
                            "quantity_un": "10",
                            "normalized_unit": "UN",
                            "conversion_factor": "1",
                            "comparable": True,
                        }
                    ],
                    "returned_item_count": 1,
                    "coverage": {},
                }
            }

    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    result = MyWegNeedsCompareService(repo, gateway=OkGateway()).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="indicative",
    )
    assert result["billing"]["status"] in {"indicative", "partial"}
    assert result["billing"]["indicativeProducts"]
    assert result["billing"]["fifoScenarios"]
    assert Decimal(result["billing"]["indicativeProducts"][0]["candidateQuantityUn"]) == Decimal(
        "10"
    )


def test_ac04_mi_quantity_un_consumed_without_double_conversion() -> None:
    """AC-04/AC-05: PC usa quantity_un; 2.5 MI → 2500 UN, sem *1000 de novo."""

    class MiGateway:
        def list_customer_outbound_invoice_line_items(self, **kwargs):
            codes = list(kwargs.get("product_codes") or [])
            return {
                "data": {
                    "totals_by_product": [
                        {
                            "product_code": codes[0],
                            "quantity": "2.5",
                            "unit": "MI",
                            "original_units": ["MI"],
                            "quantity_un": "2500",
                            "normalized_unit": "UN",
                            "conversion_factor": "1000",
                            "comparable": True,
                        }
                    ],
                    "returned_item_count": 1,
                    "coverage": {},
                }
            }

    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    result = MyWegNeedsCompareService(repo, gateway=MiGateway()).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="indicative",
    )
    assert result["billing"]["status"] in {"indicative", "partial"}
    product = result["billing"]["indicativeProducts"][0]
    assert Decimal(product["candidateQuantityUn"]) == Decimal("2500")
    assert product["originalQuantity"] == "2.5"
    assert product["originalUnit"] == "MI"
    assert product["conversionFactor"] == "1000"
    # Sem conversão dupla: não 2_500_000
    assert Decimal(product["candidateQuantityUn"]) != Decimal("2500000")
    assert result["billing"]["fifoScenarios"]
    assert Decimal(result["billing"]["fifoScenarios"][0]["candidateQuantityUn"]) == Decimal(
        "2500"
    )


def test_incompatible_unit_excluded_from_fifo() -> None:
    class MixedGateway:
        def list_customer_outbound_invoice_line_items(self, **kwargs):
            codes = list(kwargs.get("product_codes") or [])
            return {
                "data": {
                    "totals_by_product": [
                        {
                            "product_code": codes[0],
                            "quantity": "10",
                            "unit": "KG",
                            "quantity_un": None,
                            "comparable": False,
                            "incompatibility_reason": "KG vs UN",
                        }
                    ],
                    "returned_item_count": 1,
                    "coverage": {},
                }
            }

    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    result = MyWegNeedsCompareService(repo, gateway=MixedGateway()).compare(
        _user(),
        from_batch_id=first["id"],
        to_batch_id=second["id"],
        billing_mode="indicative",
    )
    assert result["billing"]["status"] == "incompatible_units"
    assert result["billing"]["totalsByProduct"] == []
    assert result["billing"]["incompatibleProducts"]
    assert result["billing"]["fifoScenarios"] == []


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


def test_compare_route_chronology_422(monkeypatch) -> None:
    repo = CompareRepo()
    first, second = _seed_two_batches(repo)
    service = MyWegNeedsCompareService(repo)
    app = FastAPI()
    app.include_router(myweg_needs_routes.router)
    monkeypatch.setattr(
        myweg_needs_routes, "build_myweg_needs_compare_service", lambda: service
    )
    monkeypatch.setattr(
        myweg_needs_routes,
        "resolve_user",
        lambda request: _user(),
    )
    client = TestClient(app)
    response = client.get(
        "/myweg/need-batches/compare",
        params={"fromBatchId": second["id"], "toBatchId": first["id"]},
    )
    assert response.status_code == 422

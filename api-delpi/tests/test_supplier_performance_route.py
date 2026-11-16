from unittest.mock import Mock

from app.interface.http.routes.supplies import supplier_performance_router as routes


def test_untrusted_caller_denied_even_for_authenticated_superadmin(monkeypatch):
    monkeypatch.setattr(routes, "is_trusted_supplies_bff_call", lambda: False)
    composer = Mock()
    monkeypatch.setattr(routes, "build_supplier_performance_use_case", composer)
    response = routes.get_supplies_supplier_performance(
        branch=["01"], date_from="2026-11-01", date_to="2026-11-16"
    )
    assert response.status_code == 403
    composer.assert_not_called()


def test_trusted_bff_validates_and_envelopes_payload(monkeypatch):
    from app.domain.services.supplies.supplier_performance import (
        compose_supplier_performance,
    )

    monkeypatch.setattr(routes, "is_trusted_supplies_bff_call", lambda: True)
    payload = compose_supplier_performance([])
    payload.update(
        period={"from": "2026-11-01", "to": "2026-11-16"},
        branches=["01"],
        calculated_at="2026-11-16T08:00:00-03:00",
    )
    case = Mock()
    case.execute.return_value = payload
    monkeypatch.setattr(routes, "build_supplier_performance_use_case", lambda: case)
    response = routes.get_supplies_supplier_performance(
        branch=["01"], date_from="2026-11-01", date_to="2026-11-16"
    )
    assert response.status_code == 200
    assert b"supplies_supplier_performance" in response.body
    case.execute.assert_called_once_with(
        branches=["01"], date_from="2026-11-01", date_to="2026-11-16"
    )


def test_real_http_wiring_schema_and_meta(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.domain.services.supplies.supplier_performance import (
        compose_supplier_performance,
    )

    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes, "is_trusted_supplies_bff_call", lambda: True)
    payload = compose_supplier_performance([])
    payload.update(
        period={"from": "2026-11-01", "to": "2026-11-16"},
        branches=["01", "02"],
        calculated_at="2026-11-16T08:00:00-03:00",
    )
    case = Mock()
    case.execute.return_value = payload
    monkeypatch.setattr(routes, "build_supplier_performance_use_case", lambda: case)
    with TestClient(app) as client:
        response = client.get(
            "/supplies/supplier-performance?branch=01&branch=02&date_from=2026-11-01&date_to=2026-11-16"
        )
        assert response.status_code == 200
        assert (
            response.json()["meta"]["operationId"]
            == "get_supplies_supplier_performance"
        )
        assert response.json()["data"]["summary"]["average_idf"] is None
        assert (
            client.get(
                "/supplies/supplier-performance?date_from=2026-11-01&date_to=2026-11-16"
            ).status_code
            == 422
        )
        operation = client.get("/openapi.json").json()["paths"][
            "/supplies/supplier-performance"
        ]["get"]
        assert operation["operationId"] == "get_supplies_supplier_performance"
        assert operation["responses"]["200"]["content"]["application/json"]["schema"][
            "$ref"
        ].endswith("SupplierPerformanceResponse")


def test_evidence_export_remains_private_to_trusted_supplies_bff(monkeypatch):
    monkeypatch.setattr(routes, "is_trusted_supplies_bff_call", lambda: False)
    builder = Mock()
    monkeypatch.setattr(routes, "build_supplier_performance_export_use_case", builder)
    response = routes.export_supplies_supplier_performance_evidence(
        branch=["01"], date_from="2026-11-01", date_to="2026-11-16",
        supplier_code="000001", supplier_store="01",
    )
    assert response.status_code == 403
    builder.assert_not_called()


def test_evidence_export_has_stable_operation_id_and_selects_supplier(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.domain.services.supplies.supplier_performance import (
        compose_supplier_performance,
    )

    app = FastAPI()
    app.include_router(routes.router)
    monkeypatch.setattr(routes, "is_trusted_supplies_bff_call", lambda: True)
    payload = compose_supplier_performance([])
    payload.update(
        period={"from": "2026-11-01", "to": "2026-11-16"},
        branches=["01"], calculated_at="2026-11-16T08:00:00-03:00",
        inspections=[], deliveries=[], supplier_selected={"code": "000001", "store": "01"}
    )
    case = Mock()
    case.execute.return_value = payload
    monkeypatch.setattr(routes, "build_supplier_performance_export_use_case", lambda: case)
    with TestClient(app) as client:
        response = client.get(
            "/supplies/supplier-performance/evidence-export"
            "?branch=01&date_from=2026-11-01&date_to=2026-11-16"
            "&supplier_code=000001&supplier_store=01"
        )
        assert response.status_code == 200
        assert response.json()["data"]["inspections"] == []
        assert response.json()["data"]["supplier_selected"]["code"] == "000001"
        assert response.json()["meta"]["operationId"] == "export_supplies_supplier_performance_evidence"
        operation = client.get("/openapi.json").json()["paths"][
            "/supplies/supplier-performance/evidence-export"
        ]["get"]
        assert operation["operationId"] == "export_supplies_supplier_performance_evidence"
    case.execute.assert_called_once_with(
        branches=["01"], date_from="2026-11-01", date_to="2026-11-16",
        supplier_code="000001", supplier_store="01",
    )

"""O2 — POST /machine-load/optimize: contrato HTTP do endpoint genérico."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from production_control_app.interface.http.routes import machine_load_routes as routes
from tests.test_machine_load import (
    FULL_PERMS,
    FakeGateway,
    FakeSnapshotRepo,
    _service,
    _user,
)
from tests.test_machine_load_publication import _op, _queue_payload
from datetime import date
import uuid


def _app() -> tuple[TestClient, FakeSnapshotRepo]:
    snapshots = FakeSnapshotRepo()
    snapshots.upsert(
        branch="01",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        payload=_queue_payload(
            [
                _op("A", "01", due_date="2026-10-08", tool="MA-01"),
                _op("B", "02", due_date="2026-10-07", tool="MA-02"),
                _op("C", "03", due_date="2026-10-08", tool="MA-02"),
            ]
        ),
        refreshed_by="seed",
        generation_id=str(uuid.uuid4()),
    )
    service = _service(FakeGateway(), snapshots)

    app = FastAPI()

    @app.middleware("http")
    async def _inject_user(request: Request, call_next):
        request.state.user = _user(*FULL_PERMS)
        return await call_next(request)

    app.include_router(routes.router)
    routes.build_machine_load_service = lambda *a, **kw: service  # type: ignore[assignment]
    return TestClient(app), snapshots


def test_optimize_endpoint_data_only() -> None:
    api, _ = _app()

    resp = api.post(
        "/machine-load/optimize?branch=01",
        json={"criteria": {"group_by_tool": False}},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    criteria = body["data"]["optimization"]["criteria"]
    assert criteria == {"delivery_date": True, "group_by_tool": False}


def test_optimize_endpoint_data_and_tool() -> None:
    api, snapshots = _app()

    resp = api.post(
        "/machine-load/optimize?branch=01&includeAllCenters=true",
        json={"criteria": {"group_by_tool": True}},
    )

    assert resp.status_code == 200
    body = resp.json()
    criteria = body["data"]["optimization"]["criteria"]
    assert criteria == {"delivery_date": True, "group_by_tool": True}
    # 07/10 primeiro (B); 08/10 agrupa MA-01 (A) antes de MA-02 (C).
    ops = body["data"]["operations"]
    assert [i["production_order"] for i in ops] == ["B", "A", "C"]


def test_optimize_endpoint_without_body_defaults_to_data_only() -> None:
    api, _ = _app()

    resp = api.post("/machine-load/optimize?branch=01")

    assert resp.status_code == 200
    assert resp.json()["data"]["optimization"]["criteria"] == {
        "delivery_date": True,
        "group_by_tool": False,
    }


def test_legacy_optimize_delivery_endpoint_still_works() -> None:
    api, _ = _app()

    resp = api.post("/machine-load/optimize-delivery?branch=01")

    assert resp.status_code == 200
    assert resp.json()["data"]["optimization"]["criteria"] == {
        "delivery_date": True,
        "group_by_tool": False,
    }

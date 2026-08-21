from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from production_control_app.interface.http.routes.subplugin_routes import router as subplugin_router
from production_control_app.main import app as production_app


def _user(**kwargs):
    defaults = {
        "is_superadmin": False,
        "permissions": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_health_path_is_public_with_root_prefix() -> None:
    from production_control_app.middleware.auth_middleware import _is_public_health

    assert _is_public_health("/health") is True
    assert _is_public_health("/apps/production-control-api/health") is True
    assert _is_public_health("/apps/production-control-api/subplugins") is False


def test_health_is_public() -> None:
    client = TestClient(production_app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert body["service"] == "production-control-api"


def test_subplugins_catalog_filters_by_permission() -> None:
    from production_control_app.application.services.subplugin_catalog_service import (
        SubpluginCatalogService,
        load_subplugin_catalog,
    )

    catalog = load_subplugin_catalog()
    assert catalog[0].id == "home"
    assert any(item.id == "problem-analysis" for item in catalog)
    assert any(item.status == "coming_soon" for item in catalog)

    service = SubpluginCatalogService()
    with_access = service.list_visible(
        _user(
            permissions=[
                "production-control.access",
                "production-control.problem-analysis.view",
                "production-control.machine-load.view",
            ]
        )
    )
    ids = {item.id for item in with_access}
    assert "home" in ids
    assert "problem-analysis" in ids
    assert "machine-load" in ids

    only_access = service.list_visible(_user(permissions=["production-control.access"]))
    only_access_ids = {item.id for item in only_access}
    assert "problem-analysis" not in only_access_ids
    assert "machine-load" not in only_access_ids
    assert "demand" not in only_access_ids


def test_demand_subplugin_requires_its_own_permission() -> None:
    from production_control_app.application.services.subplugin_catalog_service import (
        SubpluginCatalogService,
    )

    service = SubpluginCatalogService()
    visible = service.list_visible(
        _user(
            permissions=[
                "production-control.access",
                "production-control.demand.view",
            ]
        )
    )
    ids = {item.id for item in visible}
    assert "demand" in ids
    assert "machine-load" not in ids


def test_subplugins_route_returns_envelope() -> None:
    test_app = FastAPI()

    @test_app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = _user(
            is_superadmin=True,
            permissions=["production-control.access"],
        )
        return await call_next(request)

    test_app.include_router(subplugin_router)
    client = TestClient(test_app)
    response = client.get("/subplugins")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert any(item["id"] == "problem-analysis" for item in payload["data"]["items"])

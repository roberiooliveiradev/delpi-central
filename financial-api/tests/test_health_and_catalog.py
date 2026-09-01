from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_app.interface.http.routes.subplugin_routes import router as subplugin_router
from financial_app.main import app as financial_app
from tests.conftest import full_user, user


def test_health_path_is_public_with_root_prefix() -> None:
    from financial_app.middleware.auth_middleware import _is_public_health

    assert _is_public_health("/health") is True
    assert _is_public_health("/apps/financial-api/health") is True
    assert _is_public_health("/apps/financial-api/subplugins") is False


def test_health_is_public() -> None:
    client = TestClient(financial_app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert body["service"] == "financial-api"


def test_catalog_filters_by_permission() -> None:
    from financial_app.application.services.subplugin_catalog_service import (
        SubpluginCatalogService,
        load_subplugin_catalog,
    )

    load_subplugin_catalog.cache_clear()
    catalog = load_subplugin_catalog()
    assert catalog[0].id == "home"
    assert {item.id for item in catalog} >= {"billing", "delinquency", "cost-centers", "indicators"}
    assert any(item.status == "coming_soon" for item in catalog)

    service = SubpluginCatalogService()
    visible_ids = {item.id for item in service.list_visible(full_user())}
    assert {"home", "billing", "delinquency", "cost-centers", "indicators"} <= visible_ids

    only_access_ids = {item.id for item in service.list_visible(user("financial.access"))}
    assert "home" in only_access_ids
    assert "billing" in only_access_ids
    assert "delinquency" not in only_access_ids
    assert "cost-centers" not in only_access_ids
    assert "indicators" not in only_access_ids


def test_catalog_requires_access_permission() -> None:
    from financial_app.application.services.subplugin_catalog_service import (
        SubpluginCatalogService,
    )

    with pytest.raises(PermissionError):
        SubpluginCatalogService().list_visible(user())


def test_subplugins_route_returns_envelope_with_export_capability() -> None:
    test_app = FastAPI()

    @test_app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = user("financial.access", "financial.export")
        return await call_next(request)

    test_app.include_router(subplugin_router)
    payload = TestClient(test_app).get("/subplugins").json()

    assert payload["success"] is True
    assert payload["data"]["capabilities"]["export"] is True
    assert any(item["id"] == "home" for item in payload["data"]["items"])


def test_subplugins_route_denies_without_access() -> None:
    test_app = FastAPI()

    @test_app.middleware("http")
    async def inject_user(request, call_next):
        request.state.user = user()
        return await call_next(request)

    test_app.include_router(subplugin_router)
    response = TestClient(test_app).get("/subplugins")

    assert response.status_code == 403
    assert response.json()["success"] is False

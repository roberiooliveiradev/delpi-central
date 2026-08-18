from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from si_app.interface.http.routes.strategic_indicators_routes import router
from si_app.interface.http.schemas.strategic_indicators_settings_schema import (
    ImportAdminConfigBodySchema,
)


MINIMAL_BODY = {
    "schema_version": 1,
    "departments": [],
    "department_indicators": [],
    "indicator_goals": [],
    "module_settings": {},
}


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_schema_default_mode_is_replace():
    parsed = ImportAdminConfigBodySchema.model_validate(MINIMAL_BODY)
    assert parsed.mode == "replace"


def test_schema_accepts_merge_and_replace():
    merge = ImportAdminConfigBodySchema.model_validate({**MINIMAL_BODY, "mode": "merge"})
    replace = ImportAdminConfigBodySchema.model_validate(
        {**MINIMAL_BODY, "mode": "replace"}
    )
    assert merge.mode == "merge"
    assert replace.mode == "replace"


def test_schema_rejects_invalid_mode():
    with pytest.raises(ValidationError):
        ImportAdminConfigBodySchema.model_validate({**MINIMAL_BODY, "mode": "foo"})


def test_admin_config_route_paths_exist():
    paths = _app().openapi()["paths"]
    assert "/strategic-indicators/admin/config/export" in paths
    assert "get" in paths["/strategic-indicators/admin/config/export"]
    assert "/strategic-indicators/admin/config/import/preview" in paths
    assert "post" in paths["/strategic-indicators/admin/config/import/preview"]
    assert "/strategic-indicators/admin/config/import/apply" in paths
    assert "post" in paths["/strategic-indicators/admin/config/import/apply"]
    assert "/strategic-indicators/admin/config/import" in paths
    assert "post" in paths["/strategic-indicators/admin/config/import"]


def test_preview_invalid_mode_returns_422():
    client = TestClient(_app())
    response = client.post(
        "/strategic-indicators/admin/config/import/preview",
        json={**MINIMAL_BODY, "mode": "foo"},
    )
    assert response.status_code == 422


def test_apply_invalid_mode_returns_422():
    client = TestClient(_app())
    response = client.post(
        "/strategic-indicators/admin/config/import/apply",
        json={**MINIMAL_BODY, "mode": "foo"},
    )
    assert response.status_code == 422

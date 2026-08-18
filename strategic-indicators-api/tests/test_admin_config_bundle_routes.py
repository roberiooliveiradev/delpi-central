from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from delpi_auth.middleware.fastapi_auth import map_authz_exception
from delpi_auth.request_context import reset_current_user, set_current_user
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

MANAGE_PERM = "strategic-indicators.settings.manage"

PREVIEW_OK = {
    "valid": True,
    "errors": [],
    "mode": "replace",
    "current_counts": {
        "departments": 7,
        "department_indicators": 42,
        "indicator_goals": 42,
    },
    "planned": {
        "departments": {
            "in_file": 0,
            "insert": 0,
            "update": 0,
            "skip": 0,
            "delete": 7,
        }
    },
}

APPLY_OK = {
    "message": "Configuração importada com sucesso.",
    "stats": {
        "mode": "replace",
        "departments_upserted": 7,
        "indicators_upserted": 42,
        "goals_created": 42,
        "goals_skipped": 0,
        "goals_deleted": 42,
        "departments_deleted": 7,
        "indicators_deleted": 42,
        "module_settings_updated": 2,
    },
}


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(Exception)
    async def _map_authz(_request, exc: Exception):
        mapped = map_authz_exception(exc)
        if mapped is not None:
            return mapped
        raise exc

    return app


def _as_user(*, permissions: list[str], superadmin: bool = False):
    return set_current_user(
        SimpleNamespace(
            id="user-1",
            is_superadmin=superadmin,
            permissions=permissions,
            rbac_unavailable=False,
        )
    )


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


def test_export_returns_envelope():
    token = _as_user(permissions=[MANAGE_PERM])
    export_uc = MagicMock()
    export_uc.execute.return_value = {
        **MINIMAL_BODY,
        "exported_at": "2026-08-18T14:00:00Z",
    }
    try:
        with patch(
            "si_app.interface.http.routes.strategic_indicators_routes.build_export_strategic_indicators_admin_config_use_case",
            return_value=export_uc,
        ):
            response = TestClient(_app()).get(
                "/strategic-indicators/admin/config/export"
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == 1
    assert "departments" in payload
    assert "department_indicators" in payload
    assert "indicator_goals" in payload
    assert "module_settings" in payload


def test_preview_returns_planned_without_invalidate():
    token = _as_user(permissions=[MANAGE_PERM])
    preview_uc = MagicMock()
    preview_uc.execute.return_value = PREVIEW_OK
    try:
        with (
            patch(
                "si_app.interface.http.routes.strategic_indicators_routes.build_preview_strategic_indicators_admin_config_use_case",
                return_value=preview_uc,
            ),
            patch(
                "si_app.interface.http.routes.strategic_indicators_routes.invalidate_strategic_indicators_snapshot_cache"
            ) as invalidate,
        ):
            response = TestClient(_app()).post(
                "/strategic-indicators/admin/config/import/preview",
                json={**MINIMAL_BODY, "mode": "replace"},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert "planned" in payload
    assert "current_counts" in payload
    invalidate.assert_not_called()
    preview_uc.execute.assert_called_once()


def test_apply_replace_returns_stats_and_invalidates():
    token = _as_user(permissions=[MANAGE_PERM])
    apply_uc = MagicMock()
    apply_uc.execute.return_value = APPLY_OK
    try:
        with (
            patch(
                "si_app.interface.http.routes.strategic_indicators_routes.build_import_strategic_indicators_admin_config_use_case",
                return_value=apply_uc,
            ),
            patch(
                "si_app.interface.http.routes.strategic_indicators_routes.invalidate_strategic_indicators_snapshot_cache"
            ) as invalidate,
        ):
            response = TestClient(_app()).post(
                "/strategic-indicators/admin/config/import/apply",
                json={**MINIMAL_BODY, "mode": "replace"},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    payload = response.json()
    assert payload["stats"]["mode"] == "replace"
    assert payload["stats"]["departments_deleted"] == 7
    invalidate.assert_called_once()


def test_import_alias_uses_apply_contract():
    token = _as_user(permissions=[MANAGE_PERM])
    apply_uc = MagicMock()
    apply_uc.execute.return_value = APPLY_OK
    try:
        with (
            patch(
                "si_app.interface.http.routes.strategic_indicators_routes.build_import_strategic_indicators_admin_config_use_case",
                return_value=apply_uc,
            ),
            patch(
                "si_app.interface.http.routes.strategic_indicators_routes.invalidate_strategic_indicators_snapshot_cache"
            ),
        ):
            response = TestClient(_app()).post(
                "/strategic-indicators/admin/config/import",
                json={**MINIMAL_BODY, "mode": "replace"},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    assert response.json()["stats"]["mode"] == "replace"
    apply_uc.execute.assert_called_once()


def test_preview_incompatible_schema_returns_400():
    token = _as_user(permissions=[MANAGE_PERM])
    preview_uc = MagicMock()
    preview_uc.execute.side_effect = ValueError(
        "schema_version incompatível: esperado 1."
    )
    try:
        with patch(
            "si_app.interface.http.routes.strategic_indicators_routes.build_preview_strategic_indicators_admin_config_use_case",
            return_value=preview_uc,
        ):
            response = TestClient(_app()).post(
                "/strategic-indicators/admin/config/import/preview",
                json={**MINIMAL_BODY, "schema_version": 2},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 400
    assert "schema_version" in response.json()["detail"]


def test_apply_forbidden_without_permission():
    from fastapi import HTTPException

    token = _as_user(permissions=[])

    def _deny(_user) -> None:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        with patch(
            "delpi_auth.authorization._deny_missing_permission",
            _deny,
        ):
            response = TestClient(_app()).post(
                "/strategic-indicators/admin/config/import/apply",
                json={**MINIMAL_BODY, "mode": "replace"},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 403

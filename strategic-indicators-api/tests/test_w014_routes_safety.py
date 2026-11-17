"""W014 — HTTP-level contract for bulk goals, config import, jobs.

Covers the transport mappings the service-level safety tests cannot see:
typed conflicts → 409, admission refusal → 429, actor-scoped job status
→ 404, write_origin allowlist → 400, owner AuthZ → 403, and the bulk
item cap → 422.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from delpi_auth.context_resolver import resolve_user_context
from delpi_auth.middleware.fastapi_auth import map_authz_exception
from delpi_auth.request_context import reset_current_user, set_current_user
from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
from si_app.application.services.strategic_indicators.tree_load_jobs_service import (
    TreeLoadJobAdmissionError,
)
from si_app.interface.http.routes.strategic_indicators_routes import router
from si_app.application.services.strategic_indicators.indicator_goal_conflict_error import (
    StrategicIndicatorsGoalConflictError,
)


MANAGE_PERM = "strategic-indicators.settings.manage"
VIEW_PERM = "strategic-indicators.view"
ROUTES = "si_app.interface.http.routes.strategic_indicators_routes"

BULK_BODY = {
    "goal_year": 2026,
    "items": [
        {
            "indicator_id": "ind-1",
            "goal_label": "Meta 1",
            "goal_value": 10.0,
            "goal_periodicity": "monthly",
        }
    ],
}

DUP_BODY = {
    "source_year": 2025,
    "target_year": 2026,
    "department_ids": [],
    "overwrite_existing": False,
}

FILL_BODY = {
    "goal_year": 2026,
    "department_ids": [],
    "copy_from_year": 2025,
}

IMPORT_BODY = {
    "schema_version": 1,
    "departments": [],
    "department_indicators": [],
    "indicator_goals": [],
    "module_settings": {},
    "mode": "merge",
}


def _app() -> FastAPI:
    app = FastAPI()

    @app.middleware("http")
    async def _bind_user_state(request, call_next):
        # Mirrors the production JWT middleware: routes read the actor
        # from request.state.user, populated here from the test context.
        request.state.user = resolve_user_context()
        return await call_next(request)

    app.include_router(router)

    @app.exception_handler(Exception)
    async def _map_authz(_request, exc: Exception):
        mapped = map_authz_exception(exc)
        if mapped is not None:
            return mapped
        raise exc

    return app


def _as_user(*, permissions: list[str], user_id: str = "user-1"):
    return set_current_user(
        SimpleNamespace(
            id=user_id,
            is_superadmin=False,
            permissions=permissions,
            rbac_unavailable=False,
        )
    )


def _client(*, raise_server_exceptions: bool = True) -> TestClient:
    return TestClient(_app(), raise_server_exceptions=raise_server_exceptions)


# ------------------------------------------------------------ bulk goals


def test_bulk_create_conflict_maps_409():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    uc.execute.side_effect = StrategicIndicatorsGoalConflictError("stale")
    try:
        with (
            patch(
                f"{ROUTES}.build_bulk_create_strategic_indicators_indicator_goals_use_case",
                return_value=uc,
            ),
            patch(f"{ROUTES}.invalidate_strategic_indicators_snapshot_cache"),
        ):
            response = _client().post(
                "/strategic-indicators/admin/indicator-goals/bulk-create",
                json=BULK_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 409


def test_bulk_create_rejects_unknown_write_origin():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    try:
        with patch(
            f"{ROUTES}.build_bulk_create_strategic_indicators_indicator_goals_use_case",
            return_value=uc,
        ):
            response = _client().post(
                "/strategic-indicators/admin/indicator-goals/bulk-create"
                "?write_origin=not-allowlisted",
                json=BULK_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 400
    uc.execute.assert_not_called()


def test_bulk_create_items_cap_422():
    token = _as_user(permissions=[MANAGE_PERM])
    try:
        response = _client().post(
            "/strategic-indicators/admin/indicator-goals/bulk-create",
            json={
                "goal_year": 2026,
                "items": [
                    {
                        "indicator_id": f"ind-{i}",
                        "goal_label": "m",
                        "goal_value": 1.0,
                        "goal_periodicity": "monthly",
                    }
                    for i in range(501)
                ],
            },
        )
    finally:
        reset_current_user(token)
    assert response.status_code == 422


def test_bulk_create_forbidden_without_manage_perm():
    token = _as_user(permissions=[VIEW_PERM])
    try:
        response = _client(raise_server_exceptions=False).post(
            "/strategic-indicators/admin/indicator-goals/bulk-create",
            json=BULK_BODY,
        )
    finally:
        reset_current_user(token)
    assert response.status_code in (401, 403)


def test_duplicate_year_conflict_maps_409():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    uc.execute.side_effect = StrategicIndicatorsAdminConflictError("drift")
    try:
        with (
            patch(
                f"{ROUTES}.build_duplicate_strategic_indicators_indicator_goals_year_use_case",
                return_value=uc,
            ),
            patch(f"{ROUTES}.invalidate_strategic_indicators_snapshot_cache"),
        ):
            response = _client().post(
                "/strategic-indicators/admin/indicator-goals/duplicate-year",
                json=DUP_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 409


def test_duplicate_year_threads_digests_and_audit():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    uc.execute.return_value = {"items": []}
    try:
        with (
            patch(
                f"{ROUTES}.build_duplicate_strategic_indicators_indicator_goals_year_use_case",
                return_value=uc,
            ),
            patch(f"{ROUTES}.invalidate_strategic_indicators_snapshot_cache"),
        ):
            response = _client().post(
                "/strategic-indicators/admin/indicator-goals/duplicate-year"
                "?expected_source_digest=abc"
                "&expected_existing_digest=def"
                "&write_origin=davi-mcp"
                "&correlation_id=prop-1",
                json=DUP_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    kwargs = uc.execute.call_args.kwargs
    assert kwargs["expected_source_digest"] == "abc"
    assert kwargs["expected_existing_digest"] == "def"
    assert kwargs["audit_origin"] == "davi-mcp"
    assert kwargs["correlation_id"] == "prop-1"


def test_fill_missing_conflict_maps_409():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    uc.execute.side_effect = StrategicIndicatorsAdminConflictError("drift")
    try:
        with (
            patch(
                f"{ROUTES}.build_fill_missing_strategic_indicators_indicator_goals_use_case",
                return_value=uc,
            ),
            patch(f"{ROUTES}.invalidate_strategic_indicators_snapshot_cache"),
        ):
            response = _client().post(
                "/strategic-indicators/admin/indicator-goals/fill-missing",
                json=FILL_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 409


# --------------------------------------------------------- config import


def test_import_apply_expected_counts_threaded_as_ints():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    uc.execute.return_value = {"message": "ok", "stats": {}}
    try:
        with (
            patch(
                f"{ROUTES}.build_import_strategic_indicators_admin_config_use_case",
                return_value=uc,
            ),
            patch(f"{ROUTES}.invalidate_strategic_indicators_snapshot_cache"),
        ):
            response = _client().post(
                "/strategic-indicators/admin/config/import/apply"
                "?expected_departments=3"
                "&expected_indicator_goals=10",
                json=IMPORT_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    kwargs = uc.execute.call_args.kwargs
    assert kwargs["expected_counts"] == {
        "departments": 3,
        "department_indicators": 0,
        "indicator_goals": 10,
    }


def test_import_apply_conflict_maps_409():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    uc.execute.side_effect = StrategicIndicatorsAdminConflictError("counts")
    try:
        with patch(
            f"{ROUTES}.build_import_strategic_indicators_admin_config_use_case",
            return_value=uc,
        ):
            response = _client().post(
                "/strategic-indicators/admin/config/import/apply",
                json=IMPORT_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 409


def test_import_apply_rejects_unknown_write_origin():
    token = _as_user(permissions=[MANAGE_PERM])
    uc = MagicMock()
    try:
        with patch(
            f"{ROUTES}.build_import_strategic_indicators_admin_config_use_case",
            return_value=uc,
        ):
            response = _client().post(
                "/strategic-indicators/admin/config/import/apply"
                "?write_origin=evil",
                json=IMPORT_BODY,
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 400
    uc.execute.assert_not_called()


# ------------------------------------------------------------------ jobs


def test_tree_load_job_admission_maps_429():
    token = _as_user(permissions=[VIEW_PERM])
    service = MagicMock()
    service.create_and_start.side_effect = TreeLoadJobAdmissionError("cap")
    try:
        with patch(
            f"{ROUTES}.get_tree_load_jobs_service", return_value=service
        ):
            response = _client().post(
                "/strategic-indicators/departments/tree/load-job",
                json={"view_mode": "consolidated", "months": 6},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 429


def test_tree_load_job_binds_actor():
    token = _as_user(permissions=[VIEW_PERM], user_id="actor-42")
    # A stubbed registry observes the actor argument without running the
    # real snapshot/trends use cases.
    stub = MagicMock()
    stub.create_and_start.return_value = MagicMock(
        job_id="j-1",
        state="queued",
        phase="snapshot",
        progress_pct=0,
        message="",
        created_at="",
        updated_at="",
    )
    try:
        with patch(f"{ROUTES}.get_tree_load_jobs_service", return_value=stub):
            response = _client().post(
                "/strategic-indicators/departments/tree/load-job",
                json={"view_mode": "consolidated", "months": 6},
            )
    finally:
        reset_current_user(token)
    assert response.status_code == 200
    kwargs = stub.create_and_start.call_args.kwargs
    assert kwargs["actor_user_id"] == "actor-42"


def test_job_status_cross_actor_404():
    token = _as_user(permissions=[VIEW_PERM], user_id="actor-a")
    stub = MagicMock()
    # Owner-scoped lookup returns None for another actor's job.
    stub.get.return_value = None
    try:
        with patch(f"{ROUTES}.get_tree_load_jobs_service", return_value=stub):
            response = _client().get("/strategic-indicators/jobs/job-9")
    finally:
        reset_current_user(token)
    assert response.status_code == 404
    assert stub.get.call_args.kwargs["actor_user_id"] == "actor-a"

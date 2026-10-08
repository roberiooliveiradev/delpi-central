# app/tests/test_solutions_controller.py
"""Solution discovery surface — visibility != access."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import g

from app.create_app import create_app
from app.domain.ports.app_query_port import AppDTO, RouteDTO
from app.application.use_cases.list_solutions_use_case import (
    ListSolutionsUseCase,
)
from app.application.use_cases.get_solution_use_case import GetSolutionUseCase
from app.application.use_cases.solution_projection import diff_manifests


def _app_dto(app_id: str, permission: str | None) -> AppDTO:
    return AppDTO(
        id=app_id,
        name=app_id.title(),
        base_path=f"/apps/{app_id}",
        icon="gauge",
        type="microfrontend",
        entry_url=None,
        render_mode="federated",
        routes=[
            RouteDTO(
                path=f"/apps/{app_id}",
                label=f"{app_id} home",
                icon="home",
                permission_code=permission,
                show_in_menu=True,
                order=10,
                entry=None,
            )
        ],
    )


def _plugin_row(app_id: str):
    return SimpleNamespace(
        id=app_id,
        name=app_id.title(),
        description=f"{app_id} description",
        icon="gauge",
        type="microfrontend",
        version="1.2.3",
        active=True,
        base_path=f"/apps/{app_id}",
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _manifest(app_id: str):
    return {
        "id": app_id,
        "description": f"{app_id} description",
        "category": "operations",
        "version": "1.2.3",
        "features": {"boards": True},
        "dependencies": ["plugin-ui"],
        "permissions": [
            {"code": f"{app_id}.access", "name": f"Acessar {app_id}", "description": "Acesso."}
        ],
        "backend": {"serviceName": "secret-internal"},  # must never leak
        "security": {"internal": True},
    }


class _FakeUow:
    def __init__(self, apps, manifests=None, versions=None, snapshots=None):
        self.app_queries = SimpleNamespace(
            list_active_apps_with_routes=lambda: apps
        )
        self.plugin_manifests = SimpleNamespace(
            list_all=lambda: [
                {"app_id": k, "manifest": v} for k, v in (manifests or {}).items()
            ],
            get=lambda pid: (manifests or {}).get(pid),
        )
        self.plugins = SimpleNamespace(get_by_id=lambda pid: _plugin_row(pid))
        self.plugin_versions = SimpleNamespace(
            list_versions=lambda pid: versions or [],
            get_version=lambda pid, v: (snapshots or {}).get((pid, v)),
        )


class TestListSolutionsUseCase:
    def test_catalog_not_filtered_to_accessible(self):
        apps = [_app_dto("transformometro", "transformometro.access"),
                _app_dto("tv-dashboard", "tv-dashboard.access")]
        uow = _FakeUow(apps, {"transformometro": _manifest("transformometro")})
        result = ListSolutionsUseCase(uow).execute(
            permissions=["transformometro.access"], is_superadmin=False
        )
        by_id = {s["id"]: s for s in result}
        # user lacks tv-dashboard → still appears, accessible=false
        assert by_id["transformometro"]["accessible"] is True
        assert by_id["tv-dashboard"]["accessible"] is False

    def test_superadmin_sees_all_accessible(self):
        uow = _FakeUow([_app_dto("a", "a.x"), _app_dto("b", "b.x")])
        result = ListSolutionsUseCase(uow).execute(permissions=[], is_superadmin=True)
        assert all(s["accessible"] for s in result)

    def test_no_sensitive_fields(self):
        uow = _FakeUow(
            [_app_dto("x", "x.access")],
            {"x": _manifest("x")},
        )
        result = ListSolutionsUseCase(uow).execute(permissions=[], is_superadmin=False)
        text = str(result)
        for forbidden in ("backend", "serviceName", "security", "entry",
                          "checksum", "created_by", "observability"):
            assert forbidden not in text
        assert result[0]["features"] == {"boards": True}
        assert result[0]["permissions"][0]["code"] == "x.access"
        assert result[0]["routes"][0]["label"] == "x home"


class TestGetSolutionUseCase:
    def test_unknown_returns_none(self):
        uow = _FakeUow([_app_dto("a", "a.x")])
        assert GetSolutionUseCase(uow).execute(
            "nope", permissions=[], is_superadmin=False) is None

    def test_evolution_is_calculated(self):
        old = _manifest("x")
        new = dict(_manifest("x"), version="1.3.0", description="new desc")
        new["routes"] = old.get("routes") or []
        snapshots = {("x", "1.2.3"): {"version": "1.2.3", "manifest": old},
                     ("x", "1.3.0"): {"version": "1.3.0", "manifest": new}}
        versions = [{"version": "1.3.0"}, {"version": "1.2.3"}]
        uow = _FakeUow([_app_dto("x", "x.access")], {"x": new}, versions, snapshots)
        result = GetSolutionUseCase(uow).execute(
            "x", permissions=["x.access"], is_superadmin=False)
        assert result["accessible"] is True
        assert result["evolution"]["basis"] == "CALCULATED"
        assert result["evolution"]["versionChanged"] is True
        assert result["evolution"]["descriptionChanged"] is True
        assert result["recentVersions"] == versions

    def test_no_versions_evolution_none(self):
        uow = _FakeUow([_app_dto("x", "x.access")], {"x": _manifest("x")})
        result = GetSolutionUseCase(uow).execute(
            "x", permissions=[], is_superadmin=False)
        assert result["evolution"] is None


class TestDiffManifests:
    def test_route_and_permission_drift(self):
        cur = {"version": "2", "routes": [{"path": "/a"}, {"path": "/b"}],
               "permissions": [{"code": "p1"}, {"code": "p2"}]}
        prev = {"version": "1", "routes": [{"path": "/a"}],
                "permissions": [{"code": "p1"}, {"code": "p0"}]}
        diff = diff_manifests(cur, prev)
        assert diff["routesAdded"] == ["/b"]
        assert diff["permissionsAdded"] == ["p2"]
        assert diff["permissionsRemoved"] == ["p0"]


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def test_solutions_requires_auth(client):
    assert client.get("/solutions").status_code == 401
    assert client.get("/solutions/x").status_code == 401


@patch("app.interfaces.http.solutions_controller.SqlAlchemyUnitOfWork")
def test_solutions_list_and_detail(mock_uow_cls, client, app):
    fake = _FakeUow([_app_dto("tv-dashboard", "tv-dashboard.access")])
    mock_uow_cls.return_value.__enter__.return_value = fake
    user = MagicMock(permissions=["other.access"], is_superadmin=False)
    with app.app_context():
        with client.session_transaction():
            pass
        with client:
            # inject authenticated user like auth middleware does
            @app.before_request
            def _inject():
                g.current_user = user
            r1 = client.get("/solutions")
            r2 = client.get("/solutions/tv-dashboard")
            r3 = client.get("/solutions/nope")
    assert r1.status_code == 200
    assert r1.get_json()["data"][0]["accessible"] is False
    assert r2.status_code == 200
    assert r2.get_json()["data"]["id"] == "tv-dashboard"
    assert r3.status_code == 404

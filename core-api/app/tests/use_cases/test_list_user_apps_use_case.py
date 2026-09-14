# app/tests/use_cases/test_list_user_apps_use_case.py

from types import SimpleNamespace
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase


class FakeAppQuery:
    def __init__(self, apps):
        self._apps = apps

    def list_active_apps_with_routes(self):
        return self._apps


def _route(**kwargs):
    defaults = {
        "permission_code": None,
        "path": "/",
        "label": "Label",
        "icon": "icon",
        "show_in_menu": True,
        "order": 1,
        "entry": None,
        "open_in_new_tab": False,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_list_user_apps_filters_routes_by_permission():
    route_public = _route(permission_code=None, path="/public", label="Public", order=1)
    route_protected = _route(
        permission_code="dashboard.view",
        path="/dash",
        label="Dash",
        order=2,
    )

    app = SimpleNamespace(
        id="crm",
        name="CRM",
        base_path="/crm",
        icon="icon",
        type="microfrontend",
        entry_url=None,
        render_mode=None,
        routes=[route_public, route_protected],
    )

    use_case = ListUserAppsUseCase(app_query=FakeAppQuery([app]))
    result = use_case.execute(
        permissions=["dashboard.view"],
        is_superadmin=False,
    )

    assert len(result) == 1
    assert len(result[0]["routes"]) == 2


def test_list_user_apps_allow_override_permission_grants_route():
    route = _route(permission_code="permission.d", path="/allow")
    app = SimpleNamespace(
        id="ops",
        name="Ops",
        base_path="/ops",
        icon="icon",
        type="microfrontend",
        entry_url=None,
        render_mode=None,
        routes=[route],
    )

    result = ListUserAppsUseCase(FakeAppQuery([app])).execute(
        permissions=["permission.d"],
        is_superadmin=False,
    )

    assert len(result) == 1
    assert result[0]["routes"][0]["path"] == "/allow"


def test_list_user_apps_deny_override_permission_blocks_route():
    route = _route(permission_code="permission.b", path="/deny")
    app = SimpleNamespace(
        id="ops",
        name="Ops",
        base_path="/ops",
        icon="icon",
        type="microfrontend",
        entry_url=None,
        render_mode=None,
        routes=[route],
    )

    result = ListUserAppsUseCase(FakeAppQuery([app])).execute(
        permissions=["permission.a"],
        is_superadmin=False,
    )

    assert result == []

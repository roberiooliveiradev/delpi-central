# app/tests/use_cases/test_list_user_apps_use_case.py

from types import SimpleNamespace
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase


class FakePermissionResolver:
    def __init__(self, permissions):
        self._permissions = permissions

    def resolve(self, user_id, is_superadmin):
        return self._permissions


class FakeAppQuery:
    def __init__(self, apps):
        self._apps = apps

    def list_active_apps_with_routes(self):
        return self._apps


def test_list_user_apps_filters_routes_by_permission():

    route_public = SimpleNamespace(
        permission_code=None,
        path="/public",
        label="Public",
        icon="icon",
        show_in_menu=True,
        order=1,
    )

    route_protected = SimpleNamespace(
        permission_code="dashboard.view",
        path="/dash",
        label="Dash",
        icon="icon",
        show_in_menu=True,
        order=2,
    )

    app = SimpleNamespace(
        id="crm",
        name="CRM",
        base_path="/crm",
        icon="icon",
        type="microfrontend",
        routes=[route_public, route_protected],
    )

    use_case = ListUserAppsUseCase(
        app_query=FakeAppQuery([app]),
        permission_resolver=FakePermissionResolver({"dashboard.view"}),
    )

    result = use_case.execute("user1", False)

    assert len(result) == 1
    assert len(result[0]["routes"]) == 2
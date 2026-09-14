# app/tests/test_effective_permissions_alignment.py
"""
Proves Core effective-permissions alignment across:
- PermissionResolver (canonical)
- authenticated context projection (/me consumers)
- /me/access-profile.effectivePermissions
- /me/apps filtering
- cache invalidation after RBAC mutation sync
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from flask import Flask, g

from app.application.event_handlers.rbac_event_handler import RbacEventHandler
from app.application.services.app_authorization_service import AppAuthorizationService
from app.application.use_cases.get_my_access_profile_use_case import (
    GetMyAccessProfileUseCase,
)
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.permission_resolver import PermissionResolver
from app.interfaces.http import me_controller


class FakeCache:
    def __init__(self):
        self.store = {}

    def get(self, user_id):
        return self.store.get(user_id)

    def set(self, user_id, permissions):
        self.store[user_id] = list(permissions)

    def invalidate(self, user_id):
        self.store.pop(user_id, None)


class FakePermissionQueries:
    def __init__(
        self,
        *,
        all_permissions=None,
        direct=None,
        group=None,
        overrides=None,
    ):
        self._all = list(all_permissions or [])
        self._direct = list(direct or [])
        self._group = list(group or [])
        self._overrides = list(overrides or [])

    def list_all_permission_codes(self):
        return list(self._all)

    def list_direct_role_permissions(self, _user_id):
        return list(self._direct)

    def list_group_role_permissions(self, _user_id):
        return list(self._group)

    def list_user_overrides(self, _user_id):
        return list(self._overrides)

    def list_permissions_by_role_id(self, _role_id):
        return []


def _effective_state():
    return FakePermissionQueries(
        direct=["permission.a", "permission.b"],
        group=["permission.c"],
        overrides=[("permission.b", False), ("permission.d", True)],
    )


def test_me_permissions_match_access_profile_effective_permissions():
    user_id = uuid4()
    queries = _effective_state()
    cache = FakeCache()

    effective = PermissionResolver(queries, cache).resolve(user_id, False)
    assert sorted(effective) == ["permission.a", "permission.c", "permission.d"]

    uow = MagicMock()
    uow.user_roles.list_role_ids.return_value = []
    uow.user_groups.list_group_ids.return_value = []
    uow.app_queries.list_active_apps_with_routes.return_value = []
    uow.permission_queries = queries
    uow.cache = cache

    profile = GetMyAccessProfileUseCase(uow).execute(user_id, is_superadmin=False)

    assert profile["effectivePermissions"] == effective


def test_me_endpoint_projects_current_user_effective_permissions(monkeypatch):
    flask_app = Flask("test_me_effective")
    flask_app.config["TESTING"] = True
    flask_app.register_blueprint(me_controller.me_bp)

    class FakeConsents:
        def list_by_user(self, _user_id):
            return []

    class FakeUow:
        def __init__(self):
            self.consents = FakeConsents()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(me_controller, "SqlAlchemyUnitOfWork", FakeUow)

    effective = ["permission.a", "permission.c", "permission.d"]
    client = flask_app.test_client()

    with flask_app.app_context():
        with client:
            g.current_user = SimpleNamespace(
                id=str(uuid4()),
                name="User",
                email="user@test.com",
                roles=["role.direct"],
                groups=["group.ops"],
                permissions=effective,
                is_superadmin=False,
            )
            response = client.get("/me")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["permissions"] == effective


def test_list_user_apps_uses_effective_permissions_allow_override():
    route_protected = SimpleNamespace(
        permission_code="permission.d",
        path="/granted-by-allow",
        label="Allow",
        icon="icon",
        show_in_menu=True,
        order=1,
        entry=None,
        open_in_new_tab=False,
    )
    route_denied = SimpleNamespace(
        permission_code="permission.b",
        path="/removed-by-deny",
        label="Deny",
        icon="icon",
        show_in_menu=True,
        order=2,
        entry=None,
        open_in_new_tab=False,
    )
    app = SimpleNamespace(
        id="ops",
        name="Ops",
        base_path="/ops",
        icon="icon",
        type="microfrontend",
        entry_url=None,
        render_mode=None,
        routes=[route_protected, route_denied],
    )

    class FakeAppQuery:
        def list_active_apps_with_routes(self):
            return [app]

    effective = ["permission.a", "permission.c", "permission.d"]
    result = ListUserAppsUseCase(FakeAppQuery()).execute(
        permissions=effective,
        is_superadmin=False,
    )

    assert len(result) == 1
    paths = [route["path"] for route in result[0]["routes"]]
    assert "/granted-by-allow" in paths
    assert "/removed-by-deny" not in paths


def test_list_user_apps_deny_override_removes_access():
    route = SimpleNamespace(
        permission_code="permission.b",
        path="/sensitive",
        label="Sensitive",
        icon="icon",
        show_in_menu=True,
        order=1,
        entry=None,
        open_in_new_tab=False,
    )
    app = SimpleNamespace(
        id="crm",
        name="CRM",
        base_path="/crm",
        icon="icon",
        type="microfrontend",
        entry_url=None,
        render_mode=None,
        routes=[route],
    )

    class FakeAppQuery:
        def list_active_apps_with_routes(self):
            return [app]

    # Inherited would include permission.b; effective after deny does not.
    result = ListUserAppsUseCase(FakeAppQuery()).execute(
        permissions=["permission.a", "permission.c"],
        is_superadmin=False,
    )
    assert result == []


def test_superadmin_context_reaches_app_authorization_with_all_codes():
    apps = [
        SimpleNamespace(
            id="any",
            name="Any",
            base_path="/any",
            icon="i",
            type="microfrontend",
            entry_url=None,
            render_mode=None,
            routes=[
                SimpleNamespace(permission_code="secret.permission", path="/s", label="S")
            ],
        )
    ]
    auth = AppAuthorizationService()
    filtered = auth.filter_apps(apps, permissions=[], is_superadmin=True)
    assert len(filtered) == 1


def test_rbac_event_handler_invalidates_cache_before_resync():
    user_id = uuid4()
    cache = FakeCache()
    cache.set(str(user_id), ["stale.permission"])

    queries = FakePermissionQueries(
        direct=["permission.a"],
        group=[],
        overrides=[],
    )

    user = SimpleNamespace(id=user_id, is_superadmin=False)
    uow = MagicMock()
    uow.cache = cache
    uow.users.get_by_id.return_value = user
    uow.permission_queries = queries

    # IamSyncService.resolve then invalidate — prove mutation clears stale entry.
    handler = RbacEventHandler(uow)
    handler.handle(
        AdminChangedEvent(
            entity="rbac",
            action="role_added_to_user",
            payload={"userId": str(user_id)},
            target_user_id=str(user_id),
        )
    )

    assert cache.get(str(user_id)) is None

    # Subsequent resolve reflects post-mutation state.
    queries._direct = ["permission.a", "permission.new"]
    resolved = PermissionResolver(queries, cache).resolve(user_id, False)
    assert sorted(resolved) == ["permission.a", "permission.new"]
    assert cache.get(str(user_id)) == ["permission.a", "permission.new"]

# app/tests/test_rbac_access_delta_service.py

from uuid import uuid4

from app.application.services.rbac_access_delta_service import RbacAccessDeltaService
from app.domain.ports.app_query_port import AppDTO, RouteDTO


def _app(app_id, name, perm_code):
    return AppDTO(
        id=app_id,
        name=name,
        base_path=f"/{name}",
        icon=None,
        type="internal",
        entry_url=None,
        render_mode=None,
        routes=[
            RouteDTO(
                path="/",
                label="Início",
                icon=None,
                permission_code=perm_code,
                show_in_menu=True,
                order=0,
                entry=None,
            ),
            RouteDTO(
                path="/extra",
                label="Relatórios",
                icon=None,
                permission_code=f"{perm_code}.reports",
                show_in_menu=True,
                order=1,
                entry=None,
            ),
        ],
    )


class FakePermissionQueries:
    def __init__(self, full_codes=None, role_codes=None, previous_direct=None, previous_group=None):
        self.role_codes = role_codes or []
        self.previous_direct = previous_direct or []
        self.previous_group = previous_group or []

    def list_direct_role_permissions_excluding_roles(self, user_id, exclude_role_ids):
        return self.previous_direct

    def list_group_role_permissions_excluding_groups(self, user_id, exclude_group_ids):
        return []

    def list_group_role_permissions_excluding_roles(self, user_id, exclude_role_ids):
        if exclude_role_ids:
            return []
        return self.previous_group

    def list_group_role_permissions_excluding_roles_for_group(
        self, user_id, group_id, exclude_role_ids
    ):
        return []

    def list_permission_codes_granted_by_role_for_user(self, user_id, role_id):
        return self.role_codes

    def list_user_overrides(self, user_id):
        return []

    def list_permissions_by_codes(self, codes):
        from types import SimpleNamespace

        rows = []
        for code in codes:
            if code.startswith("users."):
                rows.append(
                    SimpleNamespace(
                        code=code,
                        name="Gerenciar usuários" if code == "users.manage" else "Visualizar usuários",
                        module="system",
                    )
                )
        return rows


class FakeResolver:
    def __init__(self, codes):
        self.codes = codes

    def resolve(self, user_id, is_superadmin):
        return self.codes


def test_compute_gain_new_app_when_role_was_not_present(monkeypatch):
    user_id = uuid4()
    app = _app("app-1", "Controle MP", "mp.access")

    queries = FakePermissionQueries(full_codes=[], previous_direct=[], previous_group=[])
    service = RbacAccessDeltaService(
        queries,
        None,
        type("", (), {"list_active_apps_with_routes": lambda _self: [app]})(),
    )

    monkeypatch.setattr(
        "app.application.services.rbac_access_delta_service.PermissionResolver",
        lambda *a, **k: FakeResolver(["mp.access", "mp.access.reports"]),
    )

    gain = service.compute_gain(user_id, False, previous_codes=[])

    assert len(gain.new_apps) == 1
    assert gain.new_apps[0].name == "Controle MP"


def test_compute_gain_no_new_app_when_permission_already_had(monkeypatch):
    user_id = uuid4()
    app = _app("app-1", "Controle MP", "mp.access")

    queries = FakePermissionQueries(
        previous_direct=["mp.access"],
        previous_group=[],
    )
    service = RbacAccessDeltaService(
        queries,
        None,
        type("", (), {"list_active_apps_with_routes": lambda _self: [app]})(),
    )

    monkeypatch.setattr(
        "app.application.services.rbac_access_delta_service.PermissionResolver",
        lambda *a, **k: FakeResolver(["mp.access", "mp.access.reports"]),
    )

    gain = service.compute_gain(user_id, False, previous_codes=["mp.access"])

    assert gain.new_apps == []
    assert len(gain.new_routes) == 1
    assert gain.new_routes[0][1].label == "Relatórios"


def test_previous_codes_excluding_user_roles_ignores_group_copy_of_role():
    user_id = uuid4()
    role_id = uuid4()

    queries = FakePermissionQueries(
        previous_direct=[],
        previous_group=["mp.access"],
    )
    service = RbacAccessDeltaService(
        queries,
        None,
        type("", (), {"list_active_apps_with_routes": lambda _self: []})(),
    )

    previous = service.previous_codes_excluding_user_roles(
        user_id,
        False,
        {role_id},
    )

    assert "mp.access" not in previous


def test_compute_gain_includes_system_permissions(monkeypatch):
    user_id = uuid4()
    queries = FakePermissionQueries()
    service = RbacAccessDeltaService(
        queries,
        None,
        type("", (), {"list_active_apps_with_routes": lambda _self: []})(),
    )

    monkeypatch.setattr(
        "app.application.services.rbac_access_delta_service.PermissionResolver",
        lambda *a, **k: FakeResolver(["users.manage"]),
    )

    gain = service.compute_gain(user_id, False, previous_codes=[])

    assert gain.has_gain is True
    assert len(gain.new_system_permissions) == 1
    assert gain.new_system_permissions[0].code == "users.manage"


def test_compute_gain_uses_permission_snapshot_after_role_swap(monkeypatch):
    user_id = uuid4()
    app = _app("app-1", "Controle MP", "mp.access")

    queries = FakePermissionQueries()
    service = RbacAccessDeltaService(
        queries,
        None,
        type("", (), {"list_active_apps_with_routes": lambda _self: [app]})(),
    )

    monkeypatch.setattr(
        "app.application.services.rbac_access_delta_service.PermissionResolver",
        lambda *a, **k: FakeResolver(["mp.access"]),
    )

    gain = service.compute_gain(user_id, False, previous_codes=["other.legacy"])

    assert len(gain.new_apps) == 1

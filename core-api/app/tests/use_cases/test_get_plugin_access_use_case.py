# app/tests/use_cases/test_get_plugin_access_use_case.py

from types import SimpleNamespace
from uuid import uuid4

from app.application.use_cases.get_plugin_access_use_case import GetPluginAccessUseCase


def test_get_plugin_access_builds_paths():
    plugin_id = "crm"
    perm_id = uuid4()
    role_id = uuid4()
    group_id = uuid4()
    user_direct = uuid4()
    user_group = uuid4()

    uow = SimpleNamespace(
        plugins=SimpleNamespace(get_by_id=lambda pid: {"id": pid}),
        plugin_permissions=SimpleNamespace(
            list_by_module=lambda m: [
                {
                    "id": str(perm_id),
                    "code": "crm.view",
                    "name": "View",
                    "description": None,
                }
            ]
        ),
        role_permissions=SimpleNamespace(
            list_role_ids_by_permission_id=lambda pid: [role_id],
            list_permission_codes=lambda rid: ["crm.view", "other.x"],
        ),
        roles=SimpleNamespace(
            get=lambda rid: SimpleNamespace(
                id=role_id, name="Ops", description=None
            )
        ),
        user_roles=SimpleNamespace(
            list_user_ids_by_role_id=lambda rid: [user_direct]
        ),
        group_roles=SimpleNamespace(
            list_group_role_ids_by_role_ids=lambda rids: [(group_id, role_id)]
        ),
        groups=SimpleNamespace(
            get=lambda gid: SimpleNamespace(
                id=group_id, name="TI", description=None
            )
        ),
        user_groups=SimpleNamespace(
            list_user_ids_by_group_id=lambda gid: [user_group]
        ),
        users=SimpleNamespace(
            get_by_ids=lambda ids: [
                SimpleNamespace(
                    id=user_direct,
                    name="Ana",
                    email="ana@x",
                    is_superadmin=False,
                ),
                SimpleNamespace(
                    id=user_group,
                    name="Bruno",
                    email="bruno@x",
                    is_superadmin=False,
                ),
            ]
        ),
    )

    result = GetPluginAccessUseCase(uow).execute(plugin_id)

    assert result.success
    data = result.data
    assert data["summary"]["userCount"] == 2
    assert data["roles"][0]["permissionCodes"] == ["crm.view"]
    ana = next(u for u in data["users"] if u["name"] == "Ana")
    assert any(p["type"] == "role" for p in ana["paths"])
    bruno = next(u for u in data["users"] if u["name"] == "Bruno")
    assert any(p["type"] == "group_role" for p in bruno["paths"])


def test_get_plugin_access_not_found():
    uow = SimpleNamespace(plugins=SimpleNamespace(get_by_id=lambda pid: None))
    result = GetPluginAccessUseCase(uow).execute("missing")
    assert not result.success
    assert result.errors[0]["code"] == "plugin.not_found"

from types import SimpleNamespace

from maint_app.application.services.maintenance_submodule_catalog import filter_submodules_for_user


def test_filter_submodules_requires_view_permission():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.view.filial-01"],
    )
    assert filter_submodules_for_user(user) == []


def test_filter_submodules_with_view_permission():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.view", "maintenance.view.filial-01"],
    )
    items = filter_submodules_for_user(user)
    assert len(items) == 1
    assert items[0]["id"] == "mini-aplicadores"
    assert items[0]["can_manage"] is False


def test_filter_submodules_manage_flag():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.mini-applicators.view",
            "maintenance.mini-applicators.manage",
        ],
    )
    items = filter_submodules_for_user(user)
    assert items[0]["can_manage"] is True

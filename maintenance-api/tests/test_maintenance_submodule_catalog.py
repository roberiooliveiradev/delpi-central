from types import SimpleNamespace

from maint_app.application.services.filial_access_scope_service import FilialAccessScope
from maint_app.application.services.maintenance_submodule_catalog import filter_submodules_for_user


def test_filter_submodules_requires_submodule_permission():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.view"],
    )
    assert filter_submodules_for_user(user) == []


def test_filter_submodules_with_mini_applicators_view():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.view.filial-01"],
    )
    scope = FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset(),
    )
    items = filter_submodules_for_user(user, filial="01", scope=scope)
    assert len(items) == 1
    assert items[0]["id"] == "mini-aplicadores"
    assert items[0]["can_manage"] is False
    assert items[0]["filiais"] is None


def test_filter_submodules_manage_flag_per_filial():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.mini-applicators.view.filial-01",
            "maintenance.mini-applicators.manage.filial-01",
        ],
    )
    scope = FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset({"01"}),
    )
    items = filter_submodules_for_user(user, filial="01", scope=scope)
    assert items[0]["can_manage"] is True


def test_filter_submodules_manutencao_geral_filial_permission():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.manutencao-geral.view.filial-01"],
    )
    scope = FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset(),
    )
    items = filter_submodules_for_user(user, filial="01", scope=scope)
    assert len(items) == 1
    assert items[0]["id"] == "manutencao-geral"
    assert items[0]["filiais"] == ["01"]


def test_filter_submodules_manutencao_geral_hidden_for_filial_02():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.manutencao-geral.view.filial-01",
            "maintenance.mini-applicators.view.filial-02",
        ],
    )
    scope = FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01", "02"}),
        manage_codigos=frozenset(),
    )
    items = filter_submodules_for_user(user, filial="02", scope=scope)
    assert all(item["id"] != "manutencao-geral" for item in items)
    assert len(items) == 1
    assert items[0]["id"] == "mini-aplicadores"

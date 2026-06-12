from types import SimpleNamespace

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService


def test_resolve_scope_from_manifest_view_permissions():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.mini-applicators.view.filial-02",
            "maintenance.manutencao-geral.view.filial-01",
        ],
    )
    scope = FilialAccessScopeService().resolve(user)
    assert scope.mode == "scoped"
    assert scope.allowed_codigos == frozenset({"01", "02"})
    assert scope.manage_codigos == frozenset()


def test_resolve_scope_manage_only_from_mini_applicators_manifest():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.mini-applicators.view.filial-01",
            "maintenance.mini-applicators.manage.filial-01",
        ],
    )
    scope = FilialAccessScopeService().resolve(user)
    assert scope.manage_codigos == frozenset({"01"})


def test_resolve_scope_ignores_legacy_generic_filial_permissions():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.view.filial-01",
            "maintenance.manage.filial-01",
        ],
    )
    scope = FilialAccessScopeService().resolve(user)
    assert scope.allowed_codigos == frozenset()
    assert scope.manage_codigos == frozenset()


def test_can_manage_filial_uses_manifest_manage_permission():
    svc = FilialAccessScopeService()
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.manage.filial-02"],
    )
    scope = svc.resolve(user)
    assert svc.can_manage_filial(scope, "02", user=user) is True
    assert svc.can_manage_filial(scope, "01", user=user) is False

import pytest

from tv_app.application.services.branch_access_scope_service import BranchAccessScopeService


class FakeUser:
    def __init__(self, *, permissions=None, is_superadmin=False):
        self.permissions = permissions or []
        self.is_superadmin = is_superadmin


def test_unrestricted_for_superadmin():
    svc = BranchAccessScopeService()
    scope = svc.resolve(FakeUser(is_superadmin=True))
    assert scope.is_unrestricted
    assert svc.can_use_branch(scope, "01") is True


def test_scoped_user_only_allowed_filial():
    svc = BranchAccessScopeService()
    user = FakeUser(permissions=["tv-dashboard.view.filial-01"])
    scope = svc.resolve(user)
    assert scope.mode == "scoped"
    assert svc.can_use_branch(scope, "01") is True
    assert svc.can_use_branch(scope, "02") is False


def test_scoped_user_consolidated_requires_permission():
    svc = BranchAccessScopeService()
    user = FakeUser(permissions=["tv-dashboard.view.filial-01"])
    scope = svc.resolve(user)
    assert scope.allow_consolidated is False
    assert svc.can_use_branch(scope, None) is False

    user_consolidated = FakeUser(
        permissions=["tv-dashboard.view.filial-01", "tv-dashboard.view.consolidated"],
    )
    scope2 = svc.resolve(user_consolidated)
    assert svc.can_use_branch(scope2, None) is True


def test_branch_options_intersects_static_policy(monkeypatch):
    import tv_app.application.services.tv_dashboard_content_service as content_module

    content_module._load_settings.cache_clear()
    monkeypatch.setattr(
        content_module,
        "_load_settings",
        lambda: {"branchPolicy": {"allowedBranches": ["01", "02"]}},
    )
    svc = BranchAccessScopeService()
    scope = svc.resolve(FakeUser(permissions=["tv-dashboard.view.filial-01"]))
    assert scope.branch_options() == ["01"]

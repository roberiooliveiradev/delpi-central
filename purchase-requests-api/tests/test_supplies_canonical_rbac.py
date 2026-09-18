from types import SimpleNamespace

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_access,
    has_branch_access,
    has_view_all,
)


def _user(*codes: str):
    return SimpleNamespace(is_superadmin=False, permissions=set(codes))


def test_canonical_access_requires_unit_and_does_not_open_other_branch():
    user = _user("supplies.access", "supplies.unit.filial-01")
    assert has_access(user) is True
    assert has_branch_access(user, "01") is True
    assert has_branch_access(user, "02") is False


def test_access_without_unit_denies_branch():
    user = _user("supplies.access")
    assert has_branch_access(user, "01") is False


def test_manage_only_is_not_sc_access():
    user = _user("supplies.manage")
    assert has_access(user) is False
    assert has_branch_access(user, "01") is False


def test_view_all_does_not_grant_unit():
    user = _user("supplies.purchase-requests.view-all", "supplies.unit.filial-01")
    assert has_view_all(user) is True
    assert has_access(user) is False
    assert has_branch_access(user, "02") is False

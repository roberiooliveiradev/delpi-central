from types import SimpleNamespace

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_access,
    has_branch_access,
    has_view_all,
)


def _user(*codes: str):
    return SimpleNamespace(is_superadmin=False, permissions=set(codes))


def test_canonical_access_opens_both_branches_and_all_cost_centers():
    user = _user("supplies.access")
    assert has_access(user) is True
    assert has_view_all(user) is True
    assert has_branch_access(user, "01") is True
    assert has_branch_access(user, "02") is True


def test_access_without_supplies_access_still_needs_purchase_request_unit():
    user = _user("purchase-requests.access")
    assert has_branch_access(user, "01") is False


def test_manage_only_is_not_sc_access():
    user = _user("supplies.manage")
    assert has_access(user) is False
    assert has_view_all(user) is False
    assert has_branch_access(user, "01") is False


def test_deleted_supplies_view_all_does_not_grant_scope():
    user = _user("supplies.purchase-requests.view-all", "supplies.unit.filial-01")
    assert has_view_all(user) is False
    assert has_access(user) is False
    assert has_branch_access(user, "01") is False

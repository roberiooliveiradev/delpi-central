"""Catálogo condensado commercial.access / manage / billing.notify."""

from types import SimpleNamespace

from commercial_app.application.security import commercial_permissions as perms


def _user(*codes: str) -> SimpleNamespace:
    return SimpleNamespace(permissions=list(codes), is_superadmin=False)


def test_canonical_codes() -> None:
    assert perms.COMMERCIAL_ACCESS == "commercial.access"
    assert perms.COMMERCIAL_MANAGE == "commercial.manage"
    assert perms.COMMERCIAL_BILLING_NOTIFY == "commercial.billing.notify"


def test_has_access_covers_product_helpers() -> None:
    user = _user(perms.COMMERCIAL_ACCESS)
    assert perms.has_access(user)
    assert perms.can_read_commercial(user)
    assert perms.can_view_worklist(user)
    assert perms.can_manage_followups(user)
    assert perms.can_view_analytics(user)
    assert perms.can_view_proposals(user)
    assert perms.can_export_proposals(user)
    assert perms.can_view_audit(user)
    assert not perms.has_manage(user)
    assert not perms.can_manage_portfolios(user)
    assert not perms.can_use_team_scope(user)
    assert not perms.can_view_portfolio_billing_share(user)


def test_has_manage_covers_admin_and_team() -> None:
    user = _user(perms.COMMERCIAL_MANAGE)
    assert perms.has_manage(user)
    assert perms.can_manage_portfolios(user)
    assert perms.can_use_team_scope(user)
    assert perms.can_view_accounts_team(user)
    assert perms.can_view_worklist_team(user)
    assert perms.can_view_portfolio_billing_share(user)
    assert perms.can_view_audit(user)
    assert not perms.has_access(user)


def test_billing_notify_isolated() -> None:
    user = _user(perms.COMMERCIAL_BILLING_NOTIFY)
    assert perms.has_billing_notify(user)
    assert not perms.has_access(user)
    assert not perms.has_manage(user)


def test_decorator_tuples_are_three_codes_only() -> None:
    assert perms.COMMERCIAL_ACCESS_PERMISSIONS == (perms.COMMERCIAL_ACCESS,)
    assert perms.COMMERCIAL_MANAGE_PERMISSIONS == (perms.COMMERCIAL_MANAGE,)
    assert perms.COMMERCIAL_READ_PERMISSIONS == perms.COMMERCIAL_ACCESS_PERMISSIONS
    assert perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS == perms.COMMERCIAL_MANAGE_PERMISSIONS
    assert "api-delpi.access" not in perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS

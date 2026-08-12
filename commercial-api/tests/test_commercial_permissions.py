"""Testes de capacidades RBAC commercial-api — só codes canônicos commercial.*."""

from __future__ import annotations

from types import SimpleNamespace

from commercial_app.application.security import commercial_permissions as perms


def _user(*codes: str) -> SimpleNamespace:
    return SimpleNamespace(permissions=list(codes), roles=[], is_superadmin=False)


def test_analytics_only_canonical() -> None:
    assert perms.can_view_analytics(_user(perms.COMMERCIAL_ANALYTICS_VIEW))
    assert not perms.can_view_analytics(_user("dashboard-commercial.view"))
    assert not perms.can_view_analytics(_user("api-delpi.access"))
    assert not perms.can_view_analytics(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_proposals_only_canonical_en() -> None:
    assert perms.COMMERCIAL_PROPOSALS_VIEW == "commercial.proposals.view"
    assert perms.COMMERCIAL_PROPOSALS_EXPORT == "commercial.proposals.export"
    assert perms.can_view_proposals(_user(perms.COMMERCIAL_PROPOSALS_VIEW))
    assert not perms.can_view_proposals(_user("commercial.propostas.view"))
    assert not perms.can_view_proposals(_user("propostas-comerciais.view"))
    assert perms.can_export_proposals(_user(perms.COMMERCIAL_PROPOSALS_EXPORT))
    assert perms.can_export_proposals(_user(perms.COMMERCIAL_PROPOSALS_VIEW))
    assert not perms.can_export_proposals(_user("commercial.propostas.export"))
    assert not perms.can_view_proposals(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_team_scope_is_team_view_or_manage_without_legacy_aliases() -> None:
    assert perms.can_use_team_scope(_user(perms.COMMERCIAL_ACCOUNTS_TEAM_VIEW))
    assert perms.can_use_team_scope(_user(perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE))
    assert not perms.can_use_team_scope(_user("pedidos-venda-abertos.admin"))
    assert not perms.can_use_team_scope(_user("api-delpi.access"))
    assert not perms.can_view_accounts_team(_user("pedidos-venda-abertos.access"))
    assert not perms.can_use_team_scope(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_manage_portfolios_only_canonical() -> None:
    assert perms.can_manage_portfolios(_user(perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE))
    assert not perms.can_manage_portfolios(_user("api-delpi.access"))
    assert not perms.can_manage_portfolios(_user("pedidos-venda-abertos.admin"))
    assert not perms.can_manage_portfolios(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_read_worklist_followups_only_canonical() -> None:
    assert perms.can_read_commercial(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))
    assert not perms.can_read_commercial(_user("api-delpi.access"))
    assert not perms.can_read_commercial(_user("pedidos-venda-abertos.access"))
    assert perms.can_view_worklist(_user(perms.COMMERCIAL_WORKLIST_VIEW))
    assert not perms.can_view_worklist(_user("api-delpi.access"))
    assert perms.can_manage_followups(_user(perms.COMMERCIAL_FOLLOWUPS_MANAGE))
    assert not perms.can_manage_followups(_user("api-delpi.access"))


def test_audit_is_audit_view_or_manage() -> None:
    assert perms.can_view_audit(_user(perms.COMMERCIAL_AUDIT_VIEW))
    assert perms.can_view_audit(_user(perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE))
    assert not perms.can_view_audit(_user("api-delpi.access"))
    assert not perms.can_view_audit(_user("pedidos-venda-abertos.admin"))


def test_worklist_team_has_no_legacy_alias() -> None:
    assert perms.can_view_worklist_team(_user(perms.COMMERCIAL_WORKLIST_TEAM_VIEW))
    assert not perms.can_view_worklist_team(_user(perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE))


def test_list_portfolios_permissions_include_team_and_manage_only() -> None:
    assert perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS == (
        perms.COMMERCIAL_ACCOUNTS_TEAM_VIEW,
        perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE,
    )
    assert "api-delpi.access" not in perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS
    assert "pedidos-venda-abertos.admin" not in perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS

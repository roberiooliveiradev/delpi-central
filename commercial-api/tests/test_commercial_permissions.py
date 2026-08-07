"""Testes de capacidades RBAC commercial-api (G2–G4) — codes EN + aliases."""

from __future__ import annotations

from types import SimpleNamespace

from commercial_app.application.security import commercial_permissions as perms


def _user(*codes: str) -> SimpleNamespace:
    return SimpleNamespace(permissions=list(codes), roles=[], is_superadmin=False)


def test_analytics_accepts_commercial_and_dashboard_aliases() -> None:
    assert perms.can_view_analytics(_user(perms.COMMERCIAL_ANALYTICS_VIEW))
    assert perms.can_view_analytics(_user(perms.DASHBOARD_COMMERCIAL_VIEW))
    assert perms.can_view_analytics(_user(perms.API_DELPI_ACCESS))
    assert not perms.can_view_analytics(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_proposals_canonical_en_and_pt_legacy_alias() -> None:
    assert perms.COMMERCIAL_PROPOSALS_VIEW == "commercial.proposals.view"
    assert perms.COMMERCIAL_PROPOSALS_EXPORT == "commercial.proposals.export"
    assert perms.can_view_proposals(_user(perms.COMMERCIAL_PROPOSALS_VIEW))
    assert perms.can_view_proposals(_user(perms.COMMERCIAL_PROPOSTAS_VIEW_LEGACY))
    assert perms.can_view_proposals(_user(perms.PROPOSTAS_COMERCIAIS_VIEW))
    assert perms.can_export_proposals(_user(perms.COMMERCIAL_PROPOSALS_EXPORT))
    assert perms.can_export_proposals(_user(perms.COMMERCIAL_PROPOSTAS_EXPORT_LEGACY))
    assert not perms.can_view_proposals(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_team_scope_is_team_view_or_manage_without_pva_access_alias() -> None:
    assert perms.can_use_team_scope(_user(perms.COMMERCIAL_ACCOUNTS_TEAM_VIEW))
    assert perms.can_use_team_scope(_user(perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE))
    assert perms.can_use_team_scope(_user(perms.PEDIDOS_VENDA_ABERTOS_ADMIN))
    assert not perms.can_view_accounts_team(_user(perms.PEDIDOS_VENDA_ABERTOS_ACCESS))
    assert not perms.can_use_team_scope(_user(perms.COMMERCIAL_ACCOUNTS_VIEW))


def test_worklist_team_has_no_legacy_alias() -> None:
    assert perms.can_view_worklist_team(_user(perms.COMMERCIAL_WORKLIST_TEAM_VIEW))
    assert not perms.can_view_worklist_team(_user(perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE))


def test_list_portfolios_permissions_include_team_and_manage() -> None:
    assert perms.COMMERCIAL_ACCOUNTS_TEAM_VIEW in perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS
    assert perms.COMMERCIAL_SELLER_PORTFOLIOS_MANAGE in perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS
    assert perms.API_DELPI_ACCESS in perms.COMMERCIAL_LIST_PORTFOLIOS_PERMISSIONS

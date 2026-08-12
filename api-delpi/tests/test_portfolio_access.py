"""Escopo de carteira — manage | team.view = consolidado (alinhado commercial-api)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from app.interface.http.routes.pedidos_venda_abertos import portfolio_access as pa


def _user(*codes: str) -> SimpleNamespace:
    return SimpleNamespace(id="u1", permissions=list(codes), roles=[])


def test_unrestricted_seller_portfolios_manage() -> None:
    with patch.object(pa, "get_current_user", return_value=_user("commercial.seller-portfolios.manage")):
        assert pa.is_portfolio_unrestricted() is True
        assert pa.is_portfolio_admin() is True


def test_unrestricted_includes_team_view() -> None:
    with patch.object(pa, "get_current_user", return_value=_user("commercial.accounts.team.view")):
        assert pa.is_portfolio_unrestricted() is True
        assert pa.can_filter_by_seller_id() is True
        assert pa.is_portfolio_admin() is False


def test_api_delpi_access_does_not_unrestrict() -> None:
    with patch.object(pa, "get_current_user", return_value=_user("api-delpi.access")):
        assert pa.is_portfolio_unrestricted() is False
        assert pa.is_portfolio_admin() is False
        assert pa.can_filter_by_seller_id() is False


def test_pva_admin_does_not_unrestrict() -> None:
    with patch.object(pa, "get_current_user", return_value=_user("pedidos-venda-abertos.admin")):
        assert pa.is_portfolio_unrestricted() is False
        assert pa.is_portfolio_admin() is False


def test_accounts_view_alone_no_team_filter() -> None:
    with patch.object(pa, "get_current_user", return_value=_user("commercial.accounts.view")):
        assert pa.is_portfolio_unrestricted() is False
        assert pa.can_filter_by_seller_id() is False


def test_current_user_id_prefers_id_then_sub() -> None:
    with patch.object(
        pa,
        "get_current_user",
        return_value=SimpleNamespace(id="", sub="kc-sub-1", user_id="x"),
    ):
        assert pa.current_user_id() == "kc-sub-1"

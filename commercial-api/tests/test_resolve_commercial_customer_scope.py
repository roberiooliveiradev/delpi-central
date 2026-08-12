"""Escopo de clientes por membership (commercial-api)."""

from __future__ import annotations

from unittest.mock import MagicMock

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    ResolveCommercialCustomerScopeService,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)


def _portfolio(**kwargs) -> SellerPortfolio:
    defaults = dict(
        id="p1",
        user_id="u1",
        display_name="Sul",
        active=True,
        customers=(
            SellerCustomerAssignment("100", "01", "A"),
            SellerCustomerAssignment("200", "01", "B"),
        ),
        members=(),
    )
    defaults.update(kwargs)
    return SellerPortfolio(**defaults)


def test_member_scope_filters_to_portfolio_customers() -> None:
    repo = MagicMock()
    repo.list_by_user_id.return_value = [_portfolio()]
    service = ResolveCommercialCustomerScopeService(repo)

    scope = service.execute(user_id="u1", unrestricted=False)
    assert not scope.unrestricted
    assert scope.allows("100", "01")
    assert not scope.allows("999", "01")

    filtered = service.filter_pairs(
        scope,
        [("100", "01"), ("999", "01"), ("200", "01")],
    )
    assert filtered == [("100", "01"), ("200", "01")]


def test_unrestricted_scope_allows_any_customer() -> None:
    repo = MagicMock()
    service = ResolveCommercialCustomerScopeService(repo)
    scope = service.execute(user_id="admin", unrestricted=True)
    assert scope.unrestricted
    assert scope.allows("999", "01")
    repo.list_by_user_id.assert_not_called()


def test_manage_and_team_view_are_both_unrestricted() -> None:
    """manage e team.view (unrestricted=True no caller) não leem membership."""
    repo = MagicMock()
    service = ResolveCommercialCustomerScopeService(repo)
    for label in ("manage", "team.view"):
        scope = service.execute(user_id=f"user-{label}", unrestricted=True)
        assert scope.unrestricted, label
        assert scope.allowed_customers is None, label
    repo.list_by_user_id.assert_not_called()


def test_member_without_portfolios_is_empty() -> None:
    repo = MagicMock()
    repo.list_by_user_id.return_value = []
    service = ResolveCommercialCustomerScopeService(repo)
    scope = service.execute(user_id="u1", unrestricted=False)
    assert not scope.unrestricted
    assert scope.allowed_customers == frozenset()
    assert not scope.allows("100", "01")


def test_portfolio_id_filter_rejects_outside_membership() -> None:
    repo = MagicMock()
    repo.list_by_user_id.return_value = [_portfolio(id="p1")]
    service = ResolveCommercialCustomerScopeService(repo)
    try:
        service.execute(user_id="u1", unrestricted=False, portfolio_id="other")
        assert False, "expected PermissionError"
    except PermissionError as exc:
        assert "participa" in str(exc).lower()
    repo.get_by_id.assert_not_called()


def test_portfolio_id_filter_allows_owned_portfolio_for_member() -> None:
    """Usuário comum multi-carteira pode filtrar uma carteira própria."""
    owned = _portfolio(id="p-own", customers=(SellerCustomerAssignment("100", "01", "A"),))
    other = _portfolio(
        id="p-other",
        customers=(SellerCustomerAssignment("200", "01", "B"),),
    )
    repo = MagicMock()
    repo.list_by_user_id.return_value = [owned, other]
    service = ResolveCommercialCustomerScopeService(repo)

    scope = service.execute(user_id="u1", unrestricted=False, portfolio_id="p-own")
    assert not scope.unrestricted
    assert scope.portfolio_id == "p-own"
    assert scope.allows("100", "01")
    assert not scope.allows("200", "01")
    repo.get_by_id.assert_not_called()


def test_portfolio_id_filter_scopes_to_portfolio_customers() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = _portfolio(id="p-team")
    service = ResolveCommercialCustomerScopeService(repo)
    scope = service.execute(user_id="mgr", unrestricted=True, portfolio_id="p-team")
    assert not scope.unrestricted
    assert scope.allows("100", "01")
    assert not scope.allows("999", "01")
    repo.list_by_user_id.assert_not_called()


def test_ensure_allows_raises_outside_portfolio() -> None:
    repo = MagicMock()
    repo.list_by_user_id.return_value = [_portfolio()]
    service = ResolveCommercialCustomerScopeService(repo)
    scope = service.execute(user_id="u1", unrestricted=False)
    try:
        service.ensure_allows(scope, customer_code="999", customer_store="01")
        assert False, "expected LookupError"
    except LookupError as exc:
        assert "carteira" in str(exc).lower()


def test_open_orders_without_portfolio_becomes_unrestricted() -> None:
    repo = MagicMock()
    repo.list_by_user_id.return_value = []
    service = ResolveCommercialCustomerScopeService(repo)
    scope = service.execute(user_id="u1", unrestricted=False)
    assert scope.empty_portfolio is True
    open_orders = scope.for_open_orders()
    assert open_orders.unrestricted is True
    assert open_orders.empty_portfolio is False
    assert open_orders.allows("999", "01")


def test_open_orders_keeps_membership_filter() -> None:
    repo = MagicMock()
    repo.list_by_user_id.return_value = [_portfolio()]
    service = ResolveCommercialCustomerScopeService(repo)
    scope = service.execute(user_id="u1", unrestricted=False).for_open_orders()
    assert not scope.unrestricted
    assert scope.allows("100", "01")
    assert not scope.allows("999", "01")

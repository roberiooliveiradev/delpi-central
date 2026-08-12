from unittest.mock import MagicMock

from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)
from app.infrastructure.persistence.plugins.repositories.pedidos_venda_abertos.dual_read_seller_portfolio_repository import (
    DualReadSellerPortfolioRepository,
)


def _portfolio(portfolio_id: str, user_id: str = "u1") -> SellerPortfolio:
    return SellerPortfolio(
        id=portfolio_id,
        user_id=user_id,
        display_name="Vendedor",
        active=True,
        customers=(SellerCustomerAssignment("100", "01", "A"),),
    )


def test_dual_read_prefers_commercial_get_by_id() -> None:
    commercial = MagicMock()
    legacy = MagicMock()
    commercial.get_by_id.return_value = _portfolio("c1")
    legacy.get_by_id.return_value = _portfolio("l1")
    repo = DualReadSellerPortfolioRepository(
        commercial=commercial, legacy=legacy, write_source="commercial"
    )
    found = repo.get_by_id("c1")
    assert found is not None and found.id == "c1"
    legacy.get_by_id.assert_not_called()


def test_dual_read_falls_back_to_legacy_get_by_id() -> None:
    commercial = MagicMock()
    legacy = MagicMock()
    commercial.get_by_id.return_value = None
    legacy.get_by_id.return_value = _portfolio("l1")
    repo = DualReadSellerPortfolioRepository(
        commercial=commercial, legacy=legacy, write_source="commercial"
    )
    found = repo.get_by_id("l1")
    assert found is not None and found.id == "l1"
    commercial.get_by_id.assert_called_once_with("l1")
    legacy.get_by_id.assert_called_once_with("l1")


def test_dual_read_get_by_user_id_falls_back() -> None:
    commercial = MagicMock()
    legacy = MagicMock()
    commercial.get_by_user_id.return_value = None
    legacy.get_by_user_id.return_value = _portfolio("l1", user_id="u-legacy")
    repo = DualReadSellerPortfolioRepository(
        commercial=commercial, legacy=legacy, write_source="commercial"
    )
    found = repo.get_by_user_id("u-legacy")
    assert found is not None and found.user_id == "u-legacy"


def test_dual_read_list_by_user_id_prefers_commercial() -> None:
    commercial = MagicMock()
    legacy = MagicMock()
    commercial.list_by_user_id.return_value = [_portfolio("c1"), _portfolio("c2")]
    legacy.list_by_user_id.return_value = [_portfolio("l1")]
    repo = DualReadSellerPortfolioRepository(
        commercial=commercial, legacy=legacy, write_source="commercial"
    )
    found = repo.list_by_user_id("u1", active_only=True)
    assert [p.id for p in found] == ["c1", "c2"]
    commercial.list_by_user_id.assert_called_once_with("u1", active_only=True)
    legacy.list_by_user_id.assert_not_called()


def test_dual_read_list_by_user_id_falls_back_to_legacy() -> None:
    commercial = MagicMock()
    legacy = MagicMock()
    commercial.list_by_user_id.return_value = []
    legacy.list_by_user_id.return_value = [_portfolio("l1", user_id="u-legacy")]
    repo = DualReadSellerPortfolioRepository(
        commercial=commercial, legacy=legacy, write_source="commercial"
    )
    found = repo.list_by_user_id("u-legacy", active_only=True)
    assert len(found) == 1 and found[0].id == "l1"
    commercial.list_by_user_id.assert_called_once_with("u-legacy", active_only=True)
    legacy.list_by_user_id.assert_called_once_with("u-legacy", active_only=True)

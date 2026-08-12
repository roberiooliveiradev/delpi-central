from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)


def test_owner_user_id_prefers_members_owner_over_user_id_field() -> None:
    portfolio = SellerPortfolio(
        id="p1",
        user_id="stale-mirror",
        display_name="Carteira",
        active=True,
        customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        members=(
            SellerPortfolioMember(user_id="real-owner", role="owner"),
            SellerPortfolioMember(user_id="helper", role="member"),
        ),
    )
    assert portfolio.owner_user_id == "real-owner"


def test_owner_user_id_falls_back_to_user_id_without_owner_member() -> None:
    portfolio = SellerPortfolio(
        id="p2",
        user_id="mirror-owner",
        display_name="Carteira",
        active=True,
        customers=(),
        members=(SellerPortfolioMember(user_id="helper", role="member"),),
    )
    assert portfolio.owner_user_id == "mirror-owner"


def test_owner_user_id_falls_back_when_members_empty() -> None:
    portfolio = SellerPortfolio(
        id="p3",
        user_id="solo",
        display_name="Carteira",
        active=True,
        customers=(),
    )
    assert portfolio.owner_user_id == "solo"

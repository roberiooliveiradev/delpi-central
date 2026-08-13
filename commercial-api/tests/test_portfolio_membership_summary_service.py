from __future__ import annotations

from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.services.portfolio_membership_summary_service import (
    portfolio_membership_summary,
    portfolio_profile_summary_dict,
)


def test_portfolio_membership_summary_owner_with_customers() -> None:
    portfolio = SellerPortfolio(
        id="p1",
        user_id="u1",
        display_name="Sul",
        active=True,
        customers=(
            SellerCustomerAssignment("0001", "01", "Acme"),
            SellerCustomerAssignment("0002", "01", "Beta"),
        ),
        members=(
            SellerPortfolioMember(user_id="u1", role="owner"),
            SellerPortfolioMember(user_id="u2", role="member"),
        ),
    )
    summary = portfolio_membership_summary(portfolio, viewer_user_id="u1")
    assert summary["role"] == "owner"
    assert summary["customer_count"] == 2
    assert summary["member_count"] == 2

    as_member = portfolio_membership_summary(portfolio, viewer_user_id="u2")
    assert as_member["role"] == "member"
    assert as_member["customer_count"] == 2


def test_portfolio_profile_summary_dict_shape() -> None:
    portfolio = SellerPortfolio(
        id="p1",
        user_id="u1",
        display_name="Sul",
        active=True,
        customers=(SellerCustomerAssignment("0001", "01", "Acme"),),
        members=(SellerPortfolioMember(user_id="u1", role="owner"),),
    )
    row = portfolio_profile_summary_dict(portfolio, viewer_user_id="u1")
    assert row["id"] == "p1"
    assert row["name"] == "Sul"
    assert row["role"] == "owner"
    assert row["customer_count"] == 1
    assert row["member_count"] == 1

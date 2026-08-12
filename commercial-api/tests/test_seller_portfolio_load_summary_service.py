from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.services.seller_portfolio_load_summary_service import (
    SellerPortfolioLoadSummaryService,
)


def _portfolio(
    *,
    portfolio_id: str,
    name: str,
    customers: tuple[SellerCustomerAssignment, ...],
    members: tuple[SellerPortfolioMember, ...] | None = None,
    active: bool = True,
) -> SellerPortfolio:
    resolved_members = members or (
        SellerPortfolioMember(user_id=f"u-{portfolio_id}", role="owner"),
    )
    return SellerPortfolio(
        id=portfolio_id,
        user_id=resolved_members[0].user_id if resolved_members else f"u-{portfolio_id}",
        display_name=name,
        active=active,
        customers=customers,
        members=resolved_members,
    )


def test_load_summary_counts_customers_and_members() -> None:
    service = SellerPortfolioLoadSummaryService()
    summary = service.summarize(
        [
            _portfolio(
                portfolio_id="p1",
                name="Sul",
                customers=(
                    SellerCustomerAssignment("100", "01", "A"),
                    SellerCustomerAssignment("200", "01", "B"),
                    SellerCustomerAssignment("100", "01", "A"),  # dup
                ),
                members=(
                    SellerPortfolioMember(user_id="ana", role="owner"),
                    SellerPortfolioMember(user_id="pedro", role="member"),
                ),
            ),
            _portfolio(
                portfolio_id="p2",
                name="Norte",
                customers=(SellerCustomerAssignment("300", "01", "C"),),
                members=(SellerPortfolioMember(user_id="bruno", role="owner"),),
            ),
        ]
    )

    by_id = {item.id: item for item in summary.portfolios}
    assert by_id["p1"].customer_count == 2
    assert by_id["p1"].member_count == 2
    assert by_id["p1"].open_value is None
    assert by_id["p1"].attention_count is None
    assert by_id["p2"].customer_count == 1
    assert by_id["p2"].member_count == 1
    assert summary.totvs_metrics.available is False
    assert summary.totvs_metrics.reason == "open_orders_aggregation_not_wired"


def test_load_summary_aggregates_by_person_with_customer_union() -> None:
    service = SellerPortfolioLoadSummaryService()
    summary = service.summarize(
        [
            _portfolio(
                portfolio_id="p1",
                name="Sul",
                customers=(
                    SellerCustomerAssignment("100", "01", "A"),
                    SellerCustomerAssignment("200", "01", "B"),
                ),
                members=(
                    SellerPortfolioMember(user_id="ana", role="owner"),
                    SellerPortfolioMember(user_id="pedro", role="member"),
                ),
            ),
            _portfolio(
                portfolio_id="p2",
                name="Especial",
                customers=(
                    SellerCustomerAssignment("100", "01", "A"),
                    SellerCustomerAssignment("400", "01", "D"),
                ),
                members=(SellerPortfolioMember(user_id="ana", role="owner"),),
            ),
        ]
    )

    by_user = {item.user_id: item for item in summary.by_person}
    assert set(by_user) == {"ana", "pedro"}
    assert by_user["ana"].portfolio_count == 2
    assert list(by_user["ana"].portfolio_ids) == ["p1", "p2"]
    # União: 100, 200, 400
    assert by_user["ana"].customer_count == 3
    assert by_user["pedro"].portfolio_count == 1
    assert by_user["pedro"].customer_count == 2
    assert by_user["ana"].open_value is None


def test_load_summary_falls_back_to_owner_when_members_empty() -> None:
    service = SellerPortfolioLoadSummaryService()
    portfolio = SellerPortfolio(
        id="p1",
        user_id="owner-1",
        display_name="Legado",
        active=True,
        customers=(SellerCustomerAssignment("100", "01", "A"),),
        members=(),
    )
    summary = service.summarize([portfolio])
    assert summary.portfolios[0].member_count == 1
    assert summary.by_person[0].user_id == "owner-1"

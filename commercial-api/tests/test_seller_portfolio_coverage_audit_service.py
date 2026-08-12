from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)
from commercial_app.domain.services.seller_portfolio_coverage_audit_service import (
    SellerPortfolioCoverageAuditService,
)


def _portfolio(
    *,
    portfolio_id: str,
    name: str,
    customers: tuple[SellerCustomerAssignment, ...],
    active: bool = True,
) -> SellerPortfolio:
    return SellerPortfolio(
        id=portfolio_id,
        user_id=f"u-{portfolio_id}",
        display_name=name,
        active=active,
        customers=customers,
        members=(SellerPortfolioMember(user_id=f"u-{portfolio_id}", role="owner"),),
    )


def test_audit_detects_overlapping_customers_across_active_portfolios() -> None:
    service = SellerPortfolioCoverageAuditService()
    audit = service.audit_active_portfolios(
        [
            _portfolio(
                portfolio_id="p1",
                name="Carteira A",
                customers=(
                    SellerCustomerAssignment("100", "01", "Cliente 100"),
                    SellerCustomerAssignment("200", "01", "Cliente 200"),
                ),
            ),
            _portfolio(
                portfolio_id="p2",
                name="Carteira B",
                customers=(
                    SellerCustomerAssignment("100", "01", "Cliente 100"),
                    SellerCustomerAssignment("300", "01", "Cliente 300"),
                ),
            ),
            _portfolio(
                portfolio_id="p3",
                name="Inativa",
                active=False,
                customers=(SellerCustomerAssignment("100", "01", "Cliente 100"),),
            ),
        ]
    )

    assert audit.overlapping_count == 1
    assert audit.overlapping[0].customer_code == "100"
    assert audit.overlapping[0].customer_store == "01"
    assert list(audit.overlapping[0].portfolio_ids) == ["p1", "p2"]
    assert [item.id for item in audit.portfolios_with_overlap] == ["p1", "p2"]
    assert audit.gap.available is False
    assert audit.gap.reason == "customer_universe_not_available"


def test_audit_ignores_duplicate_customer_within_same_portfolio() -> None:
    service = SellerPortfolioCoverageAuditService()
    audit = service.audit_active_portfolios(
        [
            _portfolio(
                portfolio_id="p1",
                name="A",
                customers=(
                    SellerCustomerAssignment("100", "01", "Cliente"),
                    SellerCustomerAssignment("100", "01", "Cliente"),
                ),
            ),
            _portfolio(
                portfolio_id="p2",
                name="B",
                customers=(SellerCustomerAssignment("200", "01", "Outro"),),
            ),
        ]
    )
    assert audit.overlapping_count == 0
    assert audit.portfolios_with_overlap == ()


def test_find_other_active_portfolios_for_customer() -> None:
    service = SellerPortfolioCoverageAuditService()
    portfolios = [
        _portfolio(
            portfolio_id="p1",
            name="A",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
        _portfolio(
            portfolio_id="p2",
            name="B",
            customers=(SellerCustomerAssignment("100", "01", "Cliente"),),
        ),
    ]
    others = service.find_other_active_portfolios_for_customer(
        portfolios,
        customer_code="100",
        customer_store="01",
        exclude_portfolio_id="p1",
    )
    assert len(others) == 1
    assert others[0].id == "p2"
    warning = service.build_link_overlap_warning(others)
    assert warning is not None
    assert warning.code == "customer_in_other_portfolios"
    assert "outra" in warning.message.lower()

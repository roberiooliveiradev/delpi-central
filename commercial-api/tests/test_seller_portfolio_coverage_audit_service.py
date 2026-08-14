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


def test_audit_gap_uses_open_orders_universe() -> None:
    from commercial_app.domain.ports.open_orders_metrics_port import CustomerOpenOrderMetric

    service = SellerPortfolioCoverageAuditService()
    audit = service.audit_active_portfolios(
        [
            _portfolio(
                portfolio_id="p1",
                name="Carteira A",
                customers=(SellerCustomerAssignment("100", "01", "Cliente 100"),),
            ),
        ],
        universe_metrics=[
            CustomerOpenOrderMetric("100", "01", "Cliente 100", 50.0, False),
            CustomerOpenOrderMetric("999", "01", "Sem cobertura", 900.0, True),
            CustomerOpenOrderMetric("888", "01", "Outro", 100.0, False),
        ],
        uncovered_list_cap=10,
    )
    assert audit.gap.available is True
    assert audit.gap.universe == "open_orders"
    assert audit.gap.uncovered_count == 2
    assert [item.customer_code for item in audit.gap.uncovered] == ["999", "888"]
    assert audit.gap.uncovered[0].open_value == 900.0


def test_audit_gap_treats_store_1_and_01_as_same_coverage_key() -> None:
    """SC5 pode devolver loja `1`; SA1/vínculo usa `01` — não gerar gap falso."""
    from commercial_app.domain.ports.open_orders_metrics_port import CustomerOpenOrderMetric
    from commercial_app.domain.services.seller_portfolio_coverage_audit_service import (
        customer_coverage_key,
        normalize_customer_store,
    )

    assert normalize_customer_store("1") == "01"
    assert normalize_customer_store("01") == "01"
    assert customer_coverage_key("000597", "1") == customer_coverage_key("000597", "01")

    service = SellerPortfolioCoverageAuditService()
    audit = service.audit_active_portfolios(
        [
            _portfolio(
                portfolio_id="p1",
                name="Carteira A",
                customers=(SellerCustomerAssignment("000597", "01", "CONDVOLT"),),
            ),
        ],
        universe_metrics=[
            CustomerOpenOrderMetric("000597", "1", "CONDUOLI", 338.5, False),
        ],
        uncovered_list_cap=10,
    )
    assert audit.gap.available is True
    assert audit.gap.uncovered_count == 0


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


def test_lookup_shared_customer_memberships_batch_only_returns_shared() -> None:
    service = SellerPortfolioCoverageAuditService()
    portfolios = [
        _portfolio(
            portfolio_id="p1",
            name="Sul",
            customers=(
                SellerCustomerAssignment("100", "01", "Shared"),
                SellerCustomerAssignment("200", "01", "Solo"),
            ),
        ),
        _portfolio(
            portfolio_id="p2",
            name="Ana",
            customers=(SellerCustomerAssignment("100", "01", "Shared"),),
        ),
    ]
    items = service.lookup_shared_customer_memberships(
        portfolios,
        [("100", "01"), ("200", "01"), ("999", "01")],
    )
    assert len(items) == 1
    assert items[0].customer_code == "100"
    assert items[0].shared is True
    assert [ref.display_name for ref in items[0].portfolios] == ["Sul", "Ana"]

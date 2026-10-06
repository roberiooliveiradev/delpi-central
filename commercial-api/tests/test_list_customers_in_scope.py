"""Unit — ListCustomersInScopeService + use case."""

from __future__ import annotations

from unittest.mock import MagicMock

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.list_customers_in_scope import (
    ListCustomersInScopeUseCase,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)
from commercial_app.domain.ports.open_orders_metrics_port import CustomerOpenOrderMetric
from commercial_app.domain.services.list_customers_in_scope_service import (
    ListCustomersInScopeService,
)


def test_service_left_joins_metrics_and_zeros_missing() -> None:
    service = ListCustomersInScopeService()
    result = service.build(
        [
            SellerCustomerAssignment("100", "01", "Alpha"),
            SellerCustomerAssignment("200", "01", "Beta"),
            SellerCustomerAssignment("100", "01", "Alpha Dup"),
        ],
        [
            CustomerOpenOrderMetric(
                customer_code="100",
                customer_store="01",
                customer_name="Alpha TOTVS",
                open_value=1500.0,
                has_overdue=True,
            )
        ],
    )
    assert result.customer_count == 2
    by_code = {item.customer_code: item for item in result.items}
    assert by_code["100"].open_value == 1500.0
    assert by_code["100"].has_overdue is True
    assert by_code["100"].has_open_orders is True
    assert by_code["100"].customer_name == "Alpha"
    assert by_code["200"].open_value == 0.0
    assert by_code["200"].has_overdue is False
    assert by_code["200"].has_open_orders is False


def test_service_keeps_one_row_per_center_and_pair_fallback() -> None:
    service = ListCustomersInScopeService()
    result = service.build(
        [
            SellerCustomerAssignment("000001", "01", "WEG", customer_center="1100"),
            SellerCustomerAssignment("000001", "01", "WEG", customer_center="1200"),
            SellerCustomerAssignment("000001", "10", "Sem centro"),
        ],
        [
            CustomerOpenOrderMetric(
                customer_code="000001",
                customer_store="01",
                customer_name="WEG",
                open_value=900.0,
                has_overdue=True,
            )
        ],
    )
    assert result.customer_count == 3
    centers = {
        (item.customer_store, item.customer_center): item.open_value for item in result.items
    }
    assert centers[("01", "1100")] == 0.0
    assert centers[("01", "1200")] == 0.0
    assert centers[("10", None)] == 0.0


def test_use_case_membership_without_open_orders_still_listed() -> None:
    repo = MagicMock()
    repo.list_portfolios.return_value = [
        SellerPortfolio(
            id="p1",
            user_id="u1",
            display_name="Sul",
            active=True,
            customers=(
                SellerCustomerAssignment("000204", "01", "AHT"),
                SellerCustomerAssignment("000100", "01", "Com aberto"),
            ),
        )
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = [
        CustomerOpenOrderMetric(
            customer_code="000100",
            customer_store="01",
            customer_name="Com aberto",
            open_value=99.0,
            has_overdue=False,
        )
    ]
    use_case = ListCustomersInScopeUseCase(
        repository=repo,
        open_orders_metrics=metrics,
    )
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("000204", "01"), ("000100", "01")}),
        portfolio_id="p1",
    )
    payload = use_case.execute(scope)
    codes = {item["customer_code"] for item in payload["items"]}
    assert codes == {"000204", "000100"}
    by_code = {item["customer_code"]: item for item in payload["items"]}
    assert by_code["000204"]["open_value"] == 0.0
    assert by_code["000204"]["has_open_orders"] is False
    assert by_code["000100"]["open_value"] == 99.0
    assert payload["summary"]["customer_count"] == 2
    metrics.list_customer_metrics.assert_called_once()
    called_keys = metrics.list_customer_metrics.call_args[0][0]
    assert ("000204", "01") in called_keys
    assert None not in (called_keys if isinstance(called_keys, list) else [])


def test_use_case_empty_portfolio() -> None:
    repo = MagicMock()
    metrics = MagicMock()
    use_case = ListCustomersInScopeUseCase(repository=repo, open_orders_metrics=metrics)
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset(),
        empty_portfolio=True,
        message="Sua carteira ainda não possui clientes vinculados.",
    )
    payload = use_case.execute(scope)
    assert payload["items"] == []
    assert payload["empty_portfolio"] is True
    assert "vinculados" in (payload["message"] or "")
    metrics.list_customer_metrics.assert_not_called()


def test_use_case_excludes_inactive_linked_customers_when_port_wired() -> None:
    """Cliente vinculado que inativou (A1_MSBLQL='1') sai da população
    operacional da carteira; o vínculo persistido não é alterado."""
    from commercial_app.domain.ports.customer_eligibility_port import (
        CustomerEligibility,
        CustomerEligibilityPort,
    )

    class _Eligibility(CustomerEligibilityPort):
        def lookup(self, customers):
            return {
                ("000006", "01"): CustomerEligibility(exists=True, active=False),
                ("000100", "01"): CustomerEligibility(exists=True, active=True),
            }

    repo = MagicMock()
    repo.list_portfolios.return_value = [
        SellerPortfolio(
            id="p1",
            user_id="u1",
            display_name="Sul",
            active=True,
            customers=(
                SellerCustomerAssignment("000006", "01", "AGC"),
                SellerCustomerAssignment("000100", "01", "Com aberto"),
            ),
        )
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = []
    use_case = ListCustomersInScopeUseCase(
        repository=repo,
        open_orders_metrics=metrics,
        customer_eligibility=_Eligibility(),
    )
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("000006", "01"), ("000100", "01")}),
        portfolio_id="p1",
    )
    payload = use_case.execute(scope)
    codes = {item["customer_code"] for item in payload["items"]}
    assert codes == {"000100"}
    assert payload["summary"]["customer_count"] == 1
    # Métricas só consultadas para clientes elegíveis.
    called_keys = metrics.list_customer_metrics.call_args[0][0]
    assert ("000006", "01") not in called_keys
    # Vínculo histórico intacto — nenhuma escrita de remoção.
    repo.remove_customer.assert_not_called()


def test_use_case_unrestricted_unions_all_portfolios() -> None:
    repo = MagicMock()
    repo.list_portfolios.return_value = [
        SellerPortfolio(
            id="p1",
            user_id="a",
            display_name="A",
            active=True,
            customers=(SellerCustomerAssignment("1", "01", "One"),),
        ),
        SellerPortfolio(
            id="p2",
            user_id="b",
            display_name="B",
            active=True,
            customers=(SellerCustomerAssignment("2", "01", "Two"),),
        ),
    ]
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = []
    use_case = ListCustomersInScopeUseCase(repository=repo, open_orders_metrics=metrics)
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    payload = use_case.execute(scope)
    codes = {item["customer_code"] for item in payload["items"]}
    assert codes == {"1", "2"}


_CASSIO_PORTFOLIO_ID = "8b21cee0-b470-4ac6-b900-733580c3ef76"


def _cassio_portfolio() -> SellerPortfolio:
    return SellerPortfolio(
        id=_CASSIO_PORTFOLIO_ID,
        user_id="cassio",
        display_name="Carteira NN - Cassio",
        active=True,
        customers=(
            SellerCustomerAssignment("000198", "1", "FAMAC INDUSTRIA DE MAQUINAS LTDA"),
            SellerCustomerAssignment("000204", "01", "AHT COOLING SYSTEMS"),
            SellerCustomerAssignment("000300", "01", "CLIENTE BLOQUEADO"),
        ),
    )


def _exact_sa1_eligibility():
    """SA1 casa A1_COD + A1_LOJA por igualdade exata (como o enrichment)."""
    from commercial_app.domain.ports.customer_eligibility_port import (
        CustomerEligibility,
        CustomerEligibilityPort,
    )

    sa1 = {
        ("000198", "1"): CustomerEligibility(exists=True, active=True),
        ("000204", "01"): CustomerEligibility(exists=True, active=True),
        ("000300", "01"): CustomerEligibility(exists=True, active=False),
    }

    class _ExactSa1(CustomerEligibilityPort):
        def __init__(self) -> None:
            self.requested: list[tuple[str, str]] = []

        def lookup(self, customers):
            self.requested.extend(customers)
            return {key: sa1[key] for key in customers if key in sa1}

    return _ExactSa1()


def _cassio_use_case(eligibility):
    repo = MagicMock()
    repo.list_portfolios.return_value = [_cassio_portfolio()]
    repo.list_by_user_id.return_value = [_cassio_portfolio()]
    repo.get_by_id.return_value = _cassio_portfolio()
    metrics = MagicMock()
    metrics.list_customer_metrics.return_value = [
        CustomerOpenOrderMetric("000198", "1", "FAMAC", 120.0, True),
    ]
    use_case = ListCustomersInScopeUseCase(
        repository=repo,
        open_orders_metrics=metrics,
        customer_eligibility=eligibility,
    )
    return repo, metrics, use_case


def _assert_cassio_payload(payload) -> None:
    pairs = {(item["customer_code"], item["customer_store"]) for item in payload["items"]}
    assert pairs == {("000198", "1"), ("000204", "01")}
    famac = next(item for item in payload["items"] if item["customer_code"] == "000198")
    assert famac["open_value"] == 120.0
    assert famac["has_overdue"] is True


def test_unpadded_totvs_store_stays_in_member_scope() -> None:
    """Regressão FAMAC: loja SA1 `1` não vira `01` antes do allowlist/SA1."""
    from commercial_app.application.services.resolve_commercial_customer_scope_service import (
        ResolveCommercialCustomerScopeService,
    )

    eligibility = _exact_sa1_eligibility()
    repo, metrics, use_case = _cassio_use_case(eligibility)
    scope = ResolveCommercialCustomerScopeService(repo).execute(
        user_id="cassio",
        unrestricted=False,
    )

    _assert_cassio_payload(use_case.execute(scope))
    assert ("000198", "1") in eligibility.requested
    assert ("000198", "01") not in eligibility.requested
    called_keys = metrics.list_customer_metrics.call_args[0][0]
    assert ("000198", "1") in called_keys
    assert ("000300", "01") not in called_keys


def test_unpadded_totvs_store_stays_with_portfolio_filter() -> None:
    """seller_id/portfolio_id da carteira (membro e team/manage) mantém `000198/1`."""
    from commercial_app.application.services.resolve_commercial_customer_scope_service import (
        ResolveCommercialCustomerScopeService,
    )

    for unrestricted in (False, True):
        eligibility = _exact_sa1_eligibility()
        repo, _metrics, use_case = _cassio_use_case(eligibility)
        scope = ResolveCommercialCustomerScopeService(repo).execute(
            user_id="cassio",
            unrestricted=unrestricted,
            portfolio_ids=[_CASSIO_PORTFOLIO_ID],
        )
        _assert_cassio_payload(use_case.execute(scope))
        assert ("000198", "01") not in eligibility.requested


def test_unpadded_totvs_store_stays_in_unrestricted_union() -> None:
    eligibility = _exact_sa1_eligibility()
    _repo, _metrics, use_case = _cassio_use_case(eligibility)
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    _assert_cassio_payload(use_case.execute(scope))


def test_service_returns_exact_store_and_matches_metric_by_coverage() -> None:
    """Saída preserva a loja TOTVS; métrica casa `1`/`01` como cobertura."""
    service = ListCustomersInScopeService()
    result = service.build(
        [
            SellerCustomerAssignment("000198", "1", "FAMAC"),
            SellerCustomerAssignment("000269", "01", "KOMGROUP"),
        ],
        [
            CustomerOpenOrderMetric("000198", "1", "FAMAC", 50.0, False),
            CustomerOpenOrderMetric("000269", "1", "KOMGROUP", 70.0, False),
        ],
    )
    by_code = {item.customer_code: item for item in result.items}
    assert by_code["000198"].customer_store == "1"
    assert by_code["000198"].open_value == 50.0
    assert by_code["000269"].customer_store == "01"
    assert by_code["000269"].open_value == 70.0

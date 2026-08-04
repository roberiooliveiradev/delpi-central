from __future__ import annotations

from unittest.mock import MagicMock

from app.application.use_cases.pedidos_venda_abertos.enrich_portfolio_customers_use_case import (
    EnrichCustomersRequest,
    EnrichPortfolioCustomersUseCase,
)
from app.application.use_cases.pedidos_venda_abertos.manage_customer_avatar_use_case import (
    ManageCustomerAvatarUseCase,
)
from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerBilling12mRow,
    CustomerGeoRow,
)


def test_enrich_portfolio_customers_merges_geo_billing_avatar() -> None:
    enrichment_repo = MagicMock()
    enrichment_repo.fetch_customer_geo.return_value = [
        CustomerGeoRow("100", "01", "Jaraguá do Sul", "SC"),
    ]
    enrichment_repo.fetch_billing_12m.return_value = [
        CustomerBilling12mRow(
            "100",
            "01",
            "2026-07-28",
            842500.0,
            billed_recent_6m=500000.0,
            billed_prior_6m=342500.0,
        ),
    ]
    avatar_uc = MagicMock(spec=ManageCustomerAvatarUseCase)
    avatar_uc.list_keys_with_avatar.return_value = {("100", "01")}

    use_case = EnrichPortfolioCustomersUseCase(enrichment_repo, avatar_uc)
    items = use_case.execute(
        EnrichCustomersRequest(customers=[("100", "01"), ("100", "01"), ("", "01")])
    )

    assert len(items) == 1
    assert items[0].city == "Jaraguá do Sul"
    assert items[0].state == "SC"
    assert items[0].billed_12m == 842500.0
    assert items[0].billed_recent_6m == 500000.0
    assert items[0].billed_prior_6m == 342500.0
    assert items[0].billing_trend == "up"
    assert items[0].billing_trend_pct is not None
    assert items[0].billing_trend_pct > 5.0
    assert items[0].last_purchase_date == "2026-07-28"
    assert items[0].has_avatar is True
    payload = items[0].to_dict()
    assert payload["avatar_url"].endswith("/customers/100/01/avatar")
    assert payload["billing_trend"] == "up"
    assert "billed_recent_6m" in payload
    call_kwargs = enrichment_repo.fetch_billing_12m.call_args.kwargs
    assert "mid_date" in call_kwargs
    assert "start_date" in call_kwargs
    assert "end_date" in call_kwargs


def test_enrich_and_avatar_operation_ids_in_router() -> None:
    router = open(
        "app/interface/http/routes/pedidos_venda_abertos/pedidos_venda_abertos_router.py",
        encoding="utf-8",
    ).read()
    for oid in (
        "enrich_portfolio_customers",
        "list_customer_billing_series",
        "get_customer_avatar",
        "upsert_customer_avatar",
        "delete_customer_avatar",
    ):
        assert oid in router


def test_manage_avatar_rejects_empty_identity() -> None:
    repo = MagicMock()
    use_case = ManageCustomerAvatarUseCase(repository=repo)
    try:
        use_case.get_meta(customer_code="", customer_store="01")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "obrigatórios" in str(exc)

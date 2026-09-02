from __future__ import annotations

from decimal import Decimal

import pytest

from financial_app.application.services.freight_service import (
    FreightService,
    InvalidFreightQuery,
)
from financial_app.domain.errors import BranchAccessDenied, InvalidPeriod
from tests.conftest import full_user, user
from tests.fakes import FakeFinancialGateway, freight_link

PERIOD = {"issue_start": "2026-03-01", "issue_end": "2026-03-31"}


def build(links=None) -> tuple[FreightService, FakeFinancialGateway]:
    gateway = FakeFinancialGateway()
    if links is not None:
        gateway.freight_links = list(links)
    return FreightService(gateway), gateway


# ------------------------------------------------------------------ RBAC


def test_requires_the_freight_permission() -> None:
    service, _ = build()

    with pytest.raises(PermissionError):
        service.dashboard(user("financial.access"), **PERIOD)


def test_consolidated_scope_requires_both_branches() -> None:
    service, _ = build()
    partial = user(
        "financial.access", "financial.freight.view", "financial.view.filial-01"
    )

    with pytest.raises(BranchAccessDenied):
        service.dashboard(partial, **PERIOD)


def test_single_branch_is_allowed_with_its_own_permission() -> None:
    service, gateway = build()
    scoped = user(
        "financial.access", "financial.freight.view", "financial.view.filial-01"
    )

    service.dashboard(scoped, branch="01", **PERIOD)

    assert gateway.call_kwargs("fetch_purchase_freight_links")["branch"] == "01"


# -------------------------------------------------------------- validação


def test_at_least_one_date_range_is_required() -> None:
    service, _ = build()

    with pytest.raises(InvalidPeriod):
        service.dashboard(full_user())


def test_entry_range_alone_is_enough() -> None:
    service, gateway = build()

    service.dashboard(full_user(), entry_start="2026-03-01", entry_end="2026-03-31")

    forwarded = gateway.call_kwargs("fetch_purchase_freight_links")
    assert forwarded["entry_start"] == "2026-03-01"
    assert forwarded["issue_start"] is None


def test_half_open_range_is_rejected() -> None:
    service, _ = build()

    with pytest.raises(InvalidPeriod):
        service.dashboard(full_user(), issue_start="2026-03-01")


def test_inverted_range_is_rejected() -> None:
    service, _ = build()

    with pytest.raises(InvalidPeriod):
        service.dashboard(
            full_user(), issue_start="2026-03-31", issue_end="2026-03-01"
        )


def test_period_before_the_cutoff_is_rejected_with_the_reason() -> None:
    service, _ = build()

    with pytest.raises(InvalidPeriod) as error:
        service.dashboard(full_user(), issue_start="2022-01-01", issue_end="2022-12-31")

    assert "01/01/2023" in str(error.value)


def test_invalid_situation_is_rejected() -> None:
    service, _ = build()

    with pytest.raises(InvalidFreightQuery):
        service.dashboard(full_user(), situation="acima", **PERIOD)


def test_invalid_sort_field_is_rejected() -> None:
    service, _ = build()

    with pytest.raises(InvalidFreightQuery):
        service.dashboard(full_user(), sort_by="carrier_name", **PERIOD)


# ------------------------------------------------------------------ saída


def test_dashboard_maps_invoices_and_summary() -> None:
    service, _ = build()

    result = service.dashboard(full_user(), **PERIOD)

    assert result["period"]["issueStart"] == "2026-03-01"
    assert result["limits"] == {"01": "3.25", "02": "4.25"}
    assert result["summary"]["invoiceCount"] == 2
    assert result["summary"]["aboveLimitCount"] == 1
    assert result["summary"]["goodsTotal"] == "2000.00"
    assert result["summary"]["freightTotal"] == "82.50"
    assert result["summary"]["freightPercent"] == "4.13"


def test_orphan_link_is_reported_and_kept_out_of_the_totals() -> None:
    service, _ = build()

    dashboard = service.dashboard(full_user(), **PERIOD)
    inconsistencies = service.inconsistencies(full_user(), **PERIOD)

    assert dashboard["summary"]["inconsistentCount"] == 0
    assert dashboard["summary"]["invoiceCount"] == 2
    reasons = {item["reasonCode"] for item in inconsistencies["items"]}
    assert "nf_not_found" in reasons
    assert inconsistencies["totalsByReason"][0]["count"] >= 1


def test_situation_filter_narrows_the_grid() -> None:
    service, _ = build()

    above = service.dashboard(full_user(), situation="above_limit", **PERIOD)
    normal = service.dashboard(full_user(), situation="normal", **PERIOD)

    assert [item["invoiceDocument"] for item in above["items"]] == ["000000002"]
    assert [item["invoiceDocument"] for item in normal["items"]] == ["000000001"]
    assert above["summary"]["invoiceCount"] == 2, "resumo cobre o período, não a página"


def test_pagination_windows_the_result_server_side() -> None:
    links = [
        freight_link(
            invoice_document=f"{index:09d}",
            freight_document=f"9{index:08d}",
        )
        for index in range(1, 6)
    ]
    service, _ = build(links)

    first = service.dashboard(full_user(), page=1, page_size=2, **PERIOD)
    second = service.dashboard(full_user(), page=2, page_size=2, **PERIOD)

    assert first["pagination"]["totalItems"] == 5
    assert first["pagination"]["totalPages"] == 3
    assert first["pagination"]["hasNext"] is True
    assert len(first["items"]) == 2
    assert second["pagination"]["hasPrevious"] is True
    assert {item["invoiceDocument"] for item in first["items"]}.isdisjoint(
        {item["invoiceDocument"] for item in second["items"]}
    )


def test_page_beyond_the_last_falls_back_to_the_last_page() -> None:
    service, _ = build()

    result = service.dashboard(full_user(), page=99, page_size=1, **PERIOD)

    assert result["pagination"]["page"] == result["pagination"]["totalPages"]
    assert result["items"]


def test_monetary_values_travel_as_strings_to_preserve_precision() -> None:
    service, _ = build()

    item = service.dashboard(full_user(), **PERIOD)["items"][0]

    assert isinstance(item["goodsValue"], str)
    assert isinstance(item["freightTotal"], str)
    assert Decimal(item["freightPercent"]) > Decimal("0")


def test_allocation_detail_exposes_the_base_of_each_freight_document() -> None:
    service, _ = build(
        [
            freight_link(invoice_document="000000001", invoice_goods_value=1000.0),
            freight_link(invoice_document="000000002", invoice_goods_value=3000.0),
        ]
    )

    items = service.dashboard(full_user(), **PERIOD)["items"]
    allocation = items[0]["allocations"][0]

    assert allocation["allocationBase"] == "4000.00"
    assert allocation["linkedInvoiceCount"] == 2
    assert allocation["freightGrossValue"] == "32.50"


def test_closure_rows_do_not_reach_the_grid() -> None:
    service, _ = build(
        [
            freight_link(invoice_document="000000001", in_filter=True),
            freight_link(invoice_document="000000002", in_filter=False),
        ]
    )

    result = service.dashboard(full_user(), **PERIOD)

    assert [item["invoiceDocument"] for item in result["items"]] == ["000000001"]
    assert result["items"][0]["allocations"][0]["allocationBase"] == "2000.00"


def test_incomplete_source_is_flagged_in_the_pagination() -> None:
    class TruncatingGateway(FakeFinancialGateway):
        def fetch_purchase_freight_links(self, **kwargs):
            payload = super().fetch_purchase_freight_links(**kwargs)
            payload["data"]["pagination"]["is_complete"] = False
            return payload

    service = FreightService(TruncatingGateway())

    result = service.dashboard(full_user(), **PERIOD)

    assert result["pagination"]["isComplete"] is False


def test_filters_are_forwarded_to_the_gateway() -> None:
    service, gateway = build()

    service.dashboard(
        full_user(),
        supplier="001992",
        invoice_document="000000001",
        freight_document="000000900",
        **PERIOD,
    )

    forwarded = gateway.call_kwargs("fetch_purchase_freight_links")
    assert forwarded["supplier"] == "001992"
    assert forwarded["invoice_document"] == "000000001"
    assert forwarded["freight_document"] == "000000900"
    assert forwarded["limit"] == 20000

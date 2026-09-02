import pytest

from app.application.dto.financial.purchase_freight_links_request import (
    PurchaseFreightLinksRequest,
)
from app.application.use_cases.financial.get_purchase_freight_links_use_case import (
    DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
    GetPurchaseFreightLinksUseCase,
)
from app.composition.query_cache_composer import reset_query_cache_for_tests


class FakeRepository:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def list_purchase_freight_links(self, request, *, limit):
        self.calls.append((request, limit))
        return self.rows


def _row(**overrides):
    row = {
        "branch": "01",
        "in_filter": 1,
        "link_entry_date": "20260107",
        "invoice_found": 1,
        "invoice_document": "000123456",
        "invoice_series": "1",
        "supplier_code": "001992",
        "supplier_store": "03",
        "supplier_name": "FORNECEDOR X",
        "invoice_goods_value": 1000.0,
        "invoice_issue_date": "20260105",
        "invoice_entry_date": "20260107",
        "freight_found": 1,
        "freight_document": "000000789",
        "freight_series": "1",
        "carrier_code": "003686",
        "carrier_store": "01",
        "carrier_name": "TRANSPORTADORA Y",
        "freight_gross_value": 32.5,
        "freight_issue_date": "20260106",
        "freight_access_key": "4326" + "0" * 40,
        "freight_document_type": "N",
        "freight_document_kind": "CTE",
    }
    row.update(overrides)
    return row


@pytest.fixture(autouse=True)
def _clear_cache():
    reset_query_cache_for_tests()
    yield
    reset_query_cache_for_tests()


def test_maps_row_to_english_contract() -> None:
    use_case = GetPurchaseFreightLinksUseCase(FakeRepository([_row()]))

    result = use_case.execute(PurchaseFreightLinksRequest(issue_start="2026-01-01"))
    item = result["items"][0]

    assert item["invoice_goods_value"] == 1000.0
    assert item["freight_gross_value"] == 32.5
    assert item["invoice_issue_date"] == "2026-01-05"
    assert item["invoice_entry_date"] == "2026-01-07"
    assert item["in_filter"] is True
    assert item["invoice_found"] is True


def test_missing_document_keeps_value_null_instead_of_zero() -> None:
    rows = [_row(invoice_found=0, invoice_goods_value="", invoice_issue_date="")]
    use_case = GetPurchaseFreightLinksUseCase(FakeRepository(rows))

    item = use_case.execute(PurchaseFreightLinksRequest())["items"][0]

    assert item["invoice_found"] is False
    assert item["invoice_goods_value"] is None
    assert item["invoice_issue_date"] == ""


def test_overfetch_marks_result_as_incomplete() -> None:
    rows = [_row(invoice_document=f"{index:09d}") for index in range(4)]
    use_case = GetPurchaseFreightLinksUseCase(FakeRepository(rows))

    result = use_case.execute(PurchaseFreightLinksRequest(), limit=3)

    assert result["pagination"]["returned"] == 3
    assert result["pagination"]["is_complete"] is False
    assert result["pagination"]["limit"] == 3


def test_complete_result_when_rows_fit_the_limit() -> None:
    use_case = GetPurchaseFreightLinksUseCase(FakeRepository([_row()]))

    result = use_case.execute(PurchaseFreightLinksRequest(), limit=10)

    assert result["pagination"]["is_complete"] is True
    assert result["pagination"]["returned"] == 1


def test_limit_is_capped_to_the_default_ceiling() -> None:
    repository = FakeRepository([])
    use_case = GetPurchaseFreightLinksUseCase(repository)

    use_case.execute(PurchaseFreightLinksRequest(), limit=10**9)

    assert repository.calls[0][1] == DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT


def test_summary_separates_closure_rows_from_filtered_rows() -> None:
    rows = [_row(), _row(invoice_document="000999999", in_filter=0)]
    use_case = GetPurchaseFreightLinksUseCase(FakeRepository(rows))

    summary = use_case.execute(PurchaseFreightLinksRequest(branch="01"))["summary"]

    assert summary["total_records"] == 2
    assert summary["in_filter_records"] == 1
    assert summary["branch_filter_applied"] is True


def test_second_call_with_same_filters_hits_the_cache() -> None:
    repository = FakeRepository([_row()])
    use_case = GetPurchaseFreightLinksUseCase(repository)
    request = PurchaseFreightLinksRequest(issue_start="2026-01-01")

    use_case.execute(request)
    use_case.execute(request)

    assert len(repository.calls) == 1

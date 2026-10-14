"""CI corrective: HTTP query defaults and limits remain stable."""
from app.domain.services.pagination_tier_service import PaginationTierService
from app.interface.http.pagination_query import PAGE_SIZE_QUERY


def test_gpt_legacy_page_size_contract():
    tier = PaginationTierService.get("page_50_50_gpt_legacy")
    assert (tier.default, tier.ge, tier.le) == (50, 1, 50)
    q = PAGE_SIZE_QUERY("page_50_50_gpt_legacy")
    assert (q.default, q.ge, q.le) == (50, 1, 50)


def test_received_invoice_page_size_contract():
    tier = PaginationTierService.get("page_25_100_received_invoices")
    assert (tier.default, tier.ge, tier.le) == (25, 1, 100)
    q = PAGE_SIZE_QUERY("page_25_100_received_invoices")
    assert (q.default, q.ge, q.le) == (25, 1, 100)

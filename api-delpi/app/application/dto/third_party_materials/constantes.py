from __future__ import annotations

from app.domain.totvs.protheus_third_party_materials import (
    API_SHIPMENT_STATUS_VALUES,
    DEFAULT_IGNORED_TEST_PRODUCTS,
)

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_EXPORT_ROWS = 20_000

EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_XLSX = "xlsx"
EXPORT_FORMAT_VALUES = (EXPORT_FORMAT_CSV, EXPORT_FORMAT_XLSX)

VALID_SHIPMENT_STATUS = frozenset(API_SHIPMENT_STATUS_VALUES)


def parse_ignored_products(raw: str | None) -> tuple[str, ...]:
    tokens = tuple(
        item.strip()
        for item in str(raw or "").split(",")
        if item.strip()
    )
    return tokens or DEFAULT_IGNORED_TEST_PRODUCTS

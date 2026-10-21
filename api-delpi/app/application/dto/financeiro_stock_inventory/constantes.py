"""Defaults for the R03/P7 stock-inventory snapshot query (SB9010/SB1010)."""

from __future__ import annotations

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50

REPORT_SCOPE_ALL_PRODUCTS = "all_products"
REPORT_SCOPE_MP_PI_PA = "mp_pi_pa"
REPORT_SCOPES = frozenset({REPORT_SCOPE_ALL_PRODUCTS, REPORT_SCOPE_MP_PI_PA})

# Product types (SB1 B1_TIPO) restricted by the mp_pi_pa view (doc 49 §2).
MP_PI_PA_PRODUCT_TYPES = ("MP", "PI", "PA")

# Operational query statuses (doc 49 §4 / §6.7). ``source_missing`` means the
# SB9 month-end snapshot has no rows for the requested branch(es);
# ``incomplete`` means only part of the expected branches have a snapshot;
# ``no_matching_items`` means the snapshot exists but filters matched no row.
STATUS_AVAILABLE = "available"
STATUS_INCOMPLETE = "incomplete"
STATUS_SOURCE_MISSING = "source_missing"
STATUS_NO_MATCHING_ITEMS = "no_matching_items"

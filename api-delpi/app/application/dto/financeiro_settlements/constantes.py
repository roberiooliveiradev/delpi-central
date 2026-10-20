"""Defaults for financial settlement queries (FK1/FK2 events)."""

from __future__ import annotations

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
DEFAULT_SORT_BY = "settlement_date"
DEFAULT_SORT_DIR = "desc"

SETTLEMENT_SIDE_PAYABLE = "payable"
SETTLEMENT_SIDE_RECEIVABLE = "receivable"

# Whitelist de campos ordenáveis — never interpolated raw.
SORTABLE_FIELDS = frozenset({"settlement_date", "nature"})

# Movement codes kept verbatim from the source (FKx_TPDOC). Their business
# semantics stay unclassified until the finance owner signs off (doc 48 D4).
# The filter accepts any non-empty trimmed code; the allowlist is advisory.
KNOWN_MOVEMENT_TYPES = frozenset({"BA", "ES", "VL", "CP"})

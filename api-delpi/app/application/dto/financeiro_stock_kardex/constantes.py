"""Defaults for the R06/R07 stock-kardex engine (MATR910, doc 85 §6-§7).

The status/parity vocabulary is shared with the sibling stock-inventory
family — a missing SB9 opening snapshot surfaces as ``source_missing``,
never as a substituted month or a fabricated zero balance.
"""

from __future__ import annotations

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50

# Document-kind filter (doc 122 §4): ``all`` keeps the full MATR910
# movement union; ``invent`` selects the inventory-adjustment slice
# (SD3 D3_DOC='INVENT') that R07 reproduces.
DOCUMENT_KIND_ALL = "all"
DOCUMENT_KIND_INVENT = "invent"
DOCUMENT_KINDS = frozenset({DOCUMENT_KIND_ALL, DOCUMENT_KIND_INVENT})

# Printed-column classification (MATR910 TES<=500 rule with the
# devolution inversion — BR-R06-004..006).
MOVEMENT_KIND_ENTRY = "entry"
MOVEMENT_KIND_OUTPUT = "output"
MOVEMENT_KINDS = frozenset({MOVEMENT_KIND_ENTRY, MOVEMENT_KIND_OUTPUT})

# Cost provenance per movement line (doc 122 §5.2): ``CURRENT`` reads the
# stored cost field; ``TTAT_OLD`` restores the as-of value logged in the
# table-specific *_TTAT_LOG before the first post-boundary recalculation.
COST_AS_OF_CURRENT = "CURRENT"
COST_AS_OF_TTAT = "TTAT_OLD"

# Server-side sort allowlist — anything else is a typed 400.
SORT_FIELD_PRODUCT = "product"
SORT_FIELD_DATE = "date"
SORT_FIELDS = frozenset({SORT_FIELD_PRODUCT, SORT_FIELD_DATE})
SORT_DIR_ASC = "asc"
SORT_DIR_DESC = "desc"
SORT_DIRS = frozenset({SORT_DIR_ASC, SORT_DIR_DESC})

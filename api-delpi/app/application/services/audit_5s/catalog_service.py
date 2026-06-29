from __future__ import annotations

DEFAULT_CATALOG_VERSION = 1

# Fallback quando a migration V028 ainda não rodou (dev/local).
_BRANCH_CATALOG_FALLBACK: dict[str, int] = {
    "01": 2,
    "02": 1,
}


def fallback_catalog_version(branch_code: str) -> int:
    return _BRANCH_CATALOG_FALLBACK.get(branch_code, DEFAULT_CATALOG_VERSION)

"""Sync test — catálogo Python == matriz canônica do módulo ADVPL.

Fonte única: integrations/protheus-advpl/modules/product-master/
contracts/sb1-field-matrix.json (SX3 DELPI_TST01 == DELPI).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.application.services.integrations.protheus_product_field_catalog import (
    PRODUCT_FIELD_SPECS,
    PRODUCT_PROTECTED_FIELDS,
)

MATRIX = (
    Path(__file__).resolve().parents[1]
    / "integrations/protheus-advpl/modules/product-master/contracts/sb1-field-matrix.json"
)


def _fields():
    return json.loads(MATRIX.read_text(encoding="utf-8"))["fields"]


def test_catalog_covers_all_write_eligible():
    expected = {
        f["field"]
        for f in _fields()
        if f["classification"] in ("READ_WRITE_ELIGIBLE", "CONDITIONAL")
        or f["field"] == "B1_COD"
    }
    assert set(PRODUCT_FIELD_SPECS) == expected


def test_catalog_kind_and_size_match_sx3():
    for f in _fields():
        if f["field"] not in PRODUCT_FIELD_SPECS:
            continue
        spec = PRODUCT_FIELD_SPECS[f["field"]]
        assert spec["kind"] == ("M" if f["type"] == "M" else f["type"])
        assert spec["max_length"] == f["size"]
        assert spec["decimals"] == f["decimals"]


def test_protected_matches_matrix():
    expected = {
        f["field"]
        for f in _fields()
        if f["classification"] in ("IMMUTABLE", "SYSTEM_MANAGED")
        and f["field"] != "B1_COD"
    }
    assert set(PRODUCT_PROTECTED_FIELDS) == expected


def test_no_protected_in_write_catalog():
    assert not (set(PRODUCT_PROTECTED_FIELDS) & set(PRODUCT_FIELD_SPECS))

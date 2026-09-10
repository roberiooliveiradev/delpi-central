from __future__ import annotations

from requests_app.domain.services.correction_targets import (
    normalize_correction_targets,
)


def test_normalize_filters_unknown_and_duplicates():
    assert normalize_correction_targets(
        ["recipient", "items", "recipient", "bogus", "ITEMS", "??"],
        type_code="invoice-issuance",
    ) == ["recipient", "items"]


def test_normalize_empty_inputs():
    assert normalize_correction_targets(None, type_code="invoice-issuance") == []
    assert normalize_correction_targets([], type_code="invoice-issuance") == []
    assert normalize_correction_targets("recipient", type_code="invoice-issuance") == [
        "recipient"
    ]

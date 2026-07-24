"""Normalização fiscal — lançamento-notas-fiscais."""

from __future__ import annotations

import pytest

from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    FiscalNormalizationError,
    normalize_branch,
    normalize_document,
    normalize_series,
)


@pytest.mark.parametrize(
    ("raw", "document_number", "match_key"),
    [
        ("123456", "000123456", "000123456"),
        ("00123456", "000123456", "000123456"),
        ("123456789", "123456789", "123456789"),
        ("1", "000000001", "000000001"),
    ],
)
def test_normalize_document_ok(raw: str, document_number: str, match_key: str) -> None:
    result = normalize_document(raw)
    assert result.document_number == document_number
    assert result.document_match_key == match_key


@pytest.mark.parametrize("raw", ["", "ABC", "1234567890", "12A", None])
def test_normalize_document_invalid(raw: str | None) -> None:
    with pytest.raises(FiscalNormalizationError):
        normalize_document(raw)


def test_normalize_series() -> None:
    assert normalize_series(None) == ""
    assert normalize_series("  a1 ") == "A1"
    with pytest.raises(FiscalNormalizationError):
        normalize_series("ABCD")
    with pytest.raises(FiscalNormalizationError):
        normalize_series("", required=True)
    assert normalize_series("1", required=True) == "1"


def test_normalize_branch() -> None:
    assert normalize_branch("01") == "01"
    assert normalize_branch("02") == "02"
    with pytest.raises(FiscalNormalizationError):
        normalize_branch("03")

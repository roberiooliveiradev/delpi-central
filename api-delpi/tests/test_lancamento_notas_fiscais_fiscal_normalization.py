"""Normalização fiscal — lançamento-notas-fiscais."""

from __future__ import annotations

import pytest

from app.domain.services.lancamento_notas_fiscais.fiscal_normalization import (
    FiscalNormalizationError,
    normalize_branch,
    normalize_document,
    normalize_fiscal_model,
    normalize_series,
    series_is_required,
    should_auto_resume_after_purchase_order_link,
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


def test_normalize_fiscal_model_accepts_product_and_service_invoices() -> None:
    assert normalize_fiscal_model("nfe") == "nfe"
    assert normalize_fiscal_model("NF-e") == "nfe"
    assert normalize_fiscal_model("nfse") == "nfse"
    assert normalize_fiscal_model("NFS-e") == "nfse"


def test_normalize_fiscal_model_rejects_empty_and_unknown() -> None:
    with pytest.raises(FiscalNormalizationError):
        normalize_fiscal_model(None)
    with pytest.raises(FiscalNormalizationError):
        normalize_fiscal_model("")
    with pytest.raises(FiscalNormalizationError):
        normalize_fiscal_model("cte")
    assert normalize_fiscal_model(None, required=False) is None


def test_series_is_required_only_for_product_invoice() -> None:
    assert series_is_required("nfe") is True
    assert series_is_required(None) is True
    assert series_is_required("nfse") is False


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


def test_should_auto_resume_only_for_purchase_order_block_with_linked_po() -> None:
    assert (
        should_auto_resume_after_purchase_order_link(
            status="blocked",
            block_reason="purchase_order",
            has_linked_purchase_orders=True,
        )
        is True
    )
    assert (
        should_auto_resume_after_purchase_order_link(
            status="blocked",
            block_reason="purchase_order",
            has_linked_purchase_orders=False,
        )
        is False
    )
    assert (
        should_auto_resume_after_purchase_order_link(
            status="blocked",
            block_reason="other",
            has_linked_purchase_orders=True,
        )
        is False
    )
    assert (
        should_auto_resume_after_purchase_order_link(
            status="in_progress",
            block_reason="purchase_order",
            has_linked_purchase_orders=True,
        )
        is False
    )

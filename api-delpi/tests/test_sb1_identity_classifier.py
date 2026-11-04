"""Classificação SB1 — igualdade exata, sem LIKE/prefixo."""

from __future__ import annotations

from app.domain.services.product.sb1_identity_classifier import (
    MATCH_AMBIGUOUS,
    MATCH_BLOCKED,
    MATCH_CONFIRMED,
    MATCH_DIVERGENT,
    MATCH_NOT_FOUND,
    MATCH_PENDING,
    MATCHED_BY_CODE_AND_REFERENCE,
    MATCHED_BY_REFERENCE_ONLY,
    classify_sb1_identity_pair,
)


def _row(
    code: str,
    reference: str,
    *,
    blocked: str = "2",
    description: str = "Produto",
) -> dict:
    return {
        "product_code": code,
        "customer_reference": reference,
        "description": description,
        "product_type": "PA",
        "unit": "UN",
        "group_code": "01",
        "blocked_flag": blocked,
    }


def test_confirmed_code_and_reference() -> None:
    result = classify_sb1_identity_pair(
        product_code="10080034",
        customer_reference="WEG-ABC",
        by_code=_row("10080034", "WEG-ABC"),
        by_reference=[_row("10080034", "WEG-ABC")],
    )
    assert result["match_status"] == MATCH_CONFIRMED
    assert result["matched_by"] == MATCHED_BY_CODE_AND_REFERENCE
    assert result["verified_product_code"] == "10080034"


def test_reference_only_unique() -> None:
    result = classify_sb1_identity_pair(
        product_code=None,
        customer_reference="WEG-ABC",
        by_code=None,
        by_reference=[_row("10080034", "WEG-ABC")],
    )
    assert result["match_status"] == MATCH_CONFIRMED
    assert result["matched_by"] == MATCHED_BY_REFERENCE_ONLY


def test_ambiguous_reference_does_not_pick_first() -> None:
    result = classify_sb1_identity_pair(
        product_code=None,
        customer_reference="WEG-ABC",
        by_code=None,
        by_reference=[
            _row("10080034", "WEG-ABC"),
            _row("10080099", "WEG-ABC"),
        ],
    )
    assert result["match_status"] == MATCH_AMBIGUOUS
    assert result["verified_product_code"] is None
    assert len(result["candidates"]) == 2


def test_divergent_code_vs_reference() -> None:
    result = classify_sb1_identity_pair(
        product_code="10080034",
        customer_reference="WEG-OTHER",
        by_code=_row("10080034", "WEG-ABC"),
        by_reference=[_row("10080999", "WEG-OTHER")],
    )
    assert result["match_status"] == MATCH_DIVERGENT
    assert result["reason"] == "informed_code_reference_mismatch"


def test_informed_code_missing_but_reference_maps_is_divergent() -> None:
    result = classify_sb1_identity_pair(
        product_code="99999999",
        customer_reference="WEG-ABC",
        by_code=None,
        by_reference=[_row("10080034", "WEG-ABC")],
    )
    assert result["match_status"] == MATCH_DIVERGENT
    assert result["reason"] == "informed_code_missing_reference_maps_elsewhere"


def test_not_found() -> None:
    result = classify_sb1_identity_pair(
        product_code="99999999",
        customer_reference="MISSING",
        by_code=None,
        by_reference=[],
    )
    assert result["match_status"] == MATCH_NOT_FOUND


def test_blocked_unique() -> None:
    result = classify_sb1_identity_pair(
        product_code="10080034",
        customer_reference="WEG-ABC",
        by_code=_row("10080034", "WEG-ABC", blocked="1"),
        by_reference=[_row("10080034", "WEG-ABC", blocked="1")],
    )
    assert result["match_status"] == MATCH_BLOCKED


def test_pending_when_both_empty() -> None:
    result = classify_sb1_identity_pair(
        product_code=None,
        customer_reference="  ",
        by_code=None,
        by_reference=[],
    )
    assert result["match_status"] == MATCH_PENDING


def test_normalization_strips_spaces() -> None:
    result = classify_sb1_identity_pair(
        product_code=" 10080034 ",
        customer_reference=" WEG-ABC ",
        by_code=_row("10080034", "WEG-ABC"),
        by_reference=[_row("10080034", "WEG-ABC")],
    )
    assert result["match_status"] == MATCH_CONFIRMED

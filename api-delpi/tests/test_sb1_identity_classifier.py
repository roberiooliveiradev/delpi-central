"""Classificação SB1 — igualdade exata, sem LIKE/prefixo."""

from __future__ import annotations

from app.domain.services.product.sb1_identity_classifier import (
    DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE,
    MATCH_AMBIGUOUS,
    MATCH_BLOCKED,
    MATCH_CONFIRMED,
    MATCH_DIVERGENT,
    MATCH_NOT_FOUND,
    MATCH_PENDING,
    MATCHED_BY_CODE_AND_REFERENCE,
    MATCHED_BY_REFERENCE_ONLY,
    MATCHED_BY_REFERENCE_PREFER_PRODUCTION,
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


def test_prefer_unique_production_over_sample_when_informed_8() -> None:
    """Caso 19106407: 80015942 informado, 90264221 produção elegível."""
    result = classify_sb1_identity_pair(
        product_code="80015942",
        customer_reference="19106407",
        by_code=_row("80015942", "19106407", description="Amostra"),
        by_reference=[
            _row("80015942", "19106407", description="Amostra"),
            _row("90264221", "19106407", description="Producao"),
        ],
        disambiguation_policy=DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE,
    )
    assert result["match_status"] == MATCH_CONFIRMED
    assert result["product_code"] == "80015942"
    assert result["verified_product_code"] == "90264221"
    assert result["matched_by"] == MATCHED_BY_REFERENCE_PREFER_PRODUCTION
    assert result["reason"] == "prefer_unique_production_code_over_sample"


def test_prefer_policy_off_keeps_informed_sample() -> None:
    result = classify_sb1_identity_pair(
        product_code="80015942",
        customer_reference="19106407",
        by_code=_row("80015942", "19106407"),
        by_reference=[
            _row("80015942", "19106407"),
            _row("90264221", "19106407"),
        ],
    )
    assert result["match_status"] == MATCH_CONFIRMED
    assert result["verified_product_code"] == "80015942"


def test_multiple_production_codes_remain_ambiguous() -> None:
    result = classify_sb1_identity_pair(
        product_code=None,
        customer_reference="19106407",
        by_code=None,
        by_reference=[
            _row("90264221", "19106407"),
            _row("90264222", "19106407"),
        ],
        disambiguation_policy=DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE,
    )
    assert result["match_status"] == MATCH_AMBIGUOUS
    assert result["verified_product_code"] is None
    assert result["reason"] == "multiple_production_codes"


def test_blocked_production_falls_back_to_unique_sample() -> None:
    result = classify_sb1_identity_pair(
        product_code="80015942",
        customer_reference="19106407",
        by_code=_row("80015942", "19106407"),
        by_reference=[
            _row("80015942", "19106407"),
            _row("90264221", "19106407", blocked="1"),
        ],
        disambiguation_policy=DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE,
    )
    assert result["match_status"] == MATCH_CONFIRMED
    assert result["verified_product_code"] == "80015942"
    assert result["reason"] == "provisional_sample_code_no_production"


def test_preference_does_not_override_divergent() -> None:
    result = classify_sb1_identity_pair(
        product_code="80015942",
        customer_reference="OTHER-REF",
        by_code=_row("80015942", "19106407"),
        by_reference=[
            _row("90264221", "OTHER-REF"),
            _row("80015999", "OTHER-REF"),
        ],
        disambiguation_policy=DISAMBIGUATION_PREFER_PRODUCTION_OVER_SAMPLE,
    )
    assert result["match_status"] == MATCH_DIVERGENT
    assert result["reason"] == "informed_code_reference_mismatch"

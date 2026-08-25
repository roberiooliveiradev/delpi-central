from __future__ import annotations

from app.domain.services.commercial_customer_codes_filter_service import (
    CommercialCustomerCodesFilterService,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def test_normalize_csv_dedupes_and_trims():
    assert CommercialCustomerCodesFilterService.normalize(" 001 ,002,001 ") == [
        "001",
        "002",
    ]


def test_normalize_blank_is_none():
    assert CommercialCustomerCodesFilterService.normalize(None) is None
    assert CommercialCustomerCodesFilterService.normalize("") is None
    assert CommercialCustomerCodesFilterService.normalize("   ") is None


def test_normalize_ignores_non_string_non_sequence():
    assert CommercialCustomerCodesFilterService.normalize(object()) is None


def test_normalize_nonempty_without_valid_codes_is_empty_list():
    assert CommercialCustomerCodesFilterService.normalize(",,,") == []


def test_apply_none_skips():
    qb = QueryBuilder()
    qb.raw("1 = 1")
    CommercialCustomerCodesFilterService.apply_to_query_builder(qb, "AD1.AD1_CODCLI", None)
    where, params = qb.build()
    assert where == "1 = 1"
    assert list(params) == []


def test_apply_empty_forces_no_rows():
    qb = QueryBuilder()
    CommercialCustomerCodesFilterService.apply_to_query_builder(qb, "AD1.AD1_CODCLI", [])
    where, params = qb.build()
    assert where == "1 = 0"
    assert list(params) == []


def test_apply_codes_in_list():
    qb = QueryBuilder()
    CommercialCustomerCodesFilterService.apply_to_query_builder(
        qb, "D2.D2_CLIENTE", ["A", "B"]
    )
    where, params = qb.build()
    assert "D2.D2_CLIENTE IN" in where
    assert list(params) == ["A", "B"]


def test_apply_exclude_codes_not_in():
    qb = QueryBuilder()
    CommercialCustomerCodesFilterService.apply_exclude_to_query_builder(
        qb, "D2.D2_CLIENTE", ["A", "B"]
    )
    where, params = qb.build()
    assert "D2.D2_CLIENTE NOT IN" in where
    assert list(params) == ["A", "B"]


def test_apply_exclude_none_or_empty_skips():
    qb = QueryBuilder()
    qb.raw("1 = 1")
    CommercialCustomerCodesFilterService.apply_exclude_to_query_builder(
        qb, "D2.D2_CLIENTE", None
    )
    CommercialCustomerCodesFilterService.apply_exclude_to_query_builder(
        qb, "D2.D2_CLIENTE", []
    )
    where, params = qb.build()
    assert where == "1 = 1"
    assert list(params) == []

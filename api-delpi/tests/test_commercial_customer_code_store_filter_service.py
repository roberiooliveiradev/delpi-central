from __future__ import annotations

from app.domain.services.commercial_customer_code_store_filter_service import (
    CommercialCustomerCodeStoreFilterService,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def test_normalize_csv_dedupes_and_trims():
    assert CommercialCustomerCodeStoreFilterService.normalize(
        " 000001|01 ,000001|05,000001|01 "
    ) == [
        ("000001", "01"),
        ("000001", "05"),
    ]


def test_normalize_blank_is_none():
    assert CommercialCustomerCodeStoreFilterService.normalize(None) is None
    assert CommercialCustomerCodeStoreFilterService.normalize("") is None
    assert CommercialCustomerCodeStoreFilterService.normalize("   ") is None


def test_normalize_ignores_non_string_non_sequence():
    assert CommercialCustomerCodeStoreFilterService.normalize(object()) is None


def test_normalize_nonempty_without_valid_pairs_is_empty_list():
    assert CommercialCustomerCodeStoreFilterService.normalize("|||,,") == []
    assert CommercialCustomerCodeStoreFilterService.normalize("000001") == []
    assert CommercialCustomerCodeStoreFilterService.normalize("|01") == []
    assert CommercialCustomerCodeStoreFilterService.normalize("000001|") == []


def test_normalize_list_of_tuples():
    assert CommercialCustomerCodeStoreFilterService.normalize(
        [("000001", "01"), ("000001", "01"), ("000002", "02")]
    ) == [("000001", "01"), ("000002", "02")]


def test_apply_none_skips():
    qb = QueryBuilder()
    qb.raw("1 = 1")
    CommercialCustomerCodeStoreFilterService.apply_to_query_builder(
        qb, "C5.C5_CLIENTE", "C5.C5_LOJACLI", None
    )
    where, params = qb.build()
    assert where == "1 = 1"
    assert list(params) == []


def test_apply_empty_forces_no_rows():
    qb = QueryBuilder()
    CommercialCustomerCodeStoreFilterService.apply_to_query_builder(
        qb, "C5.C5_CLIENTE", "C5.C5_LOJACLI", []
    )
    where, params = qb.build()
    assert where == "1 = 0"
    assert list(params) == []


def test_apply_pairs_or_of_ands():
    qb = QueryBuilder()
    CommercialCustomerCodeStoreFilterService.apply_to_query_builder(
        qb,
        "C5.C5_CLIENTE",
        "C5.C5_LOJACLI",
        [("000001", "01"), ("000001", "05")],
    )
    where, params = qb.build()
    assert "(C5.C5_CLIENTE = ? AND C5.C5_LOJACLI = ?)" in where
    assert " OR " in where
    assert list(params) == ["000001", "01", "000001", "05"]

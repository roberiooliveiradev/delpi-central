from __future__ import annotations

from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)
from app.domain.services.commercial_analysis_filter_service import (
    CommercialAnalysisFilterService,
)
from app.domain.services.commercial_customer_codes_filter_service import (
    CommercialCustomerCodesFilterService,
)
from app.domain.services.commercial_customer_name_filter_service import (
    CommercialCustomerNameFilterService,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def test_normalize_names_csv_dedupes_casefold():
    assert CommercialCustomerNameFilterService.normalize(" Schulz ,WANKE,schulz ") == [
        "Schulz",
        "WANKE",
    ]


def test_normalize_names_blank_is_none():
    assert CommercialCustomerNameFilterService.normalize(None) is None
    assert CommercialCustomerNameFilterService.normalize("") is None
    assert CommercialCustomerNameFilterService.normalize("   ") is None


def test_normalize_names_invalid_only_is_empty():
    assert CommercialCustomerNameFilterService.normalize(",,,") == []


def test_name_include_or_like():
    qb = QueryBuilder()
    CommercialCustomerNameFilterService.apply_include_to_query_builder(
        qb, "A1.A1_NOME", ["Schulz", "Wanke"]
    )
    where, params = qb.build()
    assert "OR" in where
    assert "LIKE ?" in where
    assert list(params) == ["%schulz%", "%wanke%"]


def test_name_exclude_and_not_like():
    qb = QueryBuilder()
    CommercialCustomerNameFilterService.apply_exclude_to_query_builder(
        qb, "A1.A1_NOME", ["Schulz"]
    )
    where, params = qb.build()
    assert "NOT LIKE ?" in where
    assert list(params) == ["%schulz%"]


def test_codes_exclude_not_in():
    qb = QueryBuilder()
    CommercialCustomerCodesFilterService.apply_exclude_to_query_builder(
        qb, "D2.D2_CLIENTE", ["A", "B"]
    )
    where, params = qb.build()
    assert "D2.D2_CLIENTE NOT IN" in where
    assert list(params) == ["A", "B"]


def test_analysis_filter_include_codes_only():
    qb = QueryBuilder()
    CommercialAnalysisFilterService.apply_to_query_builder(
        qb,
        customer_code_column="D2.D2_CLIENTE",
        customer_name_column="A1.A1_NOME",
        customer_codes=["001"],
    )
    where, params = qb.build()
    assert "D2.D2_CLIENTE IN" in where
    assert list(params) == ["001"]


def test_analysis_filter_include_names_only():
    qb = QueryBuilder()
    CommercialAnalysisFilterService.apply_to_query_builder(
        qb,
        customer_code_column="D2.D2_CLIENTE",
        customer_name_column="A1.A1_NOME",
        customer_names=["Weg"],
    )
    where, params = qb.build()
    assert "LIKE ?" in where
    assert list(params) == ["%weg%"]


def test_analysis_filter_include_codes_or_names():
    qb = QueryBuilder()
    CommercialAnalysisFilterService.apply_to_query_builder(
        qb,
        customer_code_column="D2.D2_CLIENTE",
        customer_name_column="A1.A1_NOME",
        customer_codes=["001"],
        customer_names=["Schulz"],
    )
    where, params = qb.build()
    assert " OR " in where
    assert "IN (" in where
    assert list(params) == ["001", "%schulz%"]


def test_analysis_filter_codes_and_code_stores():
    qb = QueryBuilder()
    CommercialAnalysisFilterService.apply_to_query_builder(
        qb,
        customer_code_column="C5.C5_CLIENTE",
        customer_name_column="A1.A1_NOME",
        customer_store_column="C5.C5_LOJACLI",
        customer_codes=["000001"],
        customer_code_stores=[("000001", "01"), ("000001", "05")],
    )
    where, params = qb.build()
    assert "C5.C5_CLIENTE IN" in where
    assert "C5.C5_LOJACLI = ?" in where
    assert " AND " in where
    assert list(params) == ["000001", "000001", "01", "000001", "05"]


def test_analysis_filter_request_has_include_with_code_stores():
    req = CommercialAnalysisFilterRequest(
        customer_code_stores=[("000001", "01")],
    )
    assert req.has_include_customer_filter() is True


def test_analysis_filter_exclude_wins_after_include():
    qb = QueryBuilder()
    CommercialAnalysisFilterService.apply_to_query_builder(
        qb,
        customer_code_column="D2.D2_CLIENTE",
        customer_name_column="A1.A1_NOME",
        customer_segment="new_business",
        customer_names=["Flex"],
        exclude_customer_names=["Schulz"],
        exclude_customer_codes=["999"],
    )
    where, params = qb.build()
    assert "NOT (" in where or "NOT(" in where.replace(" ", "")
    assert "NOT IN" in where
    assert "NOT LIKE ?" in where
    assert "%flex%" in params
    assert "%schulz%" in params
    assert "999" in params


def test_analysis_filter_request_validate_defaults():
    req = CommercialAnalysisFilterRequest()
    req.validate()
    assert req.granularity == "week"
    assert req.group_by == "customer"
    assert req.page == 1
    assert req.page_size == 50
    assert req.include_portfolio is False


def test_analysis_filter_request_include_portfolio():
    flags = CommercialAnalysisFilterService.parse_include_flags("portfolio")
    req = CommercialAnalysisFilterRequest(include_flags=flags)
    req.validate()
    assert req.include_portfolio is True


def test_analysis_filter_request_invalid_include():
    try:
        CommercialAnalysisFilterService.parse_include_flags("foo")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "include" in str(exc).lower()

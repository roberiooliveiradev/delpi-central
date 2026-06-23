import pytest

from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
    WEG_CLIENT_CODE_CANONICAL,
)


def test_normalize_customer_segment_accepts_weg_aliases() -> None:
    assert CommercialCustomerSegmentService.normalize_customer_segment("weg") == "weg"
    assert CommercialCustomerSegmentService.normalize_customer_segment("WEG") == "weg"


def test_normalize_customer_segment_accepts_new_business_aliases() -> None:
    assert (
        CommercialCustomerSegmentService.normalize_customer_segment("new_business")
        == "new_business"
    )
    assert (
        CommercialCustomerSegmentService.normalize_customer_segment("new-business")
        == "new_business"
    )


def test_normalize_customer_segment_empty_is_none() -> None:
    assert CommercialCustomerSegmentService.normalize_customer_segment(None) is None
    assert CommercialCustomerSegmentService.normalize_customer_segment("") is None


def test_normalize_customer_segment_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="customer_segment inválido"):
        CommercialCustomerSegmentService.normalize_customer_segment("outro")


def test_sql_is_weg_client_code_normalizes_padding() -> None:
    sql = CommercialCustomerSegmentService.sql_is_weg_client_code("AD1.AD1_CODCLI")
    assert WEG_CLIENT_CODE_CANONICAL in sql
    assert "RIGHT('000000'" in sql


def test_sql_segment_predicate_weg_and_new_business() -> None:
    weg = CommercialCustomerSegmentService.sql_segment_predicate(
        "AD1.AD1_CODCLI",
        "weg",
    )
    new_business = CommercialCustomerSegmentService.sql_segment_predicate(
        "AD1.AD1_CODCLI",
        "new_business",
    )
    assert weg.startswith("(")
    assert new_business.startswith("NOT (")


def test_sql_segment_predicate_empty_segment() -> None:
    assert (
        CommercialCustomerSegmentService.sql_segment_predicate("AD1.AD1_CODCLI", None)
        == ""
    )

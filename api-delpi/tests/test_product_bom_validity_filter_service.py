from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)


def test_validity_filter_sql_uses_reference_param_and_alias() -> None:
    sql = ProductBomValidityFilterService.validity_filter_sql(
        alias="G1",
        reference_param="@DATA_REF",
    )
    assert "G1.G1_INI" in sql
    assert "G1.G1_FIM" in sql
    assert "<= @DATA_REF" in sql
    assert ">= @DATA_REF" in sql


def test_validity_filter_sql_for_today_without_alias() -> None:
    sql = ProductBomValidityFilterService.validity_filter_sql_for_today()
    assert "G1_INI = ''" in sql
    assert "G1_FIM = ''" in sql
    assert "GETDATE()" in sql


def test_validity_filter_sql_for_today_with_alias() -> None:
    sql = ProductBomValidityFilterService.validity_filter_sql_for_today(alias="c")
    assert "c.G1_INI" in sql
    assert "c.G1_FIM" in sql


def test_response_metadata_for_chat_consumption() -> None:
    metadata = ProductBomValidityFilterService.response_metadata()
    assert metadata["filter"] == "current"
    assert "G1_INI" in metadata["validityColumns"]

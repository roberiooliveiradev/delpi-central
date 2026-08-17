"""Constantes compartilhadas de materiais de terceiros (SB6)."""

from app.domain.totvs.protheus_third_party_materials import (
    API_SHIPMENT_STATUS_VALUES,
    API_TO_VIEW_SHIPMENT_STATUS,
    DEFAULT_IGNORED_TEST_PRODUCTS,
    SB6_PODER3_REMESSA,
    SB6_PODER3_RETORNO,
    SB6_SHIPMENT_KEY_FIELDS,
    SB6_TIPO_TERCEIRO_NA_EMPRESA,
    VIEW_NAME,
    VIEW_TO_API_SHIPMENT_STATUS,
)


def test_poder3_and_tipo_are_stable() -> None:
    assert SB6_PODER3_REMESSA == "R"
    assert SB6_PODER3_RETORNO == "D"
    assert SB6_TIPO_TERCEIRO_NA_EMPRESA == "D"


def test_shipment_key_excludes_tpcf() -> None:
    assert SB6_SHIPMENT_KEY_FIELDS == ("B6_FILIAL", "B6_PRODUTO", "B6_IDENT")
    assert "B6_TPCF" not in SB6_SHIPMENT_KEY_FIELDS
    assert "B6_IDENTB6" not in SB6_SHIPMENT_KEY_FIELDS


def test_status_roundtrip() -> None:
    assert set(API_SHIPMENT_STATUS_VALUES) == {"completed", "partial", "no_return"}
    assert VIEW_TO_API_SHIPMENT_STATUS["PARCIAL"] == "partial"
    assert API_TO_VIEW_SHIPMENT_STATUS["no_return"] == "SEM RETORNO"


def test_ignored_test_product_is_configurable_default() -> None:
    assert DEFAULT_IGNORED_TEST_PRODUCTS == ("99999999",)
    assert VIEW_NAME == "dbo.VW_PD3_BENEF_RETORNOS"

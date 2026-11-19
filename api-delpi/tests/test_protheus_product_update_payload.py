"""Payload tests — product PUT partial-update contract and URL derivation.

Client contract v2: o cliente envia um subconjunto de campos elegíveis;
o use case expande para a representação completa via read-merge-write.
"""

from __future__ import annotations

import pytest

from app.application.services.integrations.protheus_product_field_catalog import (
    PRODUCT_FIELD_SPECS,
)
from app.application.services.integrations.protheus_product_payload import (
    build_upstream_product_update_body,
    merge_product_update_fields,
    normalize_product_update_fields,
    product_update_url,
    validate_product_code,
)
from app.domain.integrations.protheus_rest import ProtheusRestConfig, ProtheusRestError

FULL_PRODUCT = {
    "B1_GRUPO": "1045",
    "B1_DESC": "PESO PARA TESTE 6KG",
    "B1_REFEREN": "",
    "B1_REFCANT": "",
    "B1_CODDES": "",
    "B1_TIPO": "MC",
    "B1_YHOHS": "N",
    "B1_POSIPI": "72141010",
    "B1_LOCPAD": "01",
    "B1_UM": "PC",
    "B1_SEGUM": "",
    "B1_TE": "001",
    "B1_TS": "",
    "B1_PICMRET": "0.0",
    "B1_CONV": "0.0",
    "B1_TIPCONV": "M",
    "B1_TPMAT": "1",
    "B1_ESPECIE": "0",
    "B1_EX_NCM": "",
    "B1_EX_NBM": "",
    "B1_ORIGEM": "0",
}


def test_validate_product_code_ok() -> None:
    assert validate_product_code(" ABC123 ") == "ABC123"


def test_validate_product_code_rejects_bad() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        validate_product_code("A B!")
    assert exc.value.code == "PROTHEUS_PRODUCT_ID_INVALID"
    with pytest.raises(ProtheusRestError):
        validate_product_code("")
    with pytest.raises(ProtheusRestError):
        validate_product_code("X" * 16)


def test_normalize_accepts_valid_subset() -> None:
    out = normalize_product_update_fields(FULL_PRODUCT)
    assert out["B1_DESC"] == "PESO PARA TESTE 6KG"
    assert out["B1_REFEREN"] == ""
    assert set(out) == set(FULL_PRODUCT)


def test_normalize_accepts_single_field_partial() -> None:
    out = normalize_product_update_fields({"B1_DESC": "NOVA DESCRICAO"})
    assert out == {"B1_DESC": "NOVA DESCRICAO"}


def test_normalize_rejects_empty_delta() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({})
    assert exc.value.code == "PROTHEUS_PRODUCT_PAYLOAD_INVALID"


def test_merge_expands_delta_to_full_catalog() -> None:
    snapshot = {
        field: ("9" * spec["max_length"] if spec["kind"] == "N" else "S")
        for field, spec in PRODUCT_FIELD_SPECS.items()
    }
    snapshot["B1_DESC"] = "DESCRICAO ORIGINAL   "
    merged = merge_product_update_fields(
        snapshot=snapshot, changes={"B1_GRUPO": "2099"}
    )
    # merged cobre todo o catálogo menos B1_COD (identidade injetada
    # pelo body builder a partir do path — nunca do snapshot/delta).
    assert set(merged) == set(PRODUCT_FIELD_SPECS) - {"B1_COD"}
    assert merged["B1_GRUPO"] == "2099"
    assert merged["B1_DESC"] == "DESCRICAO ORIGINAL"


def test_merge_preserves_omitted_fields_from_snapshot() -> None:
    snapshot = {field: "" for field in PRODUCT_FIELD_SPECS}
    snapshot["B1_ESPECIE"] = "5"
    merged = merge_product_update_fields(
        snapshot=snapshot, changes={"B1_DESC": "NOVA"}
    )
    assert merged["B1_ESPECIE"] == "5"


def test_normalize_rejects_unknown_field() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_XPTO": "1"})
    assert exc.value.code == "PROTHEUS_PRODUCT_FIELD_UNKNOWN"


def test_normalize_rejects_identity_keys() -> None:
    for key in ("B1_COD", "codusr", "protheus_user_id"):
        with pytest.raises(ProtheusRestError) as exc:
            normalize_product_update_fields({**FULL_PRODUCT, key: "X"})
        assert exc.value.code == "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN"


def test_normalize_rejects_null_allows_empty() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_DESC": None})
    assert exc.value.code == "PROTHEUS_PRODUCT_PAYLOAD_INVALID"
    out = normalize_product_update_fields({**FULL_PRODUCT, "B1_REFEREN": ""})
    assert out["B1_REFEREN"] == ""


def test_normalize_rejects_oversized() -> None:
    # B1_DESC tem 120 caracteres no SX3 — 121 excede o limite.
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_DESC": "X" * 121})
    assert exc.value.code == "PROTHEUS_PRODUCT_FIELD_TOO_LONG"


def test_normalize_rejects_non_numeric_numeric_field() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        normalize_product_update_fields({**FULL_PRODUCT, "B1_PICMRET": "abc"})
    assert exc.value.code == "PROTHEUS_PRODUCT_PAYLOAD_INVALID"


def test_upstream_body_is_flat_b1() -> None:
    body = build_upstream_product_update_body(
        product_code="ABC123", fields=normalize_product_update_fields(FULL_PRODUCT)
    )
    assert body["B1_COD"] == "ABC123"
    assert body["B1_DESC"] == "PESO PARA TESTE 6KG"
    assert "codusr" not in body


def test_product_update_url_prod_shape() -> None:
    config = ProtheusRestConfig(
        username="u",
        password="p",
        base_url="http://192.168.1.231:8061",
        auth_path="/restall/api/oauth2/v1/token",
        suppliers_path="/restall/delpi/api/v1/suppliers",
    )
    assert (
        product_update_url(config)
        == "http://192.168.1.231:8061/restall/delpiproduto/v1/IncProduto/alterar"
    )


def test_product_update_url_tst_shape() -> None:
    config = ProtheusRestConfig(
        username="u",
        password="p",
        base_url="http://192.168.1.233:8701/rest",
        auth_path="/api/oauth2/v1/token",
        suppliers_path="/delpi/api/v1/suppliers",
    )
    assert (
        product_update_url(config)
        == "http://192.168.1.233:8701/rest/delpiproduto/v1/IncProduto/alterar"
    )


def test_product_update_url_fails_closed_without_marker() -> None:
    config = ProtheusRestConfig(
        username="u",
        password="p",
        base_url="http://example.invalid",
        auth_path="/api/oauth2/v1/token",
        suppliers_path="/api/v1/suppliers",
    )
    with pytest.raises(ProtheusRestError) as exc:
        product_update_url(config)
    assert exc.value.code == "PROTHEUS_CONFIG_INVALID"


# --- revisão independente: strict numeric, canonical merge, read-back ---


def test_normalize_rejects_scientific_and_empty_numeric() -> None:
    # lIsNumStr upstream: sem expoente, sem separador, sem vazio p/ N.
    for bad in ("1e-5", "1.2.3", "12,5", "", " ", "abc"):
        with pytest.raises(ProtheusRestError) as exc:
            normalize_product_update_fields(
                {**FULL_PRODUCT, "B1_PICMRET": bad}
            )
        assert exc.value.code == "PROTHEUS_PRODUCT_PAYLOAD_INVALID", bad
    for good in ("5.50", "-3", "0"):
        out = normalize_product_update_fields(
            {**FULL_PRODUCT, "B1_PICMRET": good}
        )
        assert out["B1_PICMRET"] == good


def test_merge_snapshot_numeric_canonical_form() -> None:
    from decimal import Decimal

    snapshot = {field: "" for field in PRODUCT_FIELD_SPECS}
    snapshot["B1_PICMRET"] = 5.0            # float -> "5"
    snapshot["B1_ESTSEG"] = Decimal("1E-5")  # pyodbc -> "0.00001"
    snapshot["B1_PESO"] = 0.00001            # float pequeno -> "0.00001"
    snapshot["B1_EMIN"] = 2                  # int -> "2"
    merged = merge_product_update_fields(snapshot=snapshot, changes={})
    assert merged["B1_PICMRET"] == "5"
    assert merged["B1_ESTSEG"] == "0.00001"
    assert merged["B1_PESO"] == "0.00001"
    assert merged["B1_EMIN"] == "2"


def test_canonical_number_never_corrupts_significant_digits() -> None:
    # Regressão OC-1: format(..,"f") truncava em 6 casas e rstrip("0")
    # comia zeros significativos de integrais (Decimal(10) virava "1").
    from decimal import Decimal

    from app.application.services.integrations.protheus_product_payload import (
        _canonical_number,
    )

    assert _canonical_number(Decimal("10")) == "10"
    assert _canonical_number(Decimal("100")) == "100"
    assert _canonical_number(10) == "10"
    assert _canonical_number(Decimal("1E-7")) == "0.0000001"
    assert _canonical_number(0.0000001) == "0.0000001"
    assert _canonical_number(Decimal("5.50")) == "5.5"
    assert _canonical_number(-3.25) == "-3.25"
    assert _canonical_number(0) == "0"


def test_merge_snapshot_none_stays_empty() -> None:
    snapshot = {field: "" for field in PRODUCT_FIELD_SPECS}
    snapshot["B1_DTCORTE"] = None  # data NULL -> "" (vazio legítimo)
    merged = merge_product_update_fields(snapshot=snapshot, changes={})
    assert merged["B1_DTCORTE"] == ""


def test_snapshot_value_matches_numeric_and_padded() -> None:
    from decimal import Decimal

    from app.application.services.integrations.protheus_product_payload import (
        snapshot_value_matches,
    )

    # "5.50" enviado ≡ 5.5 gravado; "" ≡ NULL/" " numericamente zero.
    assert snapshot_value_matches("B1_PICMRET", 5.5, "5.50")
    assert snapshot_value_matches("B1_PICMRET", Decimal("0"), "")
    assert snapshot_value_matches("B1_PICMRET", None, "")
    assert not snapshot_value_matches("B1_PICMRET", 6.0, "5.50")
    # caractere: padding à direita do banco é ignorado.
    assert snapshot_value_matches("B1_DESC", "TEXTO   ", "TEXTO")
    assert not snapshot_value_matches("B1_DESC", "OUTRO", "TEXTO")
    # data: vazio persistido ≡ "" enviado.
    assert snapshot_value_matches("B1_DTCORTE", "        ", "")
    assert snapshot_value_matches("B1_DTCORTE", "20260101", "20260101")

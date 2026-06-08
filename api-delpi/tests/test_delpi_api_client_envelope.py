import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))

from delpi_api_client.envelope import format_error_message, parse_envelope  # noqa: E402
from delpi_api_client.protheus_fields import coerce_yes_no, read_yes_no_label  # noqa: E402


def test_parse_envelope_extracts_data_meta_error() -> None:
    body = {
        "success": True,
        "message": "ok",
        "data": {"items": []},
        "meta": {"shape": "paged_list"},
        "error": None,
    }
    data, meta, error = parse_envelope(body)
    assert data == {"items": []}
    assert meta == {"shape": "paged_list"}
    assert error is None


def test_parse_envelope_fallback_for_raw_dict() -> None:
    body = {"items": [1]}
    data, meta, error = parse_envelope(body)
    assert data == {"items": [1]}
    assert meta is None
    assert error is None


def test_format_error_message_with_code() -> None:
    message = format_error_message(
        {
            "success": False,
            "message": "Produto não encontrado",
            "error": {"code": "PRODUCT_NOT_FOUND", "recoverable": False},
        }
    )
    assert message == "[PRODUCT_NOT_FOUND] Produto não encontrado"


def test_coerce_yes_no_accepts_normalized_and_legacy() -> None:
    assert coerce_yes_no(True) is True
    assert coerce_yes_no("SIM") is True
    assert coerce_yes_no("NAO") is False


def test_read_yes_no_label_from_normalized_payload() -> None:
    assert read_yes_no_label(
        {"exclusive_raw_material": True, "exclusive_raw_material_label": "Sim"},
        "exclusive_raw_material",
    ) == "Sim"

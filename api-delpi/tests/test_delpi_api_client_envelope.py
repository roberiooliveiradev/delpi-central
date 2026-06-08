import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))

from delpi_api_client.envelope import format_error_message, parse_envelope  # noqa: E402


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

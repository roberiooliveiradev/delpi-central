from app.domain.services.quality.nonconformity_display_service import (
    format_nonconformity_code,
    resolve_nonconformity_status_label,
    resolve_nonconformity_type_label,
)


def test_resolve_nonconformity_type_label_totvs_codes() -> None:
    assert resolve_nonconformity_type_label("1") == "Interna"
    assert resolve_nonconformity_type_label("2") == "Cliente"
    assert resolve_nonconformity_type_label("3") == "Fornecedor"


def test_resolve_nonconformity_status_label_totvs_codes() -> None:
    assert resolve_nonconformity_status_label("1") == "Registrada"
    assert resolve_nonconformity_status_label("2") == "Em análise"
    assert resolve_nonconformity_status_label("3") == "Procede"
    assert resolve_nonconformity_status_label("4") == "Não procede"
    assert resolve_nonconformity_status_label("5") == "Cancelada"


def test_format_nonconformity_code_current_year() -> None:
    assert format_nonconformity_code("000000002292026") == "229/2026"


def test_format_nonconformity_code_legacy_year() -> None:
    assert format_nonconformity_code("000000000012004") == "1/2004"


def test_format_nonconformity_code_short_sequence() -> None:
    assert format_nonconformity_code("000000000782026") == "78/2026"


def test_format_nonconformity_code_empty() -> None:
    assert format_nonconformity_code("") is None
    assert format_nonconformity_code(None) is None

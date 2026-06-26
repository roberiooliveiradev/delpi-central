from app.domain.services.quality.nonconformity_display_service import (
    format_nonconformity_code,
)


def test_format_nonconformity_code_current_year() -> None:
    assert format_nonconformity_code("000000002292026") == "229/2026"


def test_format_nonconformity_code_legacy_year() -> None:
    assert format_nonconformity_code("000000000012004") == "1/2004"


def test_format_nonconformity_code_short_sequence() -> None:
    assert format_nonconformity_code("000000000782026") == "78/2026"


def test_format_nonconformity_code_empty() -> None:
    assert format_nonconformity_code("") is None
    assert format_nonconformity_code(None) is None

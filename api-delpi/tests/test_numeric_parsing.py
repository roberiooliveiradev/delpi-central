"""Regressão do parser numérico canônico (blank ≠ float)."""

from app.application.shared.numeric_parsing import to_optional_float


def test_to_optional_float_treats_blank_as_none() -> None:
    assert to_optional_float("") is None
    assert to_optional_float("   ") is None
    assert to_optional_float(None) is None
    assert to_optional_float("12.5") == 12.5
    assert to_optional_float(0) == 0.0

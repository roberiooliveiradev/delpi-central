"""Regressão: blank/inválido não estoura float('')."""

from si_app.shared.numeric_parsing import optional_float_map, to_optional_float


def test_to_optional_float_treats_blank_as_none() -> None:
    assert to_optional_float("") is None
    assert to_optional_float("   ") is None
    assert to_optional_float(None) is None
    assert to_optional_float("12.5") == 12.5
    assert to_optional_float(0) == 0.0
    assert to_optional_float("x") is None


def test_optional_float_map_normalizes_blank_entries() -> None:
    assert optional_float_map({"01": "", "02": "10", "x": None}) == {
        "01": None,
        "02": 10.0,
        "x": None,
    }

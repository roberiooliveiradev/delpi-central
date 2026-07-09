from app.domain.services.quality.ppm_product_scope import (
    PLUGS_FINISHED_PRODUCT_PREFIX,
    normalize_ppm_product_prefix,
)


def test_plugs_prefix_constant() -> None:
    assert PLUGS_FINISHED_PRODUCT_PREFIX == "9048"


def test_normalize_ppm_product_prefix_accepts_digits() -> None:
    assert normalize_ppm_product_prefix("9048") == "9048"


def test_normalize_ppm_product_prefix_rejects_invalid() -> None:
    try:
        normalize_ppm_product_prefix("9048*")
    except ValueError as exc:
        assert "dígitos" in str(exc)
    else:
        raise AssertionError("expected ValueError")

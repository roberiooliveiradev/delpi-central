"""Escopos de produto para cálculo de PPM (prefixos de código acabado)."""

PLUGS_FINISHED_PRODUCT_PREFIX = "9048"
COMPONENTS_FINISHED_PRODUCT_PREFIX = "9026"


def normalize_ppm_product_prefix(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    if not cleaned.isdigit():
        raise ValueError("product_prefix deve conter apenas dígitos.")

    return cleaned

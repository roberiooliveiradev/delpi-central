from __future__ import annotations

import re

from production_control_app.domain.errors import Product3DModelInvalid

_CODE_PATTERN = re.compile(r"^[\dA-Z]+(?:-\d+)?$")


def normalize_product_code(code: str) -> str:
    """Normaliza o código DELPI do produto da OP (PI ou PA)."""
    normalized = str(code or "").strip().upper()
    if not normalized or ".." in normalized or "/" in normalized or "\\" in normalized:
        raise Product3DModelInvalid("Informe um código de produto válido.")
    if not _CODE_PATTERN.fullmatch(normalized):
        raise Product3DModelInvalid("Informe um código de produto válido.")
    return normalized

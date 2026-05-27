from __future__ import annotations

import re

SOURCE_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,127}$")


def normalize_indicator_source_key(source_key: str | None) -> str | None:
    normalized = (source_key or "").strip()
    return normalized or None


def validate_indicator_source_key(
    source_key: str | None,
    *,
    is_active: bool,
) -> None:
    normalized = normalize_indicator_source_key(source_key)

    if is_active and not normalized:
        raise ValueError(
            "source_key é obrigatório para indicadores ativos "
            "(medições automáticas e metas nos dashboards departamentais)."
        )

    if not normalized:
        return

    if not SOURCE_KEY_PATTERN.match(normalized):
        raise ValueError(
            "source_key inválido: use letras minúsculas, números e underscore "
            "(ex.: commercial_rol, production_otd)."
        )

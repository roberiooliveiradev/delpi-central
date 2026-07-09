"""Resolução de filtros de texto para consultas QI2 (não conformidades)."""

from app.domain.services.quality.nonconformity_display_service import (
    NONCONFORMITY_STATUS_LABELS,
)


def match_nonconformity_status_codes(query: str | None) -> list[str] | None:
    """Resolve códigos QI2_STATUS cujo rótulo ou código contém o termo buscado."""
    if query is None:
        return None

    term = str(query).strip().lower()
    if not term:
        return None

    matches = [
        code
        for code, label in NONCONFORMITY_STATUS_LABELS.items()
        if term in label.lower() or term in code.lower()
    ]

    return matches or None

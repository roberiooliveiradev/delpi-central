"""Resolução de filtros de texto para consultas QI2 (não conformidades)."""

from app.domain.services.quality.nonconformity_display_service import (
    NONCONFORMITY_STATUS_LABELS,
)

# Filtro HTTP `type` → códigos QI2_TIPO (SX3).
# `external` permanece como atalho legado (cliente + fornecedor).
_NONCONFORMITY_FILTER_TYPE_QI2_CODES: dict[str, list[str]] = {
    "internal": ["1"],
    "customer": ["2"],
    "supplier": ["3"],
    "external": ["2", "3"],
}

NONCONFORMITY_FILTER_TYPE_VALUES = frozenset(
    {*_NONCONFORMITY_FILTER_TYPE_QI2_CODES.keys(), "all"}
)


def normalize_nonconformity_filter_type(filter_type: str | None) -> str:
    """Valida e normaliza o filtro `type` da listagem/série de NC."""
    key = str(filter_type or "").strip().lower() or "all"
    if key not in NONCONFORMITY_FILTER_TYPE_VALUES:
        allowed = ", ".join(sorted(NONCONFORMITY_FILTER_TYPE_VALUES))
        raise ValueError(f"type deve ser {allowed}")
    return key


def qi2_tipo_codes_for_filter(filter_type: str | None) -> list[str] | None:
    """Resolve códigos QI2_TIPO para o filtro `type` da listagem/série de NC.

    Retorna ``None`` quando não há restrição (``all`` / vazio).
    """
    key = normalize_nonconformity_filter_type(filter_type)
    if key == "all":
        return None
    return list(_NONCONFORMITY_FILTER_TYPE_QI2_CODES[key])


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

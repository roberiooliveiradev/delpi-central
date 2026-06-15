"""Fragmentos SQL reutilizáveis — mini-aplicadores (ferramentas)."""

from __future__ import annotations

from app.application.services.product.protheus_field_normalizer import parse_protheus_yes_no

_PROTHEUS_BLOCKED_VALUES = frozenset({"1", "SIM", "SIM_SC2", "S"})
_PROTHEUS_UNBLOCKED_VALUES = frozenset({"2", "NAO", "NÃO", "N", ""})


def is_protheus_product_blocked(raw: object) -> bool:
    if raw is None:
        return False
    normalized = str(raw).strip().upper()
    if normalized in _PROTHEUS_BLOCKED_VALUES:
        return True
    if normalized in _PROTHEUS_UNBLOCKED_VALUES:
        return False
    parsed = parse_protheus_yes_no(normalized)
    return parsed is True


def bloqueado_filter_sql() -> str:
    """Exclui produtos bloqueados no Protheus (B1_MSBLQL = Sim / 1)."""
    return (
        "(RTRIM(LTRIM(SB1.B1_MSBLQL)) NOT IN ('1', 'SIM') "
        "OR SB1.B1_MSBLQL IS NULL OR RTRIM(LTRIM(SB1.B1_MSBLQL)) = '')"
    )


def codigo_prefix_pattern(term: str) -> str:
    return f"{term.strip()}%"


def codigo_filter_sql() -> str:
    """Busca pelo início do código exibido (B1_COD ou grupo + '-' + B1_COD)."""
    return (
        "(RTRIM(LTRIM(SB1.B1_COD)) LIKE ? "
        "OR RTRIM(LTRIM(SB1.B1_GRUPO)) + '-' + RTRIM(LTRIM(SB1.B1_COD)) LIKE ?)"
    )

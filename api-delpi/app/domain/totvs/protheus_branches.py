"""Filiais Protheus — escopo canônico de consulta (Todas | 01 | 02)."""

from __future__ import annotations

BRANCH_SCOPE_TODAS = "Todas"
PROTHEUS_BRANCH_CODES: tuple[str, ...] = ("01", "02")
BRANCH_SCOPE_VALUES: tuple[str, ...] = (BRANCH_SCOPE_TODAS, *PROTHEUS_BRANCH_CODES)

# Alias histórico — só códigos de filial (detalhe / chave composta).
BRANCH_CODE_VALUES = PROTHEUS_BRANCH_CODES


def is_all_branches(scope: str) -> bool:
    return str(scope or "").strip() == BRANCH_SCOPE_TODAS


def normalize_branch_scope(raw: str | None) -> str:
    """Retorna ``Todas`` | ``01`` | ``02``. Vazio/None → Todas."""
    normalized = str(raw or "").strip()
    if not normalized:
        return BRANCH_SCOPE_TODAS
    if normalized not in BRANCH_SCOPE_VALUES:
        raise ValueError("branch inválida. Use Todas, 01 ou 02.")
    return normalized


def normalize_branch_code(raw: str | None) -> str:
    """Exige filial concreta 01 ou 02 (sem Todas)."""
    normalized = str(raw or "").strip()
    if normalized not in PROTHEUS_BRANCH_CODES:
        raise ValueError("branch inválida. Use 01 ou 02.")
    return normalized


def branch_filter_sql(column: str, scope: str) -> tuple[str, list]:
    """Todas → sem predicado; 01/02 → ``column = ?``.

    Retorno: (clause, params). Clause vazia = não filtrar por filial.
    """
    resolved = normalize_branch_scope(scope)
    if is_all_branches(resolved):
        return "", []
    return f"{column} = ?", [resolved]


def append_branch_filter(
    clauses: list[str],
    params: list,
    column: str,
    scope: str,
) -> None:
    clause, branch_params = branch_filter_sql(column, scope)
    if clause:
        clauses.append(clause)
        params.extend(branch_params)

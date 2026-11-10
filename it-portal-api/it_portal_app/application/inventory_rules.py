"""Regras de aplicação comuns aos cadastros do inventário (E2A+)."""

from __future__ import annotations

from dataclasses import replace
from typing import TypeVar

from it_portal_app.domain.errors import ConflictError, ValidationError

MAX_PAGE_SIZE = 100
HISTORY_LIMIT = 50
ARCHIVE_FILTERS = ("active", "archived", "all")
SEARCH_MAX = 120

Q = TypeVar("Q")


def revision_conflict() -> ConflictError:
    return ConflictError(
        "revision_conflict",
        "O registro foi alterado por outra pessoa. Recarregue e tente novamente.",
    )


def reference_not_found(field: str, message: str) -> ValidationError:
    return ValidationError("reference_not_found", message, {"fields": {field: message}})


def normalize_listing(
    query: Q,
    *,
    sort_keys: tuple[str, ...],
    choices: dict[str, tuple[str, ...]],
) -> Q:
    """Valida filtros fechados, ordenação e paginação de uma consulta de listagem."""
    errors: dict[str, str] = {}
    for field, allowed in choices.items():
        value = getattr(query, field)
        if value and value not in allowed:
            errors[field] = "Filtro inválido."
    if query.archived not in ARCHIVE_FILTERS:
        errors["archived"] = "Filtro de arquivamento inválido."
    if query.sort not in sort_keys:
        errors["sort"] = "Ordenação inválida."
    if query.direction not in ("asc", "desc"):
        errors["direction"] = "Direção inválida."
    if errors:
        raise ValidationError("invalid_query", "Filtros inválidos.", {"fields": errors})
    q = (query.q or "").strip() or None
    return replace(
        query,
        q=q[:SEARCH_MAX] if q else None,
        page=max(1, query.page),
        page_size=min(MAX_PAGE_SIZE, max(1, query.page_size)),
    )


def page_result(items: list[dict], total: int, query) -> dict:
    return {"items": items, "total": total, "page": query.page, "page_size": query.page_size}

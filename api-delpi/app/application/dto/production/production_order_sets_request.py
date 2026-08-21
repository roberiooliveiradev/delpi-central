"""DTOs — conjuntos de ordens de produção incompletos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.domain.production.production_order_sets_scope import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    VALID_PRODUCTION_ORDER_SET_BRANCHES,
)
from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    normalize_branch_scope,
)


def _parse_iso_date(value: str | None) -> date | None:
    if not value or not str(value).strip():
        return None
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Data inválida (use AAAA-MM-DD): {value!r}") from exc


@dataclass(frozen=True, slots=True)
class IncompleteOrderSetsRequest:
    """Filtro do detector. ``branch`` nulo = consolidado nas filiais válidas.

    ``issued_from`` recorta pela emissão da OP mãe. A Delpi carrega centenas de
    conjuntos abertos desde os anos 2000 que nunca foram encerrados; quem
    consome decide a partir de quando o conjunto ainda merece atenção.
    """

    branch: str | None
    issued_from: date | None
    page: int
    page_size: int

    @classmethod
    def from_params(
        cls,
        *,
        branch: str | None = None,
        issued_from: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> IncompleteOrderSetsRequest:
        scope = normalize_branch_scope(branch)
        resolved_branch = None if scope == BRANCH_SCOPE_ALL else scope
        if resolved_branch and resolved_branch not in VALID_PRODUCTION_ORDER_SET_BRANCHES:
            raise ValueError("branch inválida. Use all, 01 ou 02.")

        resolved_page = int(page or 1)
        if resolved_page < 1:
            raise ValueError("page deve ser maior ou igual a 1.")

        resolved_page_size = int(page_size or DEFAULT_PAGE_SIZE)
        if not 1 <= resolved_page_size <= MAX_PAGE_SIZE:
            raise ValueError(f"page_size deve estar entre 1 e {MAX_PAGE_SIZE}.")

        return cls(
            branch=resolved_branch,
            issued_from=_parse_iso_date(issued_from),
            page=resolved_page,
            page_size=resolved_page_size,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def filter_kwargs(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "issued_from": self.issued_from.strftime("%Y%m%d") if self.issued_from else None,
        }

    def filters_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch or BRANCH_SCOPE_ALL,
            "issued_from": self.issued_from.isoformat() if self.issued_from else None,
        }

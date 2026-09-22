"""DTOs — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.domain.production.shared_structure_intermediates_scope import (
    DEFAULT_MOVEMENT_LOOKBACK_DAYS,
    DEFAULT_PAGE_SIZE,
    MAX_MOVEMENT_LOOKBACK_DAYS,
    MAX_PAGE_SIZE,
    VALID_BRANCHES,
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
class SharedStructureIntermediatesRequest:
    branch: str | None
    movement_from: date
    movement_to_exclusive: date
    page: int
    page_size: int

    @classmethod
    def from_params(
        cls,
        *,
        branch: str | None = None,
        movement_from: str | None = None,
        lookback_days: int | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        today: date | None = None,
    ) -> SharedStructureIntermediatesRequest:
        scope = normalize_branch_scope(branch)
        resolved_branch = None if scope == BRANCH_SCOPE_ALL else scope
        if resolved_branch and resolved_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use all, 01 ou 02.")

        resolved_page = int(page or 1)
        if resolved_page < 1:
            raise ValueError("page deve ser maior ou igual a 1.")

        resolved_page_size = int(page_size or DEFAULT_PAGE_SIZE)
        if not 1 <= resolved_page_size <= MAX_PAGE_SIZE:
            raise ValueError(f"page_size deve estar entre 1 e {MAX_PAGE_SIZE}.")

        reference = today or date.today()
        parsed_from = _parse_iso_date(movement_from)
        if parsed_from:
            resolved_from = parsed_from
        else:
            days = int(lookback_days or DEFAULT_MOVEMENT_LOOKBACK_DAYS)
            if days < 1 or days > MAX_MOVEMENT_LOOKBACK_DAYS:
                raise ValueError(
                    f"lookback_days deve estar entre 1 e {MAX_MOVEMENT_LOOKBACK_DAYS}."
                )
            resolved_from = reference - timedelta(days=days)

        if resolved_from >= reference:
            raise ValueError("movement_from deve ser anterior a hoje.")

        return cls(
            branch=resolved_branch,
            movement_from=resolved_from,
            movement_to_exclusive=reference + timedelta(days=1),
            page=resolved_page,
            page_size=resolved_page_size,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def filter_kwargs(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "movement_from": self.movement_from.strftime("%Y%m%d"),
            "movement_to_exclusive": self.movement_to_exclusive.strftime("%Y%m%d"),
        }

    def filters_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch or BRANCH_SCOPE_ALL,
            "movement_from": self.movement_from.isoformat(),
            "movement_to_exclusive": (
                self.movement_to_exclusive - timedelta(days=1)
            ).isoformat(),
        }

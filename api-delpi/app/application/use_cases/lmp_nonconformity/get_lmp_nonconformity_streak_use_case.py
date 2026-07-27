from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from app.domain.services.lmp.lmp_nonconformity_streak_service import (
    compute_lmp_nc_streak,
)


class LmpNonconformityStreakRepository(Protocol):
    def list_occurrence_dates(self) -> list[date]: ...


class GetLmpNonconformityStreakUseCase:
    def __init__(self, repository: LmpNonconformityStreakRepository) -> None:
        self._repository = repository

    def execute(self, *, as_of: date | None = None) -> dict[str, Any]:
        return compute_lmp_nc_streak(
            self._repository.list_occurrence_dates(),
            as_of=as_of or date.today(),
        )

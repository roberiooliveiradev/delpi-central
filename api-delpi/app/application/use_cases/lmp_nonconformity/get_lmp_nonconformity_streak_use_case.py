from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from app.domain.services.lmp.lmp_nonconformity_streak_service import (
    compute_lmp_nc_streak,
)


class LmpNonconformityStreakRepository(Protocol):
    def list_occurrence_dates(self) -> list[date]: ...


class LmpEarliestOvDateRepository(Protocol):
    def get_earliest_ov_date(self) -> date | None: ...


class GetLmpNonconformityStreakUseCase:
    def __init__(
        self,
        repository: LmpNonconformityStreakRepository,
        *,
        lmp_repository: LmpEarliestOvDateRepository | None = None,
    ) -> None:
        self._repository = repository
        self._lmp_repository = lmp_repository

    def execute(self, *, as_of: date | None = None) -> dict[str, Any]:
        as_of_date = as_of or date.today()
        occurrence_dates = self._repository.list_occurrence_dates()
        reference_start_date: date | None = None
        if not occurrence_dates and self._lmp_repository is not None:
            reference_start_date = self._lmp_repository.get_earliest_ov_date()
        return compute_lmp_nc_streak(
            occurrence_dates,
            as_of=as_of_date,
            reference_start_date=reference_start_date,
        )

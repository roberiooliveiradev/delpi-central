from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.dto.financeiro_inadimplencia.period_filter_request import (
    PeriodFilterRequest,
)


@dataclass(frozen=True, slots=True)
class InadimplenciaQueryRequest:
    start_date: str | None = None
    end_date: str | None = None

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> InadimplenciaQueryRequest:
        period = PeriodFilterRequest.from_query(
            start_date=start_date,
            end_date=end_date,
        )
        return cls(start_date=period.start_date, end_date=period.end_date)

    def resolve_period(
        self,
        *,
        today: date | None = None,
    ) -> tuple[date, date, str]:
        return PeriodFilterRequest(
            start_date=self.start_date,
            end_date=self.end_date,
        ).resolve_period(today=today)

    def periodo_dict(self, *, today: date | None = None) -> dict[str, str]:
        return PeriodFilterRequest(
            start_date=self.start_date,
            end_date=self.end_date,
        ).periodo_dict(today=today)

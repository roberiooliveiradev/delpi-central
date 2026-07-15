from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.dto.financeiro_inadimplencia.period_filter_request import (
    PeriodFilterRequest,
)
from app.application.dto.financeiro_inadimplencia.query_request import (
    InadimplenciaQueryRequest,
)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class InadimplenciaMensalQueryRequest:
    start_date: str | None = None
    end_date: str | None = None
    customer_code: str | None = None
    store_code: str | None = None

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        customer_code: str | None = None,
        store_code: str | None = None,
    ) -> InadimplenciaMensalQueryRequest:
        period = PeriodFilterRequest.from_query(
            start_date=start_date,
            end_date=end_date,
        )
        return cls(
            start_date=period.start_date,
            end_date=period.end_date,
            customer_code=_normalize_optional_text(customer_code),
            store_code=_normalize_optional_text(store_code),
        )

    def to_base_request(self) -> InadimplenciaQueryRequest:
        return InadimplenciaQueryRequest(
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def resolve_period(
        self,
        *,
        today: date | None = None,
    ) -> tuple[date, date, str]:
        return self.to_base_request().resolve_period(today=today)

    def periodo_dict(self, *, today: date | None = None) -> dict[str, str]:
        return self.to_base_request().periodo_dict(today=today)

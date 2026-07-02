from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.financeiro_despesas_centro_custo.period_filter_request import (
    PeriodFilterRequest,
)

DEFAULT_RANKING_LIMIT = 10
MAX_RANKING_LIMIT = 50


@dataclass(frozen=True, slots=True)
class DespesasCentroCustoQueryRequest:
    start_date: str
    end_date: str
    branch: str | None = None
    cost_center: str | None = None
    supplier_code: str | None = None
    supplier_store: str | None = None
    limit: int | None = None

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        limit: int | None = None,
    ) -> DespesasCentroCustoQueryRequest:
        period = PeriodFilterRequest.from_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return cls(
            start_date=period.start_date,
            end_date=period.end_date,
            branch=period.branch,
            cost_center=cls._normalize_optional_text(cost_center),
            supplier_code=cls._normalize_optional_text(supplier_code),
            supplier_store=cls._normalize_optional_text(supplier_store),
            limit=limit,
        )

    @staticmethod
    def _normalize_optional_text(value: str | None) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    def resolve_protheus_period(self) -> tuple[str, str]:
        return PeriodFilterRequest(
            start_date=self.start_date,
            end_date=self.end_date,
            branch=self.branch,
        ).resolve_protheus_period()

    def resolve_ranking_limit(
        self,
        *,
        default: int = DEFAULT_RANKING_LIMIT,
        maximum: int = MAX_RANKING_LIMIT,
    ) -> int:
        if self.limit is None:
            return default

        return min(max(int(self.limit), 1), maximum)

    def periodo_dict(self) -> dict[str, str]:
        start, end = self.resolve_protheus_period()
        return {"data_inicio": start, "data_fim": end}

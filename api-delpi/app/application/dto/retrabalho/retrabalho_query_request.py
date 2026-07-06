from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.retrabalho.retrabalho_period import RetrabalhoPeriod
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_query_settings import (
    DEFAULT_RANKING_LIMIT,
    MAX_RANKING_LIMIT,
)


@dataclass(frozen=True, slots=True)
class RetrabalhoQueryRequest:
    period: RetrabalhoPeriod
    recurso: str | None = None
    centro_custo: str | None = None
    codigo_operador: str | None = None
    order_by: str = "horas"
    limit: int | None = None

    @classmethod
    def from_query(
        cls,
        *,
        filial: str | None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> RetrabalhoQueryRequest:
        period = RetrabalhoPeriod.resolve(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        normalized_order = str(order_by or "horas").strip().lower() or "horas"
        if normalized_order not in {"horas", "custo"}:
            raise ValueError('orderBy inválido. Use "horas" ou "custo".')

        return cls(
            period=period,
            recurso=cls._normalize_optional(recurso),
            centro_custo=cls._normalize_optional(centro_custo),
            codigo_operador=cls._normalize_optional(codigo_operador),
            order_by=normalized_order,
            limit=limit,
        )

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

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
        return self.period.periodo_dict()

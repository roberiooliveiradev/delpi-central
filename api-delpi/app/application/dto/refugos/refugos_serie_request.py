from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.refugos.refugos_period import RefugosPeriod
from app.infrastructure.persistence.totvs.refugos.refugos_query_settings import (
    SERIE_AUTO_DAY_MAX_DAYS,
    SERIE_GRANULARITIES,
)


@dataclass(frozen=True, slots=True)
class RefugosSerieRequest:
    period: RefugosPeriod
    granularity: str
    mp: str | None = None
    pa: str | None = None
    op: str | None = None
    motivo: str | None = None
    recurso: str | None = None

    @classmethod
    def from_query(
        cls,
        *,
        filial: str | None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        granularity: str | None = None,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> RefugosSerieRequest:
        period = RefugosPeriod.resolve(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        raw = (granularity or "auto").strip().lower() or "auto"
        if raw not in SERIE_GRANULARITIES:
            raise ValueError("granularity inválida. Use day, month ou auto.")

        return cls(
            period=period,
            granularity=cls._resolve_granularity(raw, period),
            mp=cls._normalize_optional(mp),
            pa=cls._normalize_optional(pa),
            op=cls._normalize_optional(op),
            motivo=cls._normalize_optional(motivo),
            recurso=cls._normalize_optional(recurso),
        )

    @staticmethod
    def _resolve_granularity(requested: str, period: RefugosPeriod) -> str:
        if requested in {"day", "month"}:
            return requested
        span_days = (period.end_date - period.start_date).days + 1
        return "day" if span_days <= SERIE_AUTO_DAY_MAX_DAYS else "month"

    @staticmethod
    def _normalize_optional(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def periodo_dict(self) -> dict[str, str]:
        return self.period.periodo_dict()

    def filter_kwargs(self) -> dict:
        return {
            "mp": self.mp,
            "pa": self.pa,
            "op": self.op,
            "motivo": self.motivo,
            "recurso": self.recurso,
        }

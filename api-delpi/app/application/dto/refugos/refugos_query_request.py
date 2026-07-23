from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.refugos.refugos_period import RefugosPeriod
from app.infrastructure.persistence.totvs.refugos.refugos_query_settings import (
    DEFAULT_RANKING_LIMIT,
    MAX_RANKING_LIMIT,
    RANKING_DIMENSIONS,
)


@dataclass(frozen=True, slots=True)
class RefugosQueryRequest:
    period: RefugosPeriod
    dimension: str | None = None
    mp: str | None = None
    pa: str | None = None
    op: str | None = None
    motivo: str | None = None
    recurso: str | None = None
    limit: int | None = None

    @classmethod
    def from_query(
        cls,
        *,
        filial: str | None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        dimension: str | None = None,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
        limit: int | None = None,
        require_filial: bool = True,
    ) -> RefugosQueryRequest:
        period = RefugosPeriod.resolve(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
            require_filial=require_filial,
        )
        normalized_dimension = cls._normalize_optional(dimension)
        if normalized_dimension is not None:
            normalized_dimension = normalized_dimension.lower()
            if normalized_dimension not in RANKING_DIMENSIONS:
                raise ValueError(
                    "dimension inválida. Use: motivo, materia_prima, "
                    "produto_acabado, centro_trabalho, colaborador."
                )

        return cls(
            period=period,
            dimension=normalized_dimension,
            mp=cls._normalize_optional(mp),
            pa=cls._normalize_optional(pa),
            op=cls._normalize_optional(op),
            motivo=cls._normalize_optional(motivo),
            recurso=cls._normalize_optional(recurso),
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

    def filter_kwargs(self) -> dict:
        return {
            "mp": self.mp,
            "pa": self.pa,
            "op": self.op,
            "motivo": self.motivo,
            "recurso": self.recurso,
        }

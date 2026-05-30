"""Resolve a data alvo de programação de produção a partir da mensagem do usuário."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.services.chat_temporal_intent_service import (
    ChatTemporalIntentService,
    ResolvedTemporalPoint,
)


@dataclass(frozen=True)
class ResolvedProductionScheduleDate:
    target_date: date
    label: str
    use_getdate: bool = False

    @property
    def title(self) -> str:
        return f"Produtos programados para produção {self.label}"

    @property
    def empty_message(self) -> str:
        return f"Nenhum produto programado para produção {self.label}."

    @property
    def sql_date_declaration(self) -> str:
        if self.use_getdate:
            return "DECLARE @DATA DATE = CAST(GETDATE() AS DATE);"

        return f"DECLARE @DATA DATE = '{self.target_date.isoformat()}';"


class ChatSqlProductionScheduleDateService:
    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        today: date | None = None,
    ) -> ResolvedProductionScheduleDate:
        point = ChatTemporalIntentService.resolve_point(
            message,
            today=today,
            default_today=True,
        )
        return cls._from_point(point or cls._fallback_today(today))

    @classmethod
    def infer_from_sql(cls, sql: str | None) -> ResolvedProductionScheduleDate | None:
        point = ChatTemporalIntentService.infer_point_from_sql(sql)
        if not point:
            return None
        return cls._from_point(point)

    @classmethod
    def _fallback_today(cls, today: date | None) -> ResolvedTemporalPoint:
        reference = today or date.today()
        return ResolvedTemporalPoint(
            target_date=reference,
            label="hoje",
            kind="today",
            use_reference_today=True,
        )

    @classmethod
    def _from_point(cls, point: ResolvedTemporalPoint) -> ResolvedProductionScheduleDate:
        return ResolvedProductionScheduleDate(
            target_date=point.target_date,
            label=point.label,
            use_getdate=point.use_reference_today,
        )

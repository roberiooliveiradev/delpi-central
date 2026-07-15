from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.application.dto.financeiro_inadimplencia.constantes import (
    MAX_PERIOD_MONTHS,
    PERIODO_PADRAO_ROTULO,
    PERIODO_PERSONALIZADO_ROTULO,
)


def _add_months(value: date, months: int) -> date:
    year = value.year + (value.month - 1 + months) // 12
    month = (value.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _months_between(start: date, end_exclusive: date) -> int:
    return (end_exclusive.year - start.year) * 12 + (
        end_exclusive.month - start.month
    )


def parse_iso_date(value: str, *, field_name: str) -> date:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{field_name} inválida. Use o formato YYYY-MM-DD.")

    try:
        if len(normalized) == 8 and normalized.isdigit():
            return datetime.strptime(normalized, "%Y%m%d").date()
        return datetime.strptime(normalized[:10], "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            f"{field_name} inválida. Use o formato YYYY-MM-DD."
        ) from exc


def resolve_default_period(*, today: date | None = None) -> tuple[date, date]:
    """Retorna (start_inclusive, end_exclusive) dos últimos 12 meses completos."""
    reference = today or date.today()
    end_exclusive = date(reference.year, reference.month, 1)
    start = _add_months(end_exclusive, -12)
    return start, end_exclusive


@dataclass(frozen=True, slots=True)
class PeriodFilterRequest:
    start_date: str | None = None
    end_date: str | None = None

    @classmethod
    def from_query(
        cls,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> PeriodFilterRequest:
        normalized_start = str(start_date).strip() if start_date is not None else None
        normalized_end = str(end_date).strip() if end_date is not None else None

        if normalized_start == "":
            normalized_start = None
        if normalized_end == "":
            normalized_end = None

        if (normalized_start is None) ^ (normalized_end is None):
            raise ValueError(
                "Informe start_date e end_date juntos, ou omita ambos para "
                "usar o padrão dos últimos 12 meses completos."
            )

        return cls(start_date=normalized_start, end_date=normalized_end)

    def resolve_period(
        self,
        *,
        today: date | None = None,
    ) -> tuple[date, date, str]:
        """
        Resolve o período analítico.

        Semântica da fonte:
          MES_REFERENCIA >= data_inicio
          MES_REFERENCIA < data_fim_exclusiva
        """
        if self.start_date is None and self.end_date is None:
            start, end_exclusive = resolve_default_period(today=today)
            return start, end_exclusive, PERIODO_PADRAO_ROTULO

        assert self.start_date is not None and self.end_date is not None
        start = parse_iso_date(self.start_date, field_name="start_date")
        end_exclusive = parse_iso_date(self.end_date, field_name="end_date")

        if start >= end_exclusive:
            raise ValueError(
                "start_date deve ser anterior ao limite final exclusivo (end_date)."
            )

        span_months = _months_between(start, end_exclusive)
        if span_months <= 0:
            raise ValueError("O período informado é inválido.")
        if span_months > MAX_PERIOD_MONTHS:
            raise ValueError(
                f"O período máximo permitido é de {MAX_PERIOD_MONTHS} meses."
            )

        return start, end_exclusive, PERIODO_PERSONALIZADO_ROTULO

    def periodo_dict(self, *, today: date | None = None) -> dict[str, str]:
        start, end_exclusive, rotulo = self.resolve_period(today=today)
        return {
            "data_inicio": start.isoformat(),
            "data_fim_exclusiva": end_exclusive.isoformat(),
            "rotulo": rotulo,
        }

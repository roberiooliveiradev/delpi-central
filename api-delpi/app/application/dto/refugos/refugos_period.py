from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.quality.refugos.refugos_scope import VALID_REFUGOS_BRANCHES
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.infrastructure.persistence.totvs.refugos.refugos_query_settings import (
    MAX_MONTHS_WINDOW,
)


def _months_inclusive(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


@dataclass(frozen=True, slots=True)
class RefugosPeriod:
    start_date: date
    end_date: date
    filial: str | None

    @classmethod
    def resolve(
        cls,
        *,
        filial: str | None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        require_filial: bool = True,
    ) -> RefugosPeriod:
        normalized_filial = str(filial or "").strip() or None
        if normalized_filial is None:
            if require_filial:
                raise ValueError("filial é obrigatória.")
        elif normalized_filial not in VALID_REFUGOS_BRANCHES:
            raise ValueError('filial inválida. Use "01" ou "02".')

        utils = Utils()
        parsed_start = utils.parse_date(data_inicio) if data_inicio else None
        parsed_end = utils.parse_date(data_fim) if data_fim else None

        if data_inicio and parsed_start is None:
            raise ValueError("dataInicio inválida. Use o formato YYYY-MM-DD.")
        if data_fim and parsed_end is None:
            raise ValueError("dataFim inválida. Use o formato YYYY-MM-DD.")

        if parsed_start is None and parsed_end is None:
            end = date.today()
            start = date(end.year, end.month, 1)
            return cls(start_date=start, end_date=end, filial=normalized_filial)

        if parsed_start is None or parsed_end is None:
            raise ValueError("Informe dataInicio e dataFim juntas, ou omita ambas.")

        if parsed_start > parsed_end:
            raise ValueError("dataInicio não pode ser maior que dataFim.")

        if _months_inclusive(parsed_start, parsed_end) > MAX_MONTHS_WINDOW:
            raise ValueError(f"Período máximo permitido: {MAX_MONTHS_WINDOW} meses.")

        return cls(
            start_date=parsed_start,
            end_date=parsed_end,
            filial=normalized_filial,
        )

    def iso_range(self) -> tuple[str, str]:
        return self.start_date.isoformat(), self.end_date.isoformat()

    def periodo_dict(self) -> dict[str, str | None]:
        start, end = self.iso_range()
        return {"dataInicio": start, "dataFim": end, "filial": self.filial}

    def protheus_closed_open(self) -> tuple[str, str]:
        """Retorna (start YYYYMMDD, end_exclusive YYYYMMDD)."""
        qb = QueryBuilder()
        start = qb.convert_date_to_protheus(self.start_date.isoformat())
        end_exclusive = qb.convert_date_to_protheus(
            (self.end_date + timedelta(days=1)).isoformat()
        )
        if not start or not end_exclusive:
            raise ValueError(
                "Não foi possível converter o período para o formato Protheus."
            )
        return start, end_exclusive

    def day_closed_open(self) -> tuple[str, str]:
        """KPIs do dia = dataFim (inclusive)."""
        qb = QueryBuilder()
        start = qb.convert_date_to_protheus(self.end_date.isoformat())
        end_exclusive = qb.convert_date_to_protheus(
            (self.end_date + timedelta(days=1)).isoformat()
        )
        if not start or not end_exclusive:
            raise ValueError("Não foi possível converter a data do dia.")
        return start, end_exclusive

    def month_closed_open(self) -> tuple[str, str]:
        """KPIs do mês = mês calendário completo de dataFim (1º → último dia).

        Independente do intervalo filtrado: alterar só dataFim dentro do mesmo
        mês não altera valorMes (diferente do total do período).
        """
        qb = QueryBuilder()
        month_start = date(self.end_date.year, self.end_date.month, 1)
        if self.end_date.month == 12:
            next_month = date(self.end_date.year + 1, 1, 1)
        else:
            next_month = date(self.end_date.year, self.end_date.month + 1, 1)
        start = qb.convert_date_to_protheus(month_start.isoformat())
        end_exclusive = qb.convert_date_to_protheus(next_month.isoformat())
        if not start or not end_exclusive:
            raise ValueError("Não foi possível converter o mês de referência.")
        return start, end_exclusive

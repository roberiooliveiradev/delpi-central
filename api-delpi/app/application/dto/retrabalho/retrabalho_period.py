from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.quality.retrabalho.retrabalho_view_scope import VALID_RETRABALHO_BRANCHES
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_query_settings import (
    DEFAULT_MONTHS_WINDOW,
    MAX_MONTHS_WINDOW,
)


def _default_period_start(end: date, months_window: int = DEFAULT_MONTHS_WINDOW) -> date:
    """Primeiro dia do mês inicial para janela de N meses calendário (inclui mês atual)."""
    offset = months_window - 1
    total = end.year * 12 + end.month - 1 - offset
    year = total // 12
    month = total % 12 + 1
    return date(year, month, 1)


def _months_inclusive(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) + 1


@dataclass(frozen=True, slots=True)
class RetrabalhoPeriod:
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
    ) -> RetrabalhoPeriod:
        normalized_filial = str(filial or "").strip() or None
        if normalized_filial is None:
            if require_filial:
                raise ValueError("filial é obrigatória.")
        elif normalized_filial not in VALID_RETRABALHO_BRANCHES:
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
            start = _default_period_start(end)
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

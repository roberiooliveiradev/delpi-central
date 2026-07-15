from __future__ import annotations

from app.application.dto.refugos.refugos_formatters import as_int, round_cost, round_qty
from app.application.dto.refugos.refugos_serie_request import RefugosSerieRequest
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort


def _format_bucket(bucket: str, granularity: str) -> tuple[str, str]:
    """Retorna (dateKey ISO-ish, label PT curto)."""
    raw = str(bucket or "").strip()
    if granularity == "month" and len(raw) >= 6:
        year, month = raw[:4], raw[4:6]
        return f"{year}-{month}", f"{month}/{year}"
    if len(raw) >= 8:
        year, month, day = raw[:4], raw[4:6], raw[6:8]
        return f"{year}-{month}-{day}", f"{day}/{month}/{year}"
    return raw, raw


class GetRefugosSerieUseCase:
    def __init__(self, repository: RefugosRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RefugosSerieRequest) -> dict:
        date_start, date_end_exclusive = request.period.protheus_closed_open()
        rows = self._repository.get_serie(
            granularity=request.granularity,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.period.filial,
            **request.filter_kwargs(),
        )

        points = []
        for row in rows:
            date_key, label = _format_bucket(str(row.get("bucket") or ""), request.granularity)
            points.append(
                {
                    "date": date_key,
                    "label": label,
                    "value": round_cost(row.get("total_valor")),
                    "quantity": round_qty(row.get("total_quantidade")),
                    "occurrenceCount": as_int(row.get("ocorrencias")),
                }
            )

        return {
            "periodo": request.periodo_dict(),
            "granularity": request.granularity,
            "points": points,
            "branchFilterApplied": True,
            "summary": {
                "branch": request.period.filial,
                "branch_filter_applied": True,
                "period": {
                    "start": request.period.start_date.isoformat(),
                    "end": request.period.end_date.isoformat(),
                },
                "is_complete": True,
            },
        }

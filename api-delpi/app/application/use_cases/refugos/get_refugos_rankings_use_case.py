from __future__ import annotations

from app.application.dto.refugos.refugos_formatters import (
    as_int,
    clean_text,
    display_label,
    round_cost,
    round_qty,
)
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort
from app.domain.quality.refugos.refugos_scope import (
    MOTIVO_SEM_LABEL,
    OPERADOR_SEM_NOME_LABEL,
)


class GetRefugosRankingsUseCase:
    def __init__(self, repository: RefugosRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RefugosQueryRequest) -> dict:
        if not request.dimension:
            raise ValueError("dimension é obrigatória.")

        date_start, date_end_exclusive = request.period.protheus_closed_open()
        limit = request.resolve_ranking_limit()
        rows = self._repository.get_ranking(
            dimension=request.dimension,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.period.filial,
            limit=limit,
            **request.filter_kwargs(),
        )

        total_valor = sum(float(row.get("value") or 0) for row in rows)
        fallback = (
            OPERADOR_SEM_NOME_LABEL
            if request.dimension == "colaborador"
            else MOTIVO_SEM_LABEL
            if request.dimension == "motivo"
            else ""
        )

        items = []
        for row in rows:
            value = round_cost(row.get("value"))
            share = round((value / total_valor) * 100, 2) if total_valor > 0 else 0.0
            items.append(
                {
                    "code": clean_text(row.get("code")),
                    "label": display_label(row.get("label"), fallback=fallback)
                    or clean_text(row.get("code")),
                    "quantity": round_qty(row.get("quantity")),
                    "value": value,
                    "sharePct": share,
                    "occurrenceCount": as_int(row.get("occurrence_count")),
                }
            )

        return {
            "periodo": request.periodo_dict(),
            "dimension": request.dimension,
            "items": items,
            "summary": {
                "total_records": len(items),
                "total_valor": round_cost(total_valor),
                "branch": request.period.filial,
                "branch_filter_applied": True,
                "period": {
                    "start": request.period.start_date.isoformat(),
                    "end": request.period.end_date.isoformat(),
                },
                "is_complete": True,
            },
        }

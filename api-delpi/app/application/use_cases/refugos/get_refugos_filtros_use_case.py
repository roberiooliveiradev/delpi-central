from __future__ import annotations

from app.application.dto.refugos.refugos_formatters import clean_text
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort


class GetRefugosFiltrosUseCase:
    def __init__(self, repository: RefugosRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RefugosQueryRequest) -> dict:
        date_start, date_end_exclusive = request.period.protheus_closed_open()
        raw = self._repository.get_filtros(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.period.filial,
        )

        def _code_label_items(rows: list[dict]) -> list[dict]:
            return [
                {
                    "codigo": clean_text(row.get("codigo")),
                    "descricao": clean_text(row.get("descricao")),
                }
                for row in rows
                if clean_text(row.get("codigo"))
            ]

        return {
            "periodo": request.periodo_dict(),
            "materiasPrimas": _code_label_items(raw.get("materiasPrimas") or []),
            "produtosAcabados": _code_label_items(raw.get("produtosAcabados") or []),
            "ordensProducao": [
                {"codigo": clean_text(row.get("codigo"))}
                for row in (raw.get("ordensProducao") or [])
                if clean_text(row.get("codigo"))
            ],
            "motivos": _code_label_items(raw.get("motivos") or []),
        }

from __future__ import annotations

from app.application.dto.retrabalho.retrabalho_formatters import display_operador_nome
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort


class GetRetrabalhoFiltrosUseCase:
    def __init__(self, repository: RetrabalhoRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: RetrabalhoQueryRequest) -> dict:
        start_date, end_date = request.period.iso_range()
        payload = self._repository.get_filtros(
            start_date=start_date,
            end_date=end_date,
            branch=request.period.filial,
        )

        recursos = [
            {
                "recurso": row.get("recurso") or "",
                "centroCusto": row.get("centro_custo") or "",
            }
            for row in payload.get("recursos") or []
            if row.get("recurso")
        ]
        colaboradores = [
            {
                "codigoOperador": row.get("codigo_operador") or "",
                "nomeOperador": display_operador_nome(row.get("nome_operador")),
            }
            for row in payload.get("colaboradores") or []
            if row.get("codigo_operador")
        ]

        return {
            "periodo": request.periodo_dict(),
            "recursos": recursos,
            "colaboradores": colaboradores,
        }

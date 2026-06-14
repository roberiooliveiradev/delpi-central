from __future__ import annotations

from app.domain.propostas_comerciais.ports.proposta_comercial_repository_port import (
    PropostaComercialRepositoryPort,
)
from app.domain.propostas_comerciais.services.proposta_comercial_formatter import (
    PropostaComercialFormatter,
)


class ListPropostasComerciaisUseCase:
    def __init__(self, repository: PropostaComercialRepositoryPort):
        self._repository = repository

    def execute(self, *, limit: int = 100) -> dict:
        rows = self._repository.list_active_recent(limit=limit)
        items = [PropostaComercialFormatter.format_list_item(row) for row in rows]
        return {
            "items": items,
            "total": len(items),
        }

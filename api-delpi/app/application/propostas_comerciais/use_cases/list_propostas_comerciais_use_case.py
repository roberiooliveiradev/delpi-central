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

    def execute(
        self,
        *,
        limit: int = 100,
        search: str | None = None,
        page: int = 1,
        page_size: int | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> dict:
        resolved_size = page_size or limit
        resolved_page = max(page or 1, 1)
        offset = (resolved_page - 1) * resolved_size
        rows = self._repository.list_active_recent(
            limit=resolved_size, offset=offset, search=search,
            sort_by=sort_by, sort_dir=sort_dir
        )
        total = self._repository.count_active(search=search)
        items = [PropostaComercialFormatter.format_list_item(row) for row in rows]
        return {
            "items": items,
            "total": total,
            "page": resolved_page,
            "page_size": resolved_size,
        }

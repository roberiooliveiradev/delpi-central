from __future__ import annotations

from dataclasses import dataclass

from app.application.models.page import Page
from app.domain.entities.customer.customer_master import CustomerMaster
from app.domain.ports.customer.customer_query_repository_port import (
    CustomerQueryRepositoryPort,
)


@dataclass(frozen=True, slots=True)
class SearchActiveCustomersRequest:
    query: str | None = None
    page: int = 1
    page_size: int = 20
    include_blocked: bool = True


class SearchActiveCustomersUseCase:
    """Busca clientes no cadastro TOTVS (SA1).

    `include_blocked=True` (padrão) preserva contas bloqueadas para
    superfícies de consulta (Conta 360, mentions). O domínio de Carteiras
    chama com `include_blocked=False`: cliente `A1_MSBLQL='1'` não é
    elegível a vínculo. Match em nome reduzido (`A1_NREDUZ`) nos dois modos.
    """

    def __init__(self, repository: CustomerQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchActiveCustomersRequest) -> Page[CustomerMaster]:
        page = max(1, int(request.page or 1))
        page_size = min(100, max(1, int(request.page_size or 20)))
        return self._repository.search_active_customers(
            query=request.query,
            page=page,
            page_size=page_size,
            include_blocked=bool(request.include_blocked),
        )

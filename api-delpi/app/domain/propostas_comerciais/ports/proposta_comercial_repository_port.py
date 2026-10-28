from __future__ import annotations

from typing import Protocol


class PropostaComercialRepositoryPort(Protocol):
    def list_active_recent(
        self, *, limit: int = 100, offset: int = 0, search: str | None = None
    ) -> list[dict]:
        """Lista propostas ativas ordenadas da mais recente (linhas brutas do SQL)."""

    def count_active(self, *, search: str | None = None) -> int:
        """Total de propostas ativas que atendem ao critério de busca."""

    def get_detail_rows(self, proposta_interna: str) -> tuple[dict | None, list[dict]]:
        """Retorna cabeçalho agregado e itens brutos para a proposta informada."""

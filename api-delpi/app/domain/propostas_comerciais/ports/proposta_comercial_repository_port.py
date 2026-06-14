from __future__ import annotations

from typing import Protocol


class PropostaComercialRepositoryPort(Protocol):
    def list_active_recent(self, *, limit: int = 100) -> list[dict]:
        """Lista propostas ativas recentes (linhas brutas do SQL)."""

    def get_detail_rows(self, proposta_interna: str) -> tuple[dict | None, list[dict]]:
        """Retorna cabeçalho agregado e itens brutos para a proposta informada."""

from __future__ import annotations

from app.domain.propostas_comerciais.ports.proposta_comercial_repository_port import (
    PropostaComercialRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.totvs.propostas_comerciais.queries import (
    DETAIL_HEADER_SQL,
    DETAIL_ITEMS_SQL,
    LIST_ACTIVE_RECENT_SQL,
)


class PropostaComercialRepository(BaseRepository, PropostaComercialRepositoryPort):
    _MAX_LIST_LIMIT = 200
    _DEFAULT_LIST_LIMIT = 100

    def list_active_recent(self, *, limit: int = 100) -> list[dict]:
        resolved_limit = min(max(limit or self._DEFAULT_LIST_LIMIT, 1), self._MAX_LIST_LIMIT)
        with self:
            return self.execute_query(LIST_ACTIVE_RECENT_SQL, (resolved_limit,))

    def get_detail_rows(self, proposta_interna: str) -> tuple[dict | None, list[dict]]:
        code = (proposta_interna or "").strip()
        with self:
            header = self.execute_one(DETAIL_HEADER_SQL, (code,))
            if not header:
                return None, []
            items = self.execute_query(DETAIL_ITEMS_SQL, (code, code))
        return header, items

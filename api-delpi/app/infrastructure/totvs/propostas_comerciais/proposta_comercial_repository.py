from __future__ import annotations

from app.domain.propostas_comerciais.ports.proposta_comercial_repository_port import (
    PropostaComercialRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.propostas_comerciais.services.proposal_document_search_service import (
    ProposalDocumentSearchService,
)
from app.infrastructure.totvs.propostas_comerciais.queries import (
    COUNT_ACTIVE_SQL,
    DETAIL_HEADER_SQL,
    DETAIL_ITEMS_SQL,
    LIST_ACTIVE_SQL,
    resolve_list_order,
)


class PropostaComercialRepository(BaseRepository, PropostaComercialRepositoryPort):
    _MAX_LIST_LIMIT = 200
    _DEFAULT_LIST_LIMIT = 100

    def list_active_recent(
        self, *, limit: int = 100, offset: int = 0, search: str | None = None,
        sort_by: str | None = None, sort_dir: str | None = None
    ) -> list[dict]:
        resolved_limit = min(max(limit or self._DEFAULT_LIST_LIMIT, 1), self._MAX_LIST_LIMIT)
        resolved_offset = max(offset or 0, 0)
        search_clause, search_params = ProposalDocumentSearchService.clause(search)
        sql = LIST_ACTIVE_SQL.format(
            search_clause=search_clause,
            order_clause=resolve_list_order(sort_by, sort_dir),
        )
        with self:
            return self.execute_query(
                sql, (*search_params, resolved_offset, resolved_limit)
            )

    def count_active(self, *, search: str | None = None) -> int:
        search_clause, search_params = ProposalDocumentSearchService.clause(search)
        sql = COUNT_ACTIVE_SQL.format(search_clause=search_clause)
        with self:
            row = self.execute_one(sql, tuple(search_params))
        return int(row["total"]) if row else 0

    def get_detail_rows(self, proposta_interna: str) -> tuple[dict | None, list[dict]]:
        code = (proposta_interna or "").strip()
        with self:
            header = self.execute_one(DETAIL_HEADER_SQL, (code,))
            if not header:
                return None, []
            items = self.execute_query(DETAIL_ITEMS_SQL, (code,))
        return header, items

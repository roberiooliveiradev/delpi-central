from __future__ import annotations

from app.domain.ports.pedidos_venda_abertos.ops_abertas_query_repository_port import (
    OpsAbertasQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.ops_abertas_sql import (
    build_ops_abertas_detalhe_sql,
    build_ops_abertas_resumo_sql,
)


class OpsAbertasQueryRepository(BaseRepository, OpsAbertasQueryRepositoryPort):

    def list_open_ops(self) -> tuple[list[dict], list[dict]]:
        detalhe_sql = build_ops_abertas_detalhe_sql()
        resumo_sql = build_ops_abertas_resumo_sql()
        with self:
            items = self.execute_query(detalhe_sql)
            summary_items = self.execute_query(resumo_sql)
        return items, summary_items

from __future__ import annotations

from app.domain.ports.financeiro_inadimplencia.inadimplencia_repository_port import (
    InadimplenciaRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.financeiro_inadimplencia.inadimplencia_sql import (
    build_clientes_count_query,
    build_clientes_data_query,
    build_faixas_atraso_query,
    build_mensal_query,
    build_resumo_query,
    build_titulos_count_query,
    build_titulos_data_query,
)


class InadimplenciaRepository(BaseRepository, InadimplenciaRepositoryPort):
    def get_resumo(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
    ) -> dict:
        query, params = build_resumo_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def get_mensal(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        customer_code: str | None = None,
        store_code: str | None = None,
        customer_pairs: tuple[tuple[str, str], ...] | None = None,
        novos_negocios: bool = False,
    ) -> list[dict]:
        query, params = build_mensal_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
            customer_code=customer_code,
            store_code=store_code,
            customer_pairs=customer_pairs,
            novos_negocios=novos_negocios,
        )
        with self:
            return self.execute_query(query, params)

    def get_faixas_atraso(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
    ) -> list[dict]:
        query, params = build_faixas_atraso_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
        )
        with self:
            return self.execute_query(query, params)

    def count_clientes(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        q: str | None = None,
        only_with_delays: bool = True,
    ) -> int:
        query, params = build_clientes_count_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
            q=q,
            only_with_delays=only_with_delays,
        )
        with self:
            row = self.execute_one(query, params)
        return int((row or {}).get("total_items") or 0)

    def list_clientes(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        q: str | None = None,
        only_with_delays: bool = True,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]:
        query, params = build_clientes_data_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
            q=q,
            only_with_delays=only_with_delays,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

    def count_titulos(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        customer_code: str | None = None,
        store_code: str | None = None,
        status: str = "all",
        delay_range: str | None = None,
        q: str | None = None,
    ) -> int:
        query, params = build_titulos_count_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
            customer_code=customer_code,
            store_code=store_code,
            status=status,
            delay_range=delay_range,
            q=q,
        )
        with self:
            row = self.execute_one(query, params)
        return int((row or {}).get("total_items") or 0)

    def list_titulos(
        self,
        *,
        start_date: str,
        end_date_exclusive: str,
        customer_code: str | None = None,
        store_code: str | None = None,
        status: str = "all",
        delay_range: str | None = None,
        q: str | None = None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]:
        query, params = build_titulos_data_query(
            start_date=start_date,
            end_date_exclusive=end_date_exclusive,
            customer_code=customer_code,
            store_code=store_code,
            status=status,
            delay_range=delay_range,
            q=q,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

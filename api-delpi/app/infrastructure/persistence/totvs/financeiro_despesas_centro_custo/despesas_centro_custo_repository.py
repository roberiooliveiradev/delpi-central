from __future__ import annotations

from app.domain.ports.financeiro_despesas_centro_custo.despesas_centro_custo_repository_port import (
    DespesasCentroCustoRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_sql import (
    build_centros_custo_query,
    build_filiais_query,
    build_fornecedores_query,
    build_lancamentos_count_query,
    build_lancamentos_data_query,
    build_ranking_centros_query,
    build_ranking_fornecedores_query,
    build_resumo_query,
    build_serie_query,
)


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


class DespesasCentroCustoRepository(BaseRepository, DespesasCentroCustoRepositoryPort):
    def get_filtros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
    ) -> dict:
        with self:
            filiais_query, filiais_params = build_filiais_query(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
            centros_query, centros_params = build_centros_custo_query(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )
            fornecedores_query, fornecedores_params = build_fornecedores_query(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                cost_center=cost_center,
            )

            filiais_rows = self.execute_query(filiais_query, filiais_params)
            centros_rows = self.execute_query(centros_query, centros_params)
            fornecedores_rows = self.execute_query(
                fornecedores_query,
                fornecedores_params,
            )

        return {
            "filiais": [
                {"codigo": _clean(row.get("codigo"))}
                for row in filiais_rows
                if _clean(row.get("codigo"))
            ],
            "centros_custo": [
                {
                    "codigo": _clean(row.get("codigo")),
                    "descricao": _clean(row.get("descricao")),
                }
                for row in centros_rows
                if _clean(row.get("codigo"))
            ],
            "fornecedores": [
                {
                    "codigo": _clean(row.get("codigo")),
                    "loja": _clean(row.get("loja")),
                    "razao_social": _clean(row.get("razao_social")),
                }
                for row in fornecedores_rows
                if _clean(row.get("codigo"))
            ],
        }

    def get_resumo(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
    ) -> dict:
        query, params = build_resumo_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
        )
        with self:
            rows = self.execute_query(query, params)

        return rows[0] if rows else {}

    def get_serie(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
    ) -> list[dict]:
        query, params = build_serie_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
        )
        with self:
            return self.execute_query(query, params)

    def get_ranking_centros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        query, params = build_ranking_centros_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            limit=limit,
        )
        with self:
            return self.execute_query(query, params)

    def get_ranking_fornecedores(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        query, params = build_ranking_fornecedores_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            limit=limit,
        )
        with self:
            return self.execute_query(query, params)

    def count_lancamentos(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        search: str | None = None,
    ) -> int:
        query, params = build_lancamentos_count_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            search=search,
        )
        with self:
            row = self.execute_one(query, params)

        return int((row or {}).get("total_items") or 0)

    def list_lancamentos(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        search: str | None = None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]:
        query, params = build_lancamentos_data_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

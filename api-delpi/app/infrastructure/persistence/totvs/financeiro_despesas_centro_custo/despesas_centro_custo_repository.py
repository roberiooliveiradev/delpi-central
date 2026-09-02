from __future__ import annotations

from app.application.services.financeiro_despesas_centro_custo.despesas_centro_custo_query_cache import (
    get_cached_count,
    get_cached_lancamentos_rows,
    get_cached_ranking_rows,
    get_cached_resumo_row,
    lancamentos_count_cache_key,
    lancamentos_page_cache_key,
    ranking_centros_cache_key,
    ranking_fornecedores_cache_key,
    resumo_cache_key,
    set_cached_count,
    set_cached_lancamentos_rows,
    set_cached_ranking_rows,
    set_cached_resumo_row,
)
from app.domain.ports.financeiro_despesas_centro_custo.despesas_centro_custo_repository_port import (
    DespesasCentroCustoRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_sql import (
    build_centros_custo_catalog_by_branch_query,
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
    def list_centros_custo_by_branch(self, *, branch: str) -> list[dict]:
        """Lista deduplicada de centros de custo ERP para uma filial (somente leitura)."""
        query, params = build_centros_custo_catalog_by_branch_query(branch=branch)
        with self:
            rows = self.execute_query(query, params)
        seen: set[str] = set()
        items: list[dict] = []
        for row in rows:
            code = _clean(row.get("codigo"))
            if not code or code in seen:
                continue
            seen.add(code)
            items.append(
                {
                    "branch": _clean(row.get("filial")) or branch,
                    "code": code,
                    "description": _clean(row.get("descricao")),
                }
            )
        return items

    def get_filtros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        exclude_mp_products: bool = False,
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
                exclude_mp_products=exclude_mp_products,
            )
            fornecedores_query, fornecedores_params = build_fornecedores_query(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                cost_center=cost_center,
                exclude_mp_products=exclude_mp_products,
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
        exclude_mp_products: bool = False,
    ) -> dict:
        cache_key = resumo_cache_key(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            exclude_mp_products=exclude_mp_products,
        )
        cached = get_cached_resumo_row(cache_key)
        if cached is not None:
            return cached

        query, params = build_resumo_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            exclude_mp_products=exclude_mp_products,
        )
        with self:
            rows = self.execute_query(query, params)

        row = rows[0] if rows else {}
        set_cached_resumo_row(cache_key, row)
        return row

    def get_serie(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        supplier_code: str | None = None,
        supplier_store: str | None = None,
        exclude_mp_products: bool = False,
    ) -> list[dict]:
        query, params = build_serie_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            exclude_mp_products=exclude_mp_products,
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
        exclude_mp_products: bool = False,
    ) -> list[dict]:
        cache_key = ranking_centros_cache_key(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            limit=limit,
            exclude_mp_products=exclude_mp_products,
        )
        cached = get_cached_ranking_rows(cache_key)
        if cached is not None:
            return cached

        query, params = build_ranking_centros_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            limit=limit,
            exclude_mp_products=exclude_mp_products,
        )
        with self:
            rows = self.execute_query(query, params)
        set_cached_ranking_rows(cache_key, rows)
        return rows

    def get_ranking_fornecedores(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None = None,
        cost_center: str | None = None,
        limit: int = 10,
        exclude_mp_products: bool = False,
    ) -> list[dict]:
        cache_key = ranking_fornecedores_cache_key(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            limit=limit,
            exclude_mp_products=exclude_mp_products,
        )
        cached = get_cached_ranking_rows(cache_key)
        if cached is not None:
            return cached

        query, params = build_ranking_fornecedores_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            limit=limit,
            exclude_mp_products=exclude_mp_products,
        )
        with self:
            rows = self.execute_query(query, params)
        set_cached_ranking_rows(cache_key, rows)
        return rows

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
        exclude_mp_products: bool = False,
    ) -> int:
        cache_key = lancamentos_count_cache_key(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            search=search,
            exclude_mp_products=exclude_mp_products,
        )
        cached = get_cached_count(cache_key)
        if cached is not None:
            return cached

        query, params = build_lancamentos_count_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            search=search,
            exclude_mp_products=exclude_mp_products,
        )
        with self:
            row = self.execute_one(query, params)

        total = int((row or {}).get("total_items") or 0)
        set_cached_count(cache_key, total)
        return total

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
        exclude_mp_products: bool = False,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]:
        cache_key = lancamentos_page_cache_key(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            search=search,
            exclude_mp_products=exclude_mp_products,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        cached = get_cached_lancamentos_rows(cache_key)
        if cached is not None:
            return cached

        query, params = build_lancamentos_data_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            cost_center=cost_center,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
            search=search,
            exclude_mp_products=exclude_mp_products,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        with self:
            rows = self.execute_query(query, params)
        set_cached_lancamentos_rows(cache_key, rows)
        return rows

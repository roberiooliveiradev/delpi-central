from __future__ import annotations

import math

from app.domain.ports.retrabalho.retrabalho_repository_port import RetrabalhoRepositoryPort
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_sql import (
    build_detalhes_count_query,
    build_detalhes_data_query,
    build_filtros_colaboradores_query,
    build_filtros_recursos_query,
    build_health_query,
    build_mensal_query,
    build_ranking_colaborador_top1_query,
    build_ranking_colaboradores_query,
    build_ranking_recursos_query,
    build_ranking_recurso_top1_query,
    build_resumo_query,
)


class RetrabalhoRepository(BaseRepository, RetrabalhoRepositoryPort):
    def check_health(self) -> dict:
        query, params = build_health_query()
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def get_filtros(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
    ) -> dict:
        recursos_query, recursos_params = build_filtros_recursos_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        colaboradores_query, colaboradores_params = build_filtros_colaboradores_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        with self:
            recursos = self.execute_query(recursos_query, recursos_params)
            colaboradores = self.execute_query(colaboradores_query, colaboradores_params)

        return {
            "recursos": recursos,
            "colaboradores": colaboradores,
        }

    def get_resumo(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> dict:
        query, params = build_resumo_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def get_top_recurso(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> dict | None:
        query, params = build_ranking_recurso_top1_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else None

    def get_top_colaborador(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> dict | None:
        query, params = build_ranking_colaborador_top1_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else None

    def get_mensal(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> list[dict]:
        query, params = build_mensal_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
        with self:
            return self.execute_query(query, params)

    def get_ranking_recursos(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        order_by: str = "horas",
        limit: int = 10,
    ) -> list[dict]:
        query, params = build_ranking_recursos_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
            order_by=order_by,
            limit=limit,
        )
        with self:
            return self.execute_query(query, params)

    def get_ranking_colaboradores(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        order_by: str = "horas",
        limit: int = 10,
    ) -> list[dict]:
        query, params = build_ranking_colaboradores_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
            order_by=order_by,
            limit=limit,
        )
        with self:
            return self.execute_query(query, params)

    def get_detalhes(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
        sort_by: str = "data",
        sort_dir: str = "desc",
        offset: int = 0,
        page_size: int = 50,
    ) -> list[dict]:
        query, params = build_detalhes_data_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
            sort_by=sort_by,
            sort_dir=sort_dir,
            offset=offset,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

    def count_detalhes(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str,
        recurso: str | None = None,
        centro_custo: str | None = None,
        codigo_operador: str | None = None,
    ) -> int:
        query, params = build_detalhes_count_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recurso=recurso,
            centro_custo=centro_custo,
            codigo_operador=codigo_operador,
        )
        with self:
            rows = self.execute_query(query, params)
        if not rows:
            return 0
        return int(rows[0].get("total") or 0)


def calc_total_pages(total: int, page_size: int) -> int:
    if total <= 0:
        return 0
    return max(1, math.ceil(total / page_size))

from __future__ import annotations

import math

from app.domain.ports.refugos.refugos_repository_port import RefugosRepositoryPort
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.refugos.refugos_sql import (
    build_filtros_motivo_query,
    build_filtros_mp_query,
    build_filtros_op_query,
    build_filtros_pa_query,
    build_health_query,
    build_ranking_query,
    build_registros_count_query,
    build_registros_query,
    build_resumo_query,
    build_serie_query,
)


def calc_total_pages(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return int(math.ceil(total / page_size)) if total > 0 else 0


class RefugosRepository(BaseRepository, RefugosRepositoryPort):
    def check_health(self) -> dict:
        query, params = build_health_query()
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def get_filtros(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
    ) -> dict:
        common = {
            "date_start": date_start,
            "date_end_exclusive": date_end_exclusive,
            "branch": branch,
        }
        mp_q, mp_p = build_filtros_mp_query(**common)
        pa_q, pa_p = build_filtros_pa_query(**common)
        op_q, op_p = build_filtros_op_query(**common)
        motivo_q, motivo_p = build_filtros_motivo_query(**common)
        with self:
            return {
                "materiasPrimas": self.execute_query(mp_q, mp_p),
                "produtosAcabados": self.execute_query(pa_q, pa_p),
                "ordensProducao": self.execute_query(op_q, op_p),
                "motivos": self.execute_query(motivo_q, motivo_p),
            }

    def get_resumo(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        day_start: str,
        day_end_exclusive: str,
        month_start: str,
        month_end_exclusive: str,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> dict:
        query, params = build_resumo_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            day_start=day_start,
            day_end_exclusive=day_end_exclusive,
            month_start=month_start,
            month_end_exclusive=month_end_exclusive,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def get_ranking(
        self,
        *,
        dimension: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        limit: int,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> list[dict]:
        query, params = build_ranking_query(
            dimension=dimension,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            limit=limit,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
        with self:
            return self.execute_query(query, params)

    def get_serie(
        self,
        *,
        granularity: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> list[dict]:
        query, params = build_serie_query(
            granularity=granularity,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
        with self:
            return self.execute_query(query, params)

    def get_registros(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        offset: int,
        page_size: int,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> list[dict]:
        query, params = build_registros_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            offset=offset,
            page_size=page_size,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
        with self:
            return self.execute_query(query, params)

    def count_registros(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str,
        mp: str | None = None,
        pa: str | None = None,
        op: str | None = None,
        motivo: str | None = None,
        recurso: str | None = None,
    ) -> int:
        query, params = build_registros_count_query(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            mp=mp,
            pa=pa,
            op=op,
            motivo=motivo,
            recurso=recurso,
        )
        with self:
            rows = self.execute_query(query, params)
        if not rows:
            return 0
        return int(rows[0].get("total") or 0)

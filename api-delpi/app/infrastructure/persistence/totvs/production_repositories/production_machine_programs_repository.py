"""Repositório — ranking de intermediários para programas de máquina."""

from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache
from app.domain.ports.production.production_machine_programs_repository_port import (
    ProductionMachineProgramsRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production_repositories.production_machine_programs_sql import (
    build_top_intermediates_sql,
)

_CACHE_NS = "production-machine-programs-top-intermediates-v5"


def _cache_key(
    *,
    branch: str,
    date_start: str,
    date_end_exclusive: str,
    page: int,
    page_size: int,
    search: str | None,
) -> str:
    return "|".join(
        [
            _CACHE_NS,
            branch,
            date_start,
            date_end_exclusive,
            str(page),
            str(page_size),
            (search or "").strip().upper(),
        ]
    )


class ProductionMachineProgramsRepository(
    BaseRepository,
    ProductionMachineProgramsRepositoryPort,
):
    def fetch_top_intermediates(
        self,
        *,
        branch: str,
        date_start: str,
        date_end_exclusive: str,
        page: int,
        page_size: int,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        key = _cache_key(
            branch=branch,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            page=page,
            page_size=page_size,
            search=search,
        )
        cached = build_query_cache().get(key)
        if isinstance(cached, dict) and "items" in cached and "total" in cached:
            return list(cached["items"]), int(cached["total"])

        offset = max(0, (page - 1) * page_size)
        search_term = (search or "").strip()
        search_like = f"%{search_term}%" if search_term else None

        sql_items, sql_count = build_top_intermediates_sql(
            search=search_like,
            offset=offset,
            page_size=page_size,
        )

        base_params: list[Any] = [
            branch,
            date_start,
            date_end_exclusive,
            branch,
            branch,
            branch,
        ]
        if search_like:
            base_params.extend([search_like, search_like])

        with self as repo:
            items = repo.execute_query(sql_items, tuple(base_params))
            count_rows = repo.execute_query(sql_count, tuple(base_params))

        total = int((count_rows[0] or {}).get("total") or 0) if count_rows else 0
        normalized = [_normalize_row(row) for row in items]
        build_query_cache().set(key, {"items": normalized, "total": total})
        return normalized, total


def _normalize_row(row: dict) -> dict:
    return {
        "intermediate_code": str(row.get("intermediate_code") or "").strip(),
        "intermediate_description": str(
            row.get("intermediate_description") or ""
        ).strip(),
        "finished_product_code": str(row.get("finished_product_code") or "").strip(),
        "cutting_work_center": str(row.get("cutting_work_center") or "").strip(),
        "has_open_production_order": bool(int(row.get("has_open_production_order") or 0)),
        "qty_produced": float(row.get("qty_produced") or 0),
        "appointment_count": int(row.get("appointment_count") or 0),
    }

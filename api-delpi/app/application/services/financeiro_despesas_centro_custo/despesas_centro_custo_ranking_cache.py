from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache

_CACHE_NS = "despesas-cc-ranking-v1"


def ranking_centros_cache_key(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    supplier_code: str | None,
    supplier_store: str | None,
    limit: int,
    exclude_mp_products: bool,
) -> str:
    return "|".join(
        [
            _CACHE_NS,
            "centros",
            start_date,
            end_date,
            branch or "",
            supplier_code or "",
            supplier_store or "",
            str(int(limit)),
            "1" if exclude_mp_products else "0",
        ]
    )


def ranking_fornecedores_cache_key(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    cost_center: str | None,
    limit: int,
    exclude_mp_products: bool,
) -> str:
    return "|".join(
        [
            _CACHE_NS,
            "fornecedores",
            start_date,
            end_date,
            branch or "",
            cost_center or "",
            str(int(limit)),
            "1" if exclude_mp_products else "0",
        ]
    )


def get_cached_ranking_rows(key: str) -> list[dict[str, Any]] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_ranking_rows(key: str, rows: list[dict[str, Any]]) -> None:
    build_query_cache().set(key, rows)

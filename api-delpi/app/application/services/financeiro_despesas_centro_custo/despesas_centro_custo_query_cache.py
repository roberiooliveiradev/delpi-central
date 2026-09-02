from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache

_CACHE_NS = "despesas-cc-query-v1"


def _flag(value: bool) -> str:
    return "1" if value else "0"


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
            "ranking-centros",
            start_date,
            end_date,
            branch or "",
            supplier_code or "",
            supplier_store or "",
            str(int(limit)),
            _flag(exclude_mp_products),
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
            "ranking-fornecedores",
            start_date,
            end_date,
            branch or "",
            cost_center or "",
            str(int(limit)),
            _flag(exclude_mp_products),
        ]
    )


def resumo_cache_key(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    cost_center: str | None,
    supplier_code: str | None,
    supplier_store: str | None,
    exclude_mp_products: bool,
) -> str:
    return "|".join(
        [
            _CACHE_NS,
            "resumo",
            start_date,
            end_date,
            branch or "",
            cost_center or "",
            supplier_code or "",
            supplier_store or "",
            _flag(exclude_mp_products),
        ]
    )


def lancamentos_count_cache_key(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    cost_center: str | None,
    supplier_code: str | None,
    supplier_store: str | None,
    search: str | None,
    exclude_mp_products: bool,
) -> str:
    return "|".join(
        [
            _CACHE_NS,
            "lancamentos-count",
            start_date,
            end_date,
            branch or "",
            cost_center or "",
            supplier_code or "",
            supplier_store or "",
            (search or "").strip().lower(),
            _flag(exclude_mp_products),
        ]
    )


def lancamentos_page_cache_key(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    cost_center: str | None,
    supplier_code: str | None,
    supplier_store: str | None,
    search: str | None,
    exclude_mp_products: bool,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> str:
    return "|".join(
        [
            _CACHE_NS,
            "lancamentos-page",
            start_date,
            end_date,
            branch or "",
            cost_center or "",
            supplier_code or "",
            supplier_store or "",
            (search or "").strip().lower(),
            _flag(exclude_mp_products),
            sort_by,
            sort_dir,
            str(int(page)),
            str(int(page_size)),
        ]
    )


def get_cached_value(key: str) -> Any | None:
    return build_query_cache().get(key)


def set_cached_value(key: str, value: Any) -> None:
    build_query_cache().set(key, value)


def get_cached_ranking_rows(key: str) -> list[dict[str, Any]] | None:
    cached = get_cached_value(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_ranking_rows(key: str, rows: list[dict[str, Any]]) -> None:
    set_cached_value(key, rows)


def get_cached_resumo_row(key: str) -> dict[str, Any] | None:
    cached = get_cached_value(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_resumo_row(key: str, row: dict[str, Any]) -> None:
    set_cached_value(key, row)


def get_cached_count(key: str) -> int | None:
    cached = get_cached_value(key)
    if isinstance(cached, int):
        return cached
    return None


def set_cached_count(key: str, total: int) -> None:
    set_cached_value(key, int(total))


def get_cached_lancamentos_rows(key: str) -> list[dict[str, Any]] | None:
    cached = get_cached_value(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_lancamentos_rows(key: str, rows: list[dict[str, Any]]) -> None:
    set_cached_value(key, rows)

"""Dimensões de agrupamento do ranking de consumo — perfil JSON + SQL canônico."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = (
    Path(__file__).resolve().parents[3]
    / "content"
    / "production_consumption_top_items_group_by.json"
)


@dataclass(frozen=True)
class ConsumptionTopItemsGroupBySpec:
    key: str
    consolidated_when_no_branch_filter: bool
    select_fields: str
    group_by_sql: str
    order_by: str


class ProductionConsumptionTopItemsGroupByService:
    @classmethod
    @lru_cache(maxsize=1)
    def _registry(cls) -> dict[str, Any]:
        with _CONTENT_PATH.open(encoding="utf-8") as handle:
            payload = json.load(handle)

        dimensions = payload.get("dimensions")

        if not isinstance(dimensions, dict) or not dimensions:
            raise ValueError(
                "production_consumption_top_items_group_by.json exige 'dimensions'."
            )

        return payload

    @classmethod
    def invalidate_cache(cls) -> None:
        cls._registry.cache_clear()

    @classmethod
    def default_key(cls) -> str:
        return str(cls._registry().get("default") or "general").strip() or "general"

    @classmethod
    def allowed_keys(cls) -> frozenset[str]:
        dimensions = cls._registry().get("dimensions") or {}
        return frozenset(str(key).strip() for key in dimensions if str(key).strip())

    @classmethod
    def normalize(cls, group_by: str | None) -> str:
        key = str(group_by or cls.default_key()).strip().lower()

        if key in cls.allowed_keys():
            return key

        return cls.default_key()

    @classmethod
    def resolve(cls, group_by: str | None) -> ConsumptionTopItemsGroupBySpec:
        key = cls.normalize(group_by)
        raw = (cls._registry().get("dimensions") or {}).get(key) or {}

        if not isinstance(raw, dict):
            raise ValueError(f"Dimensão de agrupamento inválida: {key}")

        select_fields = str(raw.get("selectFields") or "").strip()
        group_by_sql = str(raw.get("groupBySql") or "").strip()
        order_by = str(raw.get("orderBy") or "").strip()

        if not select_fields or not group_by_sql or not order_by:
            raise ValueError(f"Perfil incompleto para group_by={key}")

        return ConsumptionTopItemsGroupBySpec(
            key=key,
            consolidated_when_no_branch_filter=bool(
                raw.get("consolidatedWhenNoBranchFilter")
            ),
            select_fields=select_fields,
            group_by_sql=group_by_sql,
            order_by=order_by,
        )

    @classmethod
    def render_select_fields(cls, spec: ConsumptionTopItemsGroupBySpec, *, consumption_expr: str) -> str:
        return spec.select_fields.format(consumption_expr=consumption_expr)

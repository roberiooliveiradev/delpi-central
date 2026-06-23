from __future__ import annotations

from typing import Any

from app.application.dto.production.production_request import ProductionRequest
from app.composition.query_cache_composer import build_query_cache
from app.domain.entities.production.on_time_delivery import OnTimeDelivery
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)


def production_oee_cache_key(request: ProductionRequest) -> str:
    return "|".join(
        [
            "production-oee",
            request.branch or "",
            request.start_date or "",
            request.end_date or "",
        ]
    )


def production_otd_cache_key(request: ProductionRequest) -> str:
    return "|".join(
        [
            "production-otd",
            request.branch or "",
            request.start_date or "",
            request.end_date or "",
        ]
    )


def get_cached_production_oee(key: str) -> OverallEquipmentEffectiveness | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return OverallEquipmentEffectiveness(**cached)
    return None


def set_cached_production_oee(
    key: str,
    value: OverallEquipmentEffectiveness,
) -> None:
    build_query_cache().set(key, value.to_dict())


def get_cached_production_otd(key: str) -> OnTimeDelivery | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return OnTimeDelivery(**cached)
    return None


def set_cached_production_otd(key: str, value: OnTimeDelivery) -> None:
    build_query_cache().set(key, value.to_dict())


def get_cached_chart_series(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def production_oee_by_branch_cache_key(request: ProductionRequest) -> str:
    return "|".join(
        [
            "production-oee-by-branch",
            request.branch or "",
            request.start_date or "",
            request.end_date or "",
        ]
    )


def get_cached_production_oee_by_branch(key: str) -> list[dict] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_production_oee_by_branch(key: str, value: list[dict]) -> None:
    build_query_cache().set(key, value)


def set_cached_chart_series(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)

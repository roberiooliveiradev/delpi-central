from __future__ import annotations

import time
from typing import Any

from delpi_api_client import DelpiApiError

from production_pulse_app.config import settings
from production_pulse_app.domain.services.binding_validation_service import BindingValidationError
from production_pulse_app.infrastructure.gateways.delpi_production_appointments_gateway import (
    DelpiProductionAppointmentsGateway,
)


class WorkCenterCatalogUnavailableError(RuntimeError):
    pass


def _normalize_code(value: str | None) -> str:
    return (value or "").strip().upper()


def _item_to_api(row: dict[str, Any], *, branch: str) -> dict[str, Any]:
    code = str(row.get("work_center") or row.get("workCenter") or "").strip()
    name = str(row.get("name") or row.get("work_center_name") or "").strip()
    is_final = row.get("is_final_inspection")
    if is_final is None:
        is_final = row.get("isFinalInspection")
    return {
        "branch": branch,
        "workCenterCode": code,
        "workCenterName": name,
        "isFinalInspection": bool(is_final),
    }


def _matches_search(item: dict[str, Any], search: str) -> bool:
    needle = search.strip().casefold()
    if not needle:
        return True
    haystacks = (
        str(item.get("workCenterCode") or ""),
        str(item.get("workCenterName") or ""),
    )
    return any(needle in value.casefold() for value in haystacks)


class WorkCenterCatalogService:
    def __init__(
        self,
        gateway: DelpiProductionAppointmentsGateway | None = None,
        *,
        cache_ttl_seconds: int | None = None,
    ) -> None:
        self._gateway = gateway or DelpiProductionAppointmentsGateway()
        self._cache_ttl_seconds = max(
            0,
            cache_ttl_seconds
            if cache_ttl_seconds is not None
            else settings.PP_WORK_CENTER_CACHE_TTL_SECONDS,
        )
        self._cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def _load_items(
        self,
        branch: str,
        *,
        authorization: str | None,
    ) -> list[dict[str, Any]]:
        branch = branch.strip()
        if not branch:
            raise BindingValidationError("branch é obrigatório.")

        cached = self._cache.get(branch)
        now = time.monotonic()
        if cached is not None and self._cache_ttl_seconds > 0:
            cached_at, items = cached
            if now - cached_at < self._cache_ttl_seconds:
                return items

        try:
            payload = self._gateway.list_work_centers(branch=branch, authorization=authorization)
        except DelpiApiError as exc:
            raise WorkCenterCatalogUnavailableError(str(exc.detail)) from exc

        raw_items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(raw_items, list):
            raise WorkCenterCatalogUnavailableError("Resposta inválida da api-delpi.")

        items = [_item_to_api(row, branch=branch) for row in raw_items if isinstance(row, dict)]
        if self._cache_ttl_seconds > 0:
            self._cache[branch] = (now, items)
        return items

    def list_work_centers(
        self,
        *,
        branch: str,
        search: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        items = self._load_items(branch, authorization=authorization)
        if search and search.strip():
            items = [item for item in items if _matches_search(item, search)]
        return {
            "branch": branch.strip(),
            "items": items,
            "summary": {
                "totalRecords": len(items),
                "branchFilterApplied": True,
            },
        }

    def validate_work_center_code(
        self,
        *,
        branch: str,
        work_center_code: str,
        authorization: str | None = None,
    ) -> None:
        code = _normalize_code(work_center_code)
        if not code:
            return

        items = self._load_items(branch, authorization=authorization)
        known = {_normalize_code(item.get("workCenterCode")) for item in items}
        if code not in known:
            raise BindingValidationError(
                f"work_center_code '{work_center_code.strip()}' não existe no catálogo TOTVS da filial."
            )


__all__ = [
    "BindingValidationError",
    "WorkCenterCatalogService",
    "WorkCenterCatalogUnavailableError",
]

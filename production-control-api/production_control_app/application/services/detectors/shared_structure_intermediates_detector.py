"""Detector — intermediários PI/PA compartilhados entre PAs ativos."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from production_control_app.application.services.problem_analysis_settings import as_int
from production_control_app.domain.errors import DelpiGatewayError
from production_control_app.domain.ports.problem_detector import (
    DetectorPage,
    DetectorSummary,
)
from production_control_app.domain.ports.production_orders_gateway import (
    ProductionOrdersGateway,
)

DETECTOR_ID = "shared-structure-intermediates"

_DEFAULT_SEVERITY = {"shared": "attention", "clear": "ok"}


def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data
    return payload if isinstance(payload, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


class SharedStructureIntermediatesDetector:
    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        settings: dict[str, Any] | None = None,
        today: date | None = None,
    ) -> None:
        self._gateway = gateway
        self._settings = settings or {}
        self._today = today

    @property
    def id(self) -> str:
        return DETECTOR_ID

    def _severity_map(self) -> dict[str, str]:
        raw = self._settings.get("severity")
        if not isinstance(raw, dict):
            return dict(_DEFAULT_SEVERITY)
        return {**_DEFAULT_SEVERITY, **{k: str(v) for k, v in raw.items()}}

    def _movement_from(self) -> str:
        days = as_int(self._settings.get("movementLookbackDays"), 365) or 365
        reference = self._today or date.today()
        return (reference - timedelta(days=days)).isoformat()

    def _lookback_days(self) -> int:
        return as_int(self._settings.get("movementLookbackDays"), 365) or 365

    def _page_size(self, requested: int | None = None) -> int:
        if requested and requested > 0:
            return requested
        return as_int(self._settings.get("pageSize"), 50) or 50

    def _map_finished_products(self, raw: Any) -> list[dict[str, Any]]:
        if not isinstance(raw, list):
            return []
        mapped: list[dict[str, Any]] = []
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            code = _text(entry.get("product_code"))
            if not code:
                continue
            mapped.append(
                {
                    "product_code": code,
                    "description": _text(entry.get("description")) or None,
                    "bom_level": as_int(entry.get("bom_level"), 0),
                }
            )
        return mapped

    def _map_item(self, item: dict[str, Any]) -> dict[str, Any]:
        code = _text(item.get("intermediate_code"))
        finished = self._map_finished_products(item.get("finished_products"))
        severity_map = self._severity_map()
        return {
            "id": f"{DETECTOR_ID}:{code}",
            "kind": DETECTOR_ID,
            "severity": severity_map["shared"],
            "intermediate_code": code or None,
            "intermediate_description": _text(item.get("intermediate_description"))
            or None,
            "intermediate_type": _text(item.get("intermediate_type")) or None,
            "shared_pa_count": as_int(item.get("shared_pa_count"), 0),
            "finished_products": finished,
            "root_code": code or None,
            "root_description": _text(item.get("intermediate_description")) or None,
        }

    def _fetch(self, *, branch: str, page: int, page_size: int) -> dict[str, Any]:
        try:
            return _unwrap_data(
                self._gateway.fetch_production_shared_structure_intermediates(
                    branch=branch,
                    movement_from=self._movement_from(),
                    lookback_days=self._lookback_days(),
                    page=page,
                    page_size=page_size,
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível conferir intermediários compartilhados."
            ) from exc

    def _summary_from(self, payload: dict[str, Any]) -> DetectorSummary:
        raw = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
        total = as_int(raw.get("shared_intermediate_count"), 0) or as_int(
            pagination.get("total"), 0
        )
        severity_map = self._severity_map()
        severity = severity_map["shared"] if total > 0 else severity_map["clear"]
        return DetectorSummary(
            count=total,
            severity=severity,
            metrics={
                "checked_pa_count": as_int(raw.get("checked_pa_count"), 0),
                "shared_intermediate_count": total,
                "max_shared_pa_count": as_int(raw.get("max_shared_pa_count"), 0),
                "movement_from": self._movement_from(),
            },
        )

    def summarize(self, *, branch: str) -> DetectorSummary:
        payload = self._fetch(branch=branch, page=1, page_size=1)
        return self._summary_from(payload)

    def collect(self, *, branch: str, page: int, page_size: int) -> DetectorPage:
        resolved_size = self._page_size(page_size)
        resolved_page = max(page, 1)
        payload = self._fetch(branch=branch, page=resolved_page, page_size=resolved_size)

        raw_items = payload.get("items")
        source = raw_items if isinstance(raw_items, list) else []
        items = [
            self._map_item(entry)
            for entry in source
            if isinstance(entry, dict)
        ]
        summary = self._summary_from(payload)
        return DetectorPage(
            items=items,
            total=summary.count,
            page=resolved_page,
            page_size=resolved_size,
            summary=summary,
        )

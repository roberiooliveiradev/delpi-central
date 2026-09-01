from __future__ import annotations

from collections import Counter
from typing import Any

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverRegistryService,
    get_device_driver_registry,
)
from production_pulse_app.domain.services.device_connectivity_status_service import (
    resolve_connectivity_status,
)
from production_pulse_app.domain.services.device_serialization_service import device_row_to_api
from production_pulse_app.infrastructure.persistence.repositories.postgres_operator_placement_repository import (
    PostgresOperatorPlacementRepository,
)


class OperatorPlacementService:
    def __init__(
        self,
        repository: PostgresOperatorPlacementRepository | None = None,
        driver_registry: DeviceDriverRegistryService | None = None,
    ) -> None:
        self._repository = repository or PostgresOperatorPlacementRepository()
        self._driver_registry = driver_registry or get_device_driver_registry()

    def _is_operator_eligible(self, driver_key: str) -> bool:
        resolved = self._driver_registry.resolve_driver(driver_key)
        return bool(resolved.definition.get("operatorEligible"))

    def _fetch_rows(
        self,
        *,
        branch: str,
        anchor_type: str | None = None,
        search: str | None = None,
        placement_key: str | None = None,
        operator_eligible_only: bool = False,
    ) -> list[dict[str, Any]]:
        rows = self._repository.list_bound_devices(
            branch=branch,
            anchor_type=anchor_type,
            search=search,
            placement_key=placement_key,
        )
        if not operator_eligible_only:
            return rows
        return [row for row in rows if self._is_operator_eligible(str(row.get("driver_key") or ""))]

    def list_placements(
        self,
        *,
        branch: str,
        anchor_type: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        rows = self._fetch_rows(
            branch=branch,
            anchor_type=anchor_type,
            search=search,
            operator_eligible_only=True,
        )
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            key = str(row.get("placement_key") or "")
            if not key:
                continue
            grouped.setdefault(key, []).append(row)

        items: list[dict[str, Any]] = []
        for placement_key, device_rows in grouped.items():
            first = device_rows[0]
            online_count = 0
            by_role: Counter[str] = Counter()
            primary_preview: dict[str, Any] | None = None

            for row in device_rows:
                role_key = str(row.get("role_key") or "")
                if role_key:
                    by_role[role_key] += 1
                connectivity = resolve_connectivity_status(row, has_binding=True)
                if connectivity.get("online"):
                    online_count += 1
                if primary_preview is None:
                    metrics = row.get("last_metrics") or {}
                    if isinstance(metrics, dict) and metrics:
                        metric_key = next(iter(metrics.keys()))
                        primary_preview = {
                            "key": metric_key,
                            "value": metrics.get(metric_key),
                        }

            items.append(
                {
                    "placementKey": placement_key,
                    "placementLabel": first.get("placement_label"),
                    "anchorType": first.get("anchor_type"),
                    "branch": first.get("branch"),
                    "deviceCount": len(device_rows),
                    "onlineCount": online_count,
                    "byRole": dict(by_role),
                    "primaryMetricPreview": primary_preview,
                }
            )

        items.sort(key=lambda item: str(item.get("placementLabel") or "").lower())
        return {"items": items}

    def list_placement_devices(
        self,
        *,
        branch: str,
        placement_key: str,
        role: str | None = None,
        operator_eligible_only: bool = True,
    ) -> dict[str, Any]:
        rows = self._fetch_rows(
            branch=branch,
            placement_key=placement_key,
            operator_eligible_only=operator_eligible_only,
        )
        if role:
            rows = [row for row in rows if str(row.get("role_key") or "") == role]

        items: list[dict[str, Any]] = []
        for row in rows:
            payload = device_row_to_api(
                row,
                capabilities=self._driver_registry.build_capabilities(str(row["driver_key"])),
            )
            connectivity = resolve_connectivity_status(row, has_binding=True)
            payload["status"] = connectivity["status"]
            payload["online"] = connectivity["online"]
            payload["graceSeconds"] = connectivity["graceSeconds"]
            payload["placementKey"] = row.get("placement_key")
            payload["placementLabel"] = row.get("placement_label")
            payload["anchorType"] = row.get("anchor_type")
            items.append(payload)

        return {"items": items}

from __future__ import annotations

from app.application.dto.strategic_indicators.get_departments_response import (
    DepartmentListItemResponse,
    DepartmentVariationResponse,
    GetStrategicIndicatorsDepartmentsResponse,
)
from app.domain.ports.strategic_indicators.departments_catalog_port import (
    StrategicIndicatorsDepartmentsCatalogPort,
)
from app.domain.ports.strategic_indicators.departments_snapshot_port import (
    StrategicIndicatorsDepartmentsSnapshotPort,
)


class GetStrategicIndicatorsDepartmentsUseCase:
    def __init__(
        self,
        catalog_port: StrategicIndicatorsDepartmentsCatalogPort,
        snapshot_port: StrategicIndicatorsDepartmentsSnapshotPort,
    ) -> None:
        self._catalog_port = catalog_port
        self._snapshot_port = snapshot_port

    def execute(self) -> GetStrategicIndicatorsDepartmentsResponse:
        catalog = self._catalog_port.get_departments_catalog()
        snapshot = self._snapshot_port.get_departments_snapshot()

        snapshot_map = {
            item["department_id"]: item
            for item in snapshot
            if item.get("department_id")
        }

        items: list[DepartmentListItemResponse] = []

        for department in catalog:
            department_id = department["department_id"]
            department_snapshot = snapshot_map.get(department_id)

            if department_snapshot is None:
                continue

            variation = department_snapshot.get("variation", {})

            items.append(
                DepartmentListItemResponse(
                    id=department_id,
                    name=department["department_name"],
                    short_name=department.get("short_name", ""),
                    weight_pct=int(department["department_weight_pct"]),
                    score=float(department_snapshot.get("score", 0)),
                    classification=department_snapshot.get("classification", ""),
                    contribution=float(department_snapshot.get("contribution", 0)),
                    aggregation_mode=department.get(
                        "aggregation_mode",
                        "consolidated",
                    ),
                    strategic_summary=department.get("strategic_summary", ""),
                    variation=DepartmentVariationResponse(
                        value=float(variation.get("value", 0)),
                        direction=variation.get("direction", "stable"),
                    ),
                )
            )

        return GetStrategicIndicatorsDepartmentsResponse(items=items)
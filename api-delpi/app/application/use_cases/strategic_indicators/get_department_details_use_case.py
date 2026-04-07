from __future__ import annotations

from app.application.dto.strategic_indicators.get_department_details_response import (
    DepartmentDetailsVariationResponse,
    DepartmentIndicatorDetailsResponse,
    DepartmentUnitScoreResponse,
    GetStrategicIndicatorsDepartmentDetailsResponse,
)
from app.domain.ports.strategic_indicators.department_details_snapshot_port import (
    StrategicIndicatorsDepartmentDetailsSnapshotPort,
)
from app.domain.ports.strategic_indicators.departments_catalog_port import (
    StrategicIndicatorsDepartmentsCatalogPort,
)


class DepartmentNotFoundError(ValueError):
    pass


class GetStrategicIndicatorsDepartmentDetailsUseCase:
    def __init__(
        self,
        catalog_port: StrategicIndicatorsDepartmentsCatalogPort,
        details_snapshot_port: StrategicIndicatorsDepartmentDetailsSnapshotPort,
    ) -> None:
        self._catalog_port = catalog_port
        self._details_snapshot_port = details_snapshot_port

    def execute(
        self,
        department_id: str,
    ) -> GetStrategicIndicatorsDepartmentDetailsResponse:
        catalog = self._catalog_port.get_departments_catalog()
        department = next(
            (
                item
                for item in catalog
                if item.get("department_id") == department_id
            ),
            None,
        )

        if department is None:
            raise DepartmentNotFoundError("Departamento não encontrado.")

        snapshot = self._details_snapshot_port.get_department_details_snapshot(
            department_id,
        )

        if snapshot is None:
            raise DepartmentNotFoundError("Snapshot do departamento não encontrado.")

        catalog_indicators = {
            item["id"]: item
            for item in department.get("indicators", [])
            if item.get("id")
        }

        indicators: list[DepartmentIndicatorDetailsResponse] = []
        for item in snapshot.get("indicators", []):
            indicator_id = item["id"]
            catalog_indicator = catalog_indicators.get(indicator_id, {})

            indicators.append(
                DepartmentIndicatorDetailsResponse(
                    id=indicator_id,
                    name=catalog_indicator.get("name", item.get("name", "")),
                    weight_pct=int(catalog_indicator.get("weight_pct", 0)),
                    goal_2026=catalog_indicator.get("goal_2026", ""),
                    strategic_description=catalog_indicator.get(
                        "strategic_description",
                        "",
                    ),
                    scope_type=catalog_indicator.get("scope_type", "consolidated"),
                    realized=item.get("realized", {}),
                    score=float(item.get("score", 0)),
                    gap=float(item.get("gap", 0)),
                    trend=item.get("trend", "stable"),
                )
            )

        variation = snapshot.get("variation", {})

        return GetStrategicIndicatorsDepartmentDetailsResponse(
            id=department["department_id"],
            name=department["department_name"],
            short_name=department.get("short_name", ""),
            weight_pct=int(department["department_weight_pct"]),
            score=float(snapshot.get("score", 0)),
            classification=snapshot.get("classification", ""),
            contribution=float(snapshot.get("contribution", 0)),
            aggregation_mode=department.get("aggregation_mode", "consolidated"),
            strategic_summary=department.get("strategic_summary", ""),
            variation=DepartmentDetailsVariationResponse(
                value=float(variation.get("value", 0)),
                direction=variation.get("direction", "stable"),
            ),
            units=[
                DepartmentUnitScoreResponse(
                    unit_id=unit.get("unit_id", ""),
                    unit_name=unit.get("unit_name", ""),
                    score=float(unit.get("score", 0)),
                    classification=unit.get("classification", ""),
                )
                for unit in snapshot.get("units", [])
            ],
            indicators=indicators,
        )
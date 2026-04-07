from __future__ import annotations

from app.domain.ports.strategic_indicators.department_snapshot_port import (
    StrategicIndicatorsDepartmentSnapshotPort,
)


class StaticStrategicIndicatorsDepartmentSnapshotProvider(
    StrategicIndicatorsDepartmentSnapshotPort
):
    def get_department_snapshots(self) -> list[dict]:
        return [
            {"department_id": "financial", "score": 7.8, "trend": "up"},
            {"department_id": "hr", "score": 8.0, "trend": "up"},
            {"department_id": "commercial", "score": 8.2, "trend": "up"},
            {"department_id": "production", "score": 7.8, "trend": "up"},
            {"department_id": "quality", "score": 7.4, "trend": "up"},
            {"department_id": "supplies", "score": 7.1, "trend": "down"},
            {"department_id": "engineering", "score": 7.9, "trend": "up"},
        ]
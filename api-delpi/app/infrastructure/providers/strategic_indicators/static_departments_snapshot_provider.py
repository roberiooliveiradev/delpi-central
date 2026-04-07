from __future__ import annotations

from app.domain.ports.strategic_indicators.departments_snapshot_port import (
    StrategicIndicatorsDepartmentsSnapshotPort,
)


class StaticStrategicIndicatorsDepartmentsSnapshotProvider(
    StrategicIndicatorsDepartmentsSnapshotPort,
):
    def get_departments_snapshot(self) -> list[dict]:
        return [
            {
                "department_id": "financial",
                "score": 7.8,
                "classification": "Satisfatório com Alertas",
                "contribution": 1.17,
                "variation": {"value": 0.1, "direction": "up"},
            },
            {
                "department_id": "hr",
                "score": 8.0,
                "classification": "Alto Desempenho",
                "contribution": 1.2,
                "variation": {"value": 0.1, "direction": "up"},
            },
            {
                "department_id": "commercial",
                "score": 8.2,
                "classification": "Alto Desempenho",
                "contribution": 1.394,
                "variation": {"value": 0.2, "direction": "up"},
            },
            {
                "department_id": "production",
                "score": 7.8,
                "classification": "Satisfatório com Alertas",
                "contribution": 1.326,
                "variation": {"value": 0.1, "direction": "up"},
            },
            {
                "department_id": "quality",
                "score": 7.4,
                "classification": "Satisfatório com Alertas",
                "contribution": 1.036,
                "variation": {"value": 0.2, "direction": "up"},
            },
            {
                "department_id": "supplies",
                "score": 7.1,
                "classification": "Satisfatório com Alertas",
                "contribution": 0.852,
                "variation": {"value": -0.2, "direction": "down"},
            },
            {
                "department_id": "engineering",
                "score": 7.9,
                "classification": "Satisfatório com Alertas",
                "contribution": 0.79,
                "variation": {"value": 0.1, "direction": "up"},
            },
        ]
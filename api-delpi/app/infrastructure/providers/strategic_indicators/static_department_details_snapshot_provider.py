from __future__ import annotations

from app.domain.ports.strategic_indicators.department_details_snapshot_port import (
    StrategicIndicatorsDepartmentDetailsSnapshotPort,
)


class StaticStrategicIndicatorsDepartmentDetailsSnapshotProvider(
    StrategicIndicatorsDepartmentDetailsSnapshotPort,
):
    def get_department_details_snapshot(self, department_id: str) -> dict | None:
        data = {
            "financial": {
                "score": 7.8,
                "classification": "Satisfatório com Alertas",
                "contribution": 1.17,
                "variation": {"value": 0.1, "direction": "up"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 7.9,
                        "classification": "Satisfatório com Alertas",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 7.7,
                        "classification": "Satisfatório com Alertas",
                    },
                ],
                "indicators": [
                    {
                        "id": "financial-ebitda",
                        "realized": {"matrix": 13.3, "branch": 12.7},
                        "score": 8.2,
                        "gap": 0.0,
                        "trend": "up",
                    },
                    {
                        "id": "financial-fixed-costs",
                        "realized": {"matrix": 14.2, "branch": 14.8},
                        "score": 7.5,
                        "gap": 0.8,
                        "trend": "stable",
                    },
                    {
                        "id": "financial-pmr",
                        "realized": {"matrix": 37, "branch": 41},
                        "score": 7.7,
                        "gap": 2.0,
                        "trend": "stable",
                    },
                ],
            },
            "hr": {
                "score": 8.0,
                "classification": "Alto Desempenho",
                "contribution": 1.2,
                "variation": {"value": 0.1, "direction": "up"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 8.1,
                        "classification": "Alto Desempenho",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 7.9,
                        "classification": "Satisfatório com Alertas",
                    },
                ],
                "indicators": [
                    {
                        "id": "hr-absenteeism",
                        "realized": {"matrix": 1.9, "branch": 2.2},
                        "score": 7.6,
                        "gap": 0.2,
                        "trend": "stable",
                    },
                    {
                        "id": "hr-turnover",
                        "realized": {"matrix": 1.3, "branch": 1.6},
                        "score": 8.1,
                        "gap": 0.1,
                        "trend": "up",
                    },
                    {
                        "id": "hr-satisfaction",
                        "realized": {"matrix": 87, "branch": 84},
                        "score": 8.3,
                        "gap": -1.0,
                        "trend": "up",
                    },
                    {
                        "id": "hr-pdi",
                        "realized": {"matrix": 100, "branch": 96},
                        "score": 8.0,
                        "gap": 4.0,
                        "trend": "stable",
                    },
                    {
                        "id": "hr-training",
                        "realized": {"matrix": 2.1, "branch": 1.8},
                        "score": 7.9,
                        "gap": 0.2,
                        "trend": "stable",
                    },
                ],
            },
            "commercial": {
                "score": 8.2,
                "classification": "Alto Desempenho",
                "contribution": 1.394,
                "variation": {"value": 0.2, "direction": "up"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 8.3,
                        "classification": "Alto Desempenho",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 8.1,
                        "classification": "Alto Desempenho",
                    },
                ],
                "indicators": [
                    {
                        "id": "commercial-rol-matrix",
                        "realized": {"matrix": 102.0},
                        "score": 8.4,
                        "gap": -2.0,
                        "trend": "up",
                    },
                    {
                        "id": "commercial-rol-branch",
                        "realized": {"branch": 99.0},
                        "score": 8.1,
                        "gap": 1.0,
                        "trend": "stable",
                    },
                    {
                        "id": "commercial-closing-rate",
                        "realized": {"consolidated": 31.0},
                        "score": 8.0,
                        "gap": -1.0,
                        "trend": "up",
                    },
                    {
                        "id": "commercial-new-clients",
                        "realized": {"consolidated": 9.5},
                        "score": 7.8,
                        "gap": 0.5,
                        "trend": "stable",
                    },
                    {
                        "id": "commercial-new-rol",
                        "realized": {"consolidated": 11.4},
                        "score": 7.5,
                        "gap": 0.6,
                        "trend": "stable",
                    },
                ],
            },
            "production": {
                "score": 7.8,
                "classification": "Satisfatório com Alertas",
                "contribution": 1.326,
                "variation": {"value": 0.1, "direction": "up"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 7.9,
                        "classification": "Satisfatório com Alertas",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 7.7,
                        "classification": "Satisfatório com Alertas",
                    },
                ],
                "indicators": [
                    {
                        "id": "production-direct-labor",
                        "realized": {"matrix": 9.7, "branch": 10.5},
                        "score": 7.4,
                        "gap": 0.5,
                        "trend": "stable",
                    },
                    {
                        "id": "production-costs",
                        "realized": {"matrix": 31.8, "branch": 32.7},
                        "score": 7.2,
                        "gap": 0.7,
                        "trend": "stable",
                    },
                    {
                        "id": "production-depreciation",
                        "realized": {"matrix": 1.4, "branch": 1.6},
                        "score": 7.6,
                        "gap": 0.1,
                        "trend": "stable",
                    },
                    {
                        "id": "production-oee",
                        "realized": {"matrix": 72.4, "branch": 68.1},
                        "score": 8.0,
                        "gap": 1.9,
                        "trend": "up",
                    },
                    {
                        "id": "production-otd",
                        "realized": {"matrix": 92.8, "branch": 91.1},
                        "score": 7.9,
                        "gap": 0.9,
                        "trend": "stable",
                    },
                ],
            },
            "quality": {
                "score": 7.4,
                "classification": "Satisfatório com Alertas",
                "contribution": 1.036,
                "variation": {"value": 0.2, "direction": "up"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 7.5,
                        "classification": "Satisfatório com Alertas",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 7.3,
                        "classification": "Satisfatório com Alertas",
                    },
                ],
                "indicators": [
                    {
                        "id": "quality-ppm-internal",
                        "realized": {"matrix": 1320, "branch": 1480},
                        "score": 7.3,
                        "gap": 80.0,
                        "trend": "stable",
                    },
                    {
                        "id": "quality-ppm-external",
                        "realized": {"matrix": 1080, "branch": 1190},
                        "score": 6.8,
                        "gap": 90.0,
                        "trend": "down",
                    },
                    {
                        "id": "quality-kaizen-ideas",
                        "realized": {"matrix": 7, "branch": 8},
                        "score": 7.7,
                        "gap": 1.0,
                        "trend": "stable",
                    },
                    {
                        "id": "quality-audit-5s",
                        "realized": {"matrix": 81, "branch": 78},
                        "score": 7.8,
                        "gap": 2.0,
                        "trend": "stable",
                    },
                    {
                        "id": "quality-kaizen-financial",
                        "realized": {"matrix": 4700, "branch": 4200},
                        "score": 7.2,
                        "gap": 300.0,
                        "trend": "stable",
                    },
                ],
            },
            "supplies": {
                "score": 7.1,
                "classification": "Satisfatório com Alertas",
                "contribution": 0.852,
                "variation": {"value": -0.2, "direction": "down"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 7.1,
                        "classification": "Satisfatório com Alertas",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 7.1,
                        "classification": "Satisfatório com Alertas",
                    },
                ],
                "indicators": [
                    {
                        "id": "supplies-cpv",
                        "realized": {"consolidated": 51.0},
                        "score": 7.0,
                        "gap": 0.5,
                        "trend": "stable",
                    },
                    {
                        "id": "supplies-otd-purchases",
                        "realized": {"consolidated": 90.8},
                        "score": 7.1,
                        "gap": 1.2,
                        "trend": "down",
                    },
                    {
                        "id": "supplies-stock-turnover",
                        "realized": {"consolidated": 2.02},
                        "score": 7.0,
                        "gap": 0.07,
                        "trend": "stable",
                    },
                    {
                        "id": "supplies-total-stock",
                        "realized": {"consolidated": 13800000},
                        "score": 6.9,
                        "gap": 300000.0,
                        "trend": "down",
                    },
                    {
                        "id": "supplies-purchase-savings",
                        "realized": {"consolidated": 18300},
                        "score": 7.4,
                        "gap": 1700.0,
                        "trend": "stable",
                    },
                ],
            },
            "engineering": {
                "score": 7.9,
                "classification": "Satisfatório com Alertas",
                "contribution": 0.79,
                "variation": {"value": 0.1, "direction": "up"},
                "units": [
                    {
                        "unit_id": "matrix",
                        "unit_name": "Matriz",
                        "score": 8.0,
                        "classification": "Alto Desempenho",
                    },
                    {
                        "unit_id": "branch",
                        "unit_name": "Filial",
                        "score": 7.8,
                        "classification": "Satisfatório com Alertas",
                    },
                ],
                "indicators": [
                    {
                        "id": "engineering-projects-on-time",
                        "realized": {"matrix": 96.0, "branch": 93.0},
                        "score": 7.8,
                        "gap": 2.0,
                        "trend": "stable",
                    },
                    {
                        "id": "engineering-transforma-plus",
                        "realized": {"matrix": 15500, "branch": 14800},
                        "score": 8.0,
                        "gap": 200.0,
                        "trend": "up",
                    },
                ],
            },
        }

        department = data.get(department_id)
        if department is None:
            return None

        return {
            "department_id": department_id,
            **department,
        }
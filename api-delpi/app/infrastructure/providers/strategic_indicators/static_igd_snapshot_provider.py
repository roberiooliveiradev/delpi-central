from __future__ import annotations

from datetime import date

from app.domain.ports.strategic_indicators.igd_snapshot_port import (
    StrategicIndicatorsIgdSnapshotPort,
)


class StaticStrategicIndicatorsIgdSnapshotProvider(
    StrategicIndicatorsIgdSnapshotPort
):
    def get_igd_snapshot(self) -> dict:
        return {
            "competence": date.today().strftime("%Y-%m"),
            "igd": 7.8,
            "igd_exact": 7.768,
            "classification": "Satisfatório com Alertas",
            "variation": {
                "value": 0.2,
                "direction": "up",
                "vs_label": "vs período anterior",
            },
        }
from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsDepartmentSnapshotPort(ABC):
    @abstractmethod
    def get_department_snapshots(self) -> list[dict]:
        """
        Retorna snapshot executivo por departamento.
        Cada item deve conter, no mínimo:
        - department_id
        - score
        - trend
        Pode conter também:
        - short_name
        - strategic_summary
        - key_indicators
        """
        raise NotImplementedError
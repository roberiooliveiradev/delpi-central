from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsDepartmentsSnapshotPort(ABC):
    @abstractmethod
    def get_departments_snapshot(self) -> list[dict]:
        """
        Retorna snapshot consolidado dos departamentos para a visão comparativa.
        Cada item deve conter:
        - department_id
        - score
        - classification
        - contribution
        - variation
        """
        raise NotImplementedError
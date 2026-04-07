from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsDepartmentDetailsSnapshotPort(ABC):
    @abstractmethod
    def get_department_details_snapshot(self, department_id: str) -> dict | None:
        """
        Retorna snapshot detalhado de uma área:
        - department_id
        - score
        - classification
        - contribution
        - variation
        - units[]
        - indicators[]
        """
        raise NotImplementedError
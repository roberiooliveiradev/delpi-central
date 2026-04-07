from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsDepartmentsCatalogPort(ABC):
    @abstractmethod
    def get_departments_catalog(self) -> list[dict]:
        """
        Retorna o catálogo estrutural dos departamentos a partir do módulo:
        - department_id
        - department_name
        - short_name
        - department_weight_pct
        - aggregation_mode
        - units
        - strategic_summary
        - indicators
        """
        raise NotImplementedError
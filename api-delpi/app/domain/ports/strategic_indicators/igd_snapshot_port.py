from __future__ import annotations

from abc import ABC, abstractmethod


class StrategicIndicatorsIgdSnapshotPort(ABC):
    @abstractmethod
    def get_igd_snapshot(self) -> dict:
        """
        Retorna snapshot consolidado do IGD:
        - competence
        - igd
        - igd_exact
        - classification
        - variation
        """
        raise NotImplementedError
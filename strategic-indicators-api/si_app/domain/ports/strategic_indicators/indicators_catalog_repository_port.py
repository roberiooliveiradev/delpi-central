from __future__ import annotations

from abc import ABC, abstractmethod

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
)


class StrategicIndicatorsIndicatorsCatalogRepositoryPort(ABC):
    @abstractmethod
    def list_indicators_catalog(self) -> list[StrategicIndicatorCatalogItem]:
        raise NotImplementedError

    @abstractmethod
    def list_indicators_catalog_by_department(
        self,
        department_id: str,
    ) -> list[StrategicIndicatorCatalogItem]:
        raise NotImplementedError
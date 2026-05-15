from __future__ import annotations

from abc import ABC, abstractmethod

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
)


class StrategicIndicatorsDepartmentsCatalogRepositoryPort(ABC):
    @abstractmethod
    def list_departments_catalog(self) -> list[StrategicDepartmentCatalogItem]:
        raise NotImplementedError
from __future__ import annotations

from abc import ABC, abstractmethod

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
)


class StrategicIndicatorsResolvedIndicatorsCatalogRepositoryPort(ABC):
    @abstractmethod
    def list_resolved_indicators_catalog(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        department_id: str | None = None,
        branch: str | None = None,
    ) -> list[StrategicIndicatorCatalogItem]:
        raise NotImplementedError
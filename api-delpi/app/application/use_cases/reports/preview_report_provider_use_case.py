"""Preview autenticado do provider safety_stock_shortage_30d."""

from __future__ import annotations

from typing import Any, Mapping

from app.domain.services.reports.report_types import ReportDataset


class PreviewReportProviderUseCase:
    def __init__(self, provider: Any) -> None:
        self._provider = provider

    def execute(self, params: Mapping[str, Any]) -> dict[str, Any]:
        dataset: ReportDataset = self._provider.collect(params)
        return {
            "items": [dict(row) for row in dataset.rows],
            "total": dataset.row_count,
            "title": dataset.title,
            "columns": list(dataset.columns),
            "meta": dict(dataset.meta),
            "providerKey": dataset.provider_key,
        }

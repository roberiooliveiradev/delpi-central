"""Preview autenticado do provider safety_stock_shortage_30d."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from app.application.services.reports.shortage_item_note_observation_enrichment_service import (
    ShortageItemNoteObservationEnrichmentService,
)
from app.domain.services.reports.report_types import ReportDataset
from app.domain.services.reports.safety_stock_shortage_30d_rules import PROVIDER_KEY


class _NotesRepo(Protocol):
    def get_shortage_item_notes_by_product(
        self,
        *,
        definition_id: str,
        branch: str,
    ) -> dict[str, dict[str, Any]]: ...


class PreviewReportProviderUseCase:
    def __init__(
        self,
        provider: Any,
        *,
        repository: _NotesRepo | None = None,
    ) -> None:
        self._provider = provider
        self._repository = repository

    def execute(
        self,
        params: Mapping[str, Any],
        *,
        definition_id: str | None = None,
    ) -> dict[str, Any]:
        dataset: ReportDataset = self._provider.collect(params)
        dataset = self._enrich_observation_notes(
            dataset,
            params=params,
            definition_id=definition_id,
        )
        return {
            "items": [dict(row) for row in dataset.rows],
            "total": dataset.row_count,
            "title": dataset.title,
            "columns": list(dataset.columns),
            "meta": dict(dataset.meta),
            "providerKey": dataset.provider_key,
        }

    def _enrich_observation_notes(
        self,
        dataset: ReportDataset,
        *,
        params: Mapping[str, Any],
        definition_id: str | None,
    ) -> ReportDataset:
        if not definition_id or self._repository is None:
            return dataset
        if dataset.provider_key != PROVIDER_KEY:
            return dataset
        branch = str(params.get("branch") or "").strip()
        if not branch:
            return dataset
        notes = self._repository.get_shortage_item_notes_by_product(
            definition_id=str(definition_id).strip(),
            branch=branch,
        )
        return ShortageItemNoteObservationEnrichmentService.enrich_dataset(
            dataset,
            notes if isinstance(notes, dict) else None,
        )

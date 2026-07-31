"""Enriquece a coluna Observação com notas de acompanhamento (Delpi Reports)."""

from __future__ import annotations

from typing import Any, Mapping

from app.domain.services.reports.report_types import ReportDataset
from app.domain.services.reports.safety_stock_shortage_30d_rules import (
    PROVIDER_KEY,
    build_follow_up_observation,
)


class ShortageItemNoteObservationEnrichmentService:
    """Pós-collect: anexa acompanhamento humano sem ocultar itens do e-mail."""

    @classmethod
    def enrich_dataset(
        cls,
        dataset: ReportDataset,
        notes_by_product: Mapping[str, Mapping[str, Any]] | None,
    ) -> ReportDataset:
        if dataset.provider_key != PROVIDER_KEY:
            return dataset
        if not isinstance(notes_by_product, Mapping) or not notes_by_product:
            return dataset

        enriched_rows: list[dict[str, Any]] = []
        applied = 0
        for raw in dataset.rows:
            row = dict(raw)
            code = str(row.get("product_code") or "").strip()
            note = notes_by_product.get(code) if code else None
            if not isinstance(note, Mapping):
                enriched_rows.append(row)
                continue
            follow_up = build_follow_up_observation(
                note.get("authorDisplayName"),
                note.get("noteText"),
                note.get("expectedReceiptDate"),
            )
            if not follow_up:
                enriched_rows.append(row)
                continue
            # Com acompanhamento humano, a observação de sistema (terceiro/amostra)
            # deixa de aparecer — só o trecho operacional.
            row["observation"] = follow_up
            applied += 1
            enriched_rows.append(row)

        meta = dict(dataset.meta)
        if applied:
            meta["followUpNotesApplied"] = applied
        return ReportDataset(
            provider_key=dataset.provider_key,
            title=dataset.title,
            columns=dataset.columns,
            rows=tuple(enriched_rows),
            meta=meta,
        )

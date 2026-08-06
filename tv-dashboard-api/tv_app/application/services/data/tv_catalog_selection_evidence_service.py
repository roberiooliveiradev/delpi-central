"""Adapter de evidência para candidatos de seleção (preview amostral; falha soft)."""

from __future__ import annotations

import logging
from typing import Any, Callable

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)

logger = logging.getLogger(__name__)


class TvCatalogSelectionEvidenceService:
    """Enriquece top-N candidatos com amostra tabular via preview-block.

    Evidência é metadata de seleção — nunca alimenta renderPlan / Automático.
    Falha de preview não remove o candidato.
    """

    @classmethod
    def enrich(
        cls,
        candidates: list[dict[str, Any]],
        *,
        authorization: str | None = None,
        user: Any | None = None,
        preview_fn: Callable[..., dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []
        max_n = TvCopilotContentService.setting_int("routeEvidenceMaxCandidates", 3)
        max_rows = TvCopilotContentService.setting_int("routeEvidenceMaxRows", 5)
        out: list[dict[str, Any]] = []
        for index, row in enumerate(candidates):
            if not isinstance(row, dict):
                continue
            item = dict(row)
            if index < max_n:
                evidence = cls._sample_evidence(
                    str(item.get("operationId") or item.get("id") or "").strip(),
                    authorization=authorization,
                    user=user,
                    max_rows=max_rows,
                    preview_fn=preview_fn,
                )
                if evidence:
                    item["evidence"] = evidence
            out.append(item)
        return out

    @classmethod
    def _sample_evidence(
        cls,
        operation_id: str,
        *,
        authorization: str | None,
        user: Any | None,
        max_rows: int,
        preview_fn: Callable[..., dict[str, Any]] | None,
    ) -> dict[str, Any] | None:
        if not operation_id:
            return None
        # Sem auth/preview injetado: não dispara HTTP (suggest unitário / dry-run).
        if preview_fn is None and not authorization and user is None:
            return None
        try:
            selected = cls._run_preview(
                operation_id,
                authorization=authorization,
                user=user,
                max_rows=max_rows,
                preview_fn=preview_fn,
            )
        except Exception:  # noqa: BLE001 — evidência é best-effort
            logger.debug(
                "selection_evidence_preview_failed operationId=%s",
                operation_id,
                exc_info=True,
            )
            return None
        return cls._evidence_from_preview(selected, max_rows=max_rows)

    @classmethod
    def _run_preview(
        cls,
        operation_id: str,
        *,
        authorization: str | None,
        user: Any | None,
        max_rows: int,
        preview_fn: Callable[..., dict[str, Any]] | None,
    ) -> dict[str, Any]:
        block = {
            "id": f"sel_ev_{operation_id}",
            "type": "kpi",
            "dataBinding": {
                "operationId": operation_id,
                "params": {},
                "displayMode": "auto",
            },
        }
        native_config = {"blocks": [block]}
        options = {"maxRows": max_rows, "includeColumnProfile": False}
        if preview_fn is not None:
            return preview_fn(
                block,
                native_config=native_config,
                authorization=authorization,
                user=user,
                preview_options=options,
            )
        from tv_app.application.services.data.tv_data_preview_service import (
            TvDataPreviewService,
        )

        return TvDataPreviewService().preview_block(
            block,
            native_config=native_config,
            authorization=authorization,
            user=user,
            preview_options=options,
        )

    @classmethod
    def _evidence_from_preview(
        cls,
        selected: dict[str, Any] | None,
        *,
        max_rows: int,
    ) -> dict[str, Any] | None:
        if not isinstance(selected, dict):
            return None
        resolved = selected.get("resolved")
        if not isinstance(resolved, dict):
            return None
        columns, rows = cls._table_from_resolved(resolved)
        if not columns and not rows:
            return None
        truncated = len(rows) > max_rows
        return {
            "shape": "table",
            "columns": columns,
            "rows": rows[: max(0, max_rows)],
            "truncated": truncated,
        }

    @classmethod
    def _table_from_resolved(
        cls,
        resolved: dict[str, Any],
    ) -> tuple[list[str], list[list[Any]]]:
        # Prefer payload tabular (items / rows); fallback a pares KPI.
        data = resolved.get("data")
        if isinstance(data, dict):
            items = data.get("items")
            if isinstance(items, list) and items and isinstance(items[0], dict):
                keys = [str(k) for k in items[0].keys()]
                rows = [
                    [row.get(k) for k in keys]
                    for row in items
                    if isinstance(row, dict)
                ]
                return keys, rows
            # Scalar / KPI: uma linha chave→valor
            pairs = [
                (str(k), v)
                for k, v in data.items()
                if k not in {"items", "pagination", "summary", "meta"}
            ]
            if pairs:
                return ["campo", "valor"], [[k, v] for k, v in pairs[:12]]

        table = resolved.get("table")
        if isinstance(table, dict):
            cols = table.get("columns") or table.get("headers")
            rows = table.get("rows") or table.get("data")
            if isinstance(cols, list) and isinstance(rows, list):
                return [str(c) for c in cols], [
                    list(r) if isinstance(r, (list, tuple)) else [r] for r in rows
                ]
        return [], []

"""Métricas de observabilidade — skill Análise de Desenhos DELPI (Onda 12.6)."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatDrawingMetricsService:
    """Snapshot leve para metadata, adminDebug e auditoria."""

    @classmethod
    def build_snapshot(
        cls,
        drawing: dict[str, Any],
        *,
        latency_ms: int | None = None,
        report_exported: bool = False,
        analyser_ok: bool | None = None,
    ) -> dict[str, Any]:
        items = drawing.get("items") if isinstance(drawing.get("items"), list) else []
        status_counter: Counter[str] = Counter()

        for item in items:
            if isinstance(item, dict):
                status_counter[str(item.get("status") or "unknown")] += 1

        sections = sorted(
            {
                str(item.get("section"))
                for item in items
                if isinstance(item, dict) and item.get("section")
            }
        )

        return {
            "productCode": drawing.get("productCode"),
            "overallStatus": drawing.get("status"),
            "overallLabel": drawing.get("overallLabel"),
            "criticalErrors": int(drawing.get("criticalErrors") or 0),
            "errors": int(drawing.get("errors") or 0),
            "warnings": int(drawing.get("warnings") or 0),
            "checklistItems": len(items),
            "sections": sections,
            "itemsByStatus": dict(status_counter),
            "hasPdfAttachment": bool(drawing.get("hasPdfAttachment")),
            "pdfLegible": drawing.get("pdfLegible"),
            "reportExported": bool(report_exported),
            "analyserOk": analyser_ok,
            "latencyMs": latency_ms,
        }

    @classmethod
    def _resolve_drawing(
        cls,
        *,
        intelligence: dict | None,
        tool_context: dict | None,
    ) -> dict[str, Any] | None:
        if isinstance(intelligence, dict):
            drawing = intelligence.get("drawingAnalysis")

            if isinstance(drawing, dict):
                return drawing

        if isinstance(tool_context, dict):
            drawing = tool_context.get("drawingAnalysis")

            if isinstance(drawing, dict):
                return drawing

        return None

    @classmethod
    @classmethod
    def resolve_analyser_ok(cls, tool_context: dict | None) -> bool | None:
        if not isinstance(tool_context, dict):
            return None

        for call in tool_context.get("toolCalls") or []:
            if not isinstance(call, dict):
                continue

            metadata = call.get("metadata") or {}
            path = str(metadata.get("path") or "").lower()

            if "/analyser" not in path and (call.get("arguments") or {}).get(
                "actionId"
            ) != "get_product_analyser":
                continue

            return metadata.get("ok") is True

        return None

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        intelligence: dict | None = None,
        tool_context: dict | None = None,
        latency_ms: int | None = None,
    ) -> None:
        drawing = cls._resolve_drawing(intelligence=intelligence, tool_context=tool_context)

        if not drawing:
            return

        export = None

        if isinstance(tool_context, dict):
            export = tool_context.get("drawingAnalysisExport")

        if not isinstance(export, dict):
            export = metadata.get("drawingAnalysisExport")

        snapshot = cls.build_snapshot(
            drawing,
            latency_ms=latency_ms,
            report_exported=bool(isinstance(export, dict) and export.get("markdown")),
            analyser_ok=cls.resolve_analyser_ok(tool_context),
        )
        metadata["drawingAnalysisMetrics"] = snapshot

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        intelligence: dict | None = None,
        tool_context: dict | None = None,
        latency_ms: int | None = None,
    ) -> dict:
        drawing = cls._resolve_drawing(intelligence=intelligence, tool_context=tool_context)

        if not drawing:
            return audit_metadata

        export = tool_context.get("drawingAnalysisExport") if isinstance(tool_context, dict) else None

        audit_metadata["drawingAnalysis"] = cls.build_snapshot(
            drawing,
            latency_ms=latency_ms,
            report_exported=bool(isinstance(export, dict) and export.get("markdown")),
            analyser_ok=cls.resolve_analyser_ok(tool_context),
        )

        return audit_metadata

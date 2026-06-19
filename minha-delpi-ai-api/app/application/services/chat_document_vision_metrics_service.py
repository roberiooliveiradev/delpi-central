"""Métricas de observabilidade — skill Visão de Documentos DELPI (Onda 13.6)."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatDocumentVisionMetricsService:
    """Snapshot leve para metadata, adminDebug e auditoria."""

    TRACKED_STAGES = (
        "native",
        "tesseract",
        "tesseract_pdf",
        "tesseract_stamp_crop",
        "tesseract_region_detail",
        "tesseract_image",
        "bom_heuristic",
        "table_heuristic",
        "docling",
        "paddleocr",
        "ollama_vlm",
    )

    @classmethod
    def stage_usage_from_stages(cls, stages: list | None) -> dict[str, int]:
        usage = {name: 0 for name in cls.TRACKED_STAGES}
        normalized = stages if isinstance(stages, list) else []

        for stage in normalized:
            key = str(stage or "").strip()

            if key in usage:
                usage[key] += 1

        return {key: count for key, count in usage.items() if count > 0}

    @classmethod
    def build_snapshot(
        cls,
        vision: dict[str, Any],
        *,
        char_count: int | None = None,
        legible: bool | None = None,
        context: str = "drawing",
    ) -> dict[str, Any]:
        stages = vision.get("stages") if isinstance(vision.get("stages"), list) else []
        engine = str(vision.get("engine") or "unknown").strip() or "unknown"
        stage_usage = cls.stage_usage_from_stages(stages)

        return {
            "context": context,
            "engine": engine,
            "schemaVersion": vision.get("schemaVersion"),
            "stages": stages,
            "stageCount": len(stages),
            "stageUsage": stage_usage,
            "legibilityScore": vision.get("legibilityScore"),
            "durationMs": vision.get("durationMs"),
            "charCount": char_count if char_count is not None else vision.get("charCount"),
            "legible": legible if legible is not None else vision.get("legible"),
            "bomRowCount": vision.get("bomRowCount"),
            "hasTitleBlock": bool(vision.get("titleBlock")),
            "tableCount": vision.get("tableCount"),
        }

    @classmethod
    def _resolve_vision(
        cls,
        *,
        intelligence: dict | None,
        tool_context: dict | None,
    ) -> tuple[dict[str, Any] | None, int | None, bool | None]:
        if isinstance(tool_context, dict):
            vision = tool_context.get("documentVision")

            if isinstance(vision, dict) and vision:
                summary = tool_context.get("drawingPdfExtractSummary")

                if isinstance(summary, dict):
                    return vision, None, summary.get("legible")

                return vision, None, None

        if isinstance(intelligence, dict):
            vision = intelligence.get("documentVision")

            if isinstance(vision, dict) and vision:
                return vision, None, None

        return None, None, None

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        intelligence: dict | None = None,
        tool_context: dict | None = None,
    ) -> None:
        vision, char_count, legible = cls._resolve_vision(
            intelligence=intelligence,
            tool_context=tool_context,
        )

        if not vision:
            return

        if isinstance(tool_context, dict):
            summary = tool_context.get("drawingPdfExtractSummary")

            if isinstance(summary, dict):
                if summary.get("legible") is not None:
                    legible = bool(summary.get("legible"))

                if char_count is None:
                    char_count = int(summary.get("charCount") or 0) or None

        context = "drawing"

        if isinstance(tool_context, dict) and tool_context.get("drawingAnalysisMode"):
            context = "drawing"
        elif isinstance(tool_context, dict):
            context = "attachment"

        metadata["documentVisionMetrics"] = cls.build_snapshot(
            vision,
            char_count=char_count,
            legible=legible,
            context=context,
        )

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        intelligence: dict | None = None,
        tool_context: dict | None = None,
    ) -> dict:
        vision, char_count, legible = cls._resolve_vision(
            intelligence=intelligence,
            tool_context=tool_context,
        )

        if not vision:
            return audit_metadata

        audit_metadata["documentVision"] = cls.build_snapshot(
            vision,
            char_count=char_count,
            legible=legible,
            context="drawing" if (tool_context or {}).get("drawingAnalysisMode") else "attachment",
        )

        return audit_metadata

    @classmethod
    def aggregate_snapshots(
        cls,
        entries: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        by_engine: Counter[str] = Counter()
        by_context: Counter[str] = Counter()
        by_stage: Counter[str] = Counter()
        legible_count = 0
        total_duration = 0
        duration_samples = 0

        for entry in entries:
            snapshot = entry.get("snapshot") if isinstance(entry.get("snapshot"), dict) else entry

            if not isinstance(snapshot, dict):
                continue

            engine = str(snapshot.get("engine") or "unknown")
            by_engine[engine] += 1
            by_context[str(snapshot.get("context") or "unknown")] += 1

            stage_usage = snapshot.get("stageUsage")

            if isinstance(stage_usage, dict):
                for stage_name, count in stage_usage.items():
                    if count:
                        by_stage[str(stage_name)] += int(count)
            else:
                for stage_name in cls.stage_usage_from_stages(snapshot.get("stages")):
                    by_stage[stage_name] += 1

            if snapshot.get("legible") is True:
                legible_count += 1

            duration = snapshot.get("durationMs")

            if isinstance(duration, (int, float)) and duration >= 0:
                total_duration += int(duration)
                duration_samples += 1

        recent = []

        for entry in entries[:12]:
            if not isinstance(entry, dict):
                continue

            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "action": entry.get("action"),
                    "engine": snapshot.get("engine"),
                    "context": snapshot.get("context"),
                    "legible": snapshot.get("legible"),
                    "durationMs": snapshot.get("durationMs"),
                }
            )

        runs = sum(by_engine.values())

        return {
            "windowHours": hours,
            "since": since_iso,
            "runsCount": runs,
            "byEngine": dict(by_engine),
            "byContext": dict(by_context),
            "byStage": dict(by_stage),
            "legibleCount": legible_count,
            "legibilityRate": round(legible_count / runs, 3) if runs else None,
            "avgDurationMs": round(total_duration / duration_samples) if duration_samples else None,
            "recent": recent,
        }

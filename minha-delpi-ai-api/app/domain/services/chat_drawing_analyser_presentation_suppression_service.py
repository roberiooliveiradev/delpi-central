"""Suprime apresentação rica do /analyser quando o turno entrega relatório DELPI."""

from __future__ import annotations

from typing import Any


class ChatDrawingAnalyserPresentationSuppressionService:
    _ANALYSER_PATH_MARKER = "/analyser"

    _CLIENT_PRESENTATION_KEYS = (
        "presentation",
        "tablePresentation",
        "tablePresentations",
        "textPresentation",
        "treePresentation",
        "chartPresentation",
        "kpiPresentation",
        "dashboardPresentation",
        "inspectionTablePresentation",
        "profileTablePresentation",
        "humanizedSummary",
        "templateProseArchive",
        "stackPresentationPlan",
        "presentationDecision",
        "dataCoverageNotice",
        "pagination",
        "renderPlan",
        "dataCommentary",
        "dataAnswer",
    )

    @classmethod
    def should_apply(cls, tool_context: dict | None) -> bool:
        if not isinstance(tool_context, dict):
            return False

        export = tool_context.get("drawingAnalysisExport")

        if not isinstance(export, dict):
            return False

        return bool(str(export.get("markdown") or "").strip())

    @classmethod
    def strip_analyser_metadata(cls, metadata: dict | None) -> dict:
        cleaned = dict(metadata or {})

        for key in cls._CLIENT_PRESENTATION_KEYS:
            cleaned.pop(key, None)

        cleaned["suppressClientPresentation"] = True

        return cleaned

    @classmethod
    def apply(cls, tool_context: dict | None) -> dict[str, Any]:
        if not cls.should_apply(tool_context):
            return tool_context or {}

        updated = dict(tool_context)
        tool_calls = updated.get("toolCalls")

        if not isinstance(tool_calls, list):
            return updated

        stripped_calls: list[dict] = []

        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                stripped_calls.append(tool_call)
                continue

            item = dict(tool_call)
            metadata = dict(item.get("metadata") or {})
            path = str(metadata.get("path") or "").lower()

            if cls._ANALYSER_PATH_MARKER not in path:
                stripped_calls.append(item)
                continue

            item["metadata"] = cls.strip_analyser_metadata(metadata)
            stripped_calls.append(item)

        updated["toolCalls"] = stripped_calls

        return updated

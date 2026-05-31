"""Chips de follow-up após análise de desenho — Onda 12.4/12.5."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatDrawingFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        intelligence: dict | None = None,
        tool_context: dict | None = None,
    ) -> None:
        drawing = None

        if isinstance(intelligence, dict):
            drawing = intelligence.get("drawingAnalysis")

        if not isinstance(drawing, dict) and isinstance(tool_context, dict):
            drawing = tool_context.get("drawingAnalysis")

        if not isinstance(drawing, dict):
            return

        suggestions = cls.build_suggestions(drawing)

        if suggestions:
            metadata["drawingFollowUpSuggestions"] = suggestions

        export = tool_context.get("drawingAnalysisExport") if isinstance(tool_context, dict) else None

        if isinstance(export, dict) and export.get("markdown"):
            metadata["drawingAnalysisExport"] = export

    @classmethod
    def build_suggestions(cls, drawing: dict) -> list[dict[str, str]]:
        labels = list(
            _playbook().get("drawingFollowUpChips")
            or [
                "Ver só erros críticos",
                "Ver checklist completo",
                "Validar BOM",
                "Gerar relatório",
                "Reanalisar desenho",
            ]
        )
        queries = _playbook().get("drawingFollowUpQueries") or {}
        critical = int(drawing.get("criticalErrors") or 0)

        if critical <= 0 and "Ver só erros críticos" in labels:
            labels = [label for label in labels if label != "Ver só erros críticos"]

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or label).strip()
            code = str(drawing.get("productCode") or "").strip()

            if code and "{{productCode}}" in template:
                template = template.replace("{{productCode}}", code)

            suggestions.append({"label": str(label), "query": template})

        return suggestions

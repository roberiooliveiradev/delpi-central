"""Compila Spec.delivery / constraints → metadata canvasOpen (sem canvasPresentation)."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.chat_rich_presentation_canvas_export_service import (
    ChatRichPresentationCanvasExportService,
)


class PresentationDeliveryCompilerService:
    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec | None = None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        prefer_canvas = cls._should_prefer_canvas(metadata, spec=spec)
        if not prefer_canvas:
            return

        markdown = cls._build_markdown(metadata)
        if not markdown:
            return

        title = cls._derive_title(metadata)
        metadata["deliveryPreferCanvas"] = True
        metadata["canvasOpen"] = {
            "title": title,
            "markdown": markdown,
            "sourceMessageId": metadata.get("sourceMessageId"),
        }

    @classmethod
    def _should_prefer_canvas(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec | None,
    ) -> bool:
        if spec is not None and spec.delivery is not None and spec.delivery.prefer_canvas:
            return True

        constraints = metadata.get("presentationConstraints")
        if isinstance(constraints, dict) and constraints.get("preferCanvas"):
            return True

        return False

    @classmethod
    def _build_markdown(cls, metadata: dict[str, Any]) -> str:
        sections = ChatRichPresentationCanvasExportService.sections_from_tool_metadata(
            metadata,
        )
        if sections:
            return ChatRichPresentationCanvasExportService._merge_sections(sections).strip()

        content = str(
            metadata.get("assistantAnswer")
            or metadata.get("answer")
            or metadata.get("summaryMarkdown")
            or "",
        ).strip()
        return ChatRichPresentationCanvasExportService.build_markdown_from_assistant(
            content,
            metadata,
        ).strip()

    @classmethod
    def _derive_title(cls, metadata: dict[str, Any]) -> str:
        for key in (
            "tablePresentation",
            "chartPresentation",
            "kpiPresentation",
            "dashboardPresentation",
            "treePresentation",
            "presentation",
        ):
            presentation = metadata.get(key)
            if isinstance(presentation, dict):
                title = str(presentation.get("title") or "").strip()
                if title:
                    return title[:120]

        decision = metadata.get("presentationDecision")
        if isinstance(decision, dict):
            selected = str(decision.get("selected") or "").strip()
            if selected:
                return selected.replace("_", " ").title()[:120]

        return "Conteúdo do chat"

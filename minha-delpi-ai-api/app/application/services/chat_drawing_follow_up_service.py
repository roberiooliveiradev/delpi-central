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
        latency_ms: int | None = None,
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

        if isinstance(tool_context, dict):
            from app.domain.services.chat_drawing_validation_package_service import (
                ChatDrawingValidationPackageService,
            )

            package = tool_context.get(ChatDrawingValidationPackageService.PACKAGE_KEY)

            if isinstance(package, dict):
                ChatDrawingValidationPackageService.attach_to_metadata(metadata, package)

        if isinstance(tool_context, dict) and tool_context.get("drawingAnalysisMode"):
            metadata["drawingAnalysisMode"] = True

        if isinstance(drawing, dict):
            metadata["drawingAnalysis"] = drawing

        overrides = None

        if isinstance(tool_context, dict) and isinstance(
            tool_context.get("drawingAnalysisOverrides"),
            list,
        ):
            overrides = tool_context.get("drawingAnalysisOverrides")

        if overrides is None and isinstance(drawing, dict) and isinstance(
            drawing.get("drawingAnalysisOverrides"),
            list,
        ):
            overrides = drawing.get("drawingAnalysisOverrides")

        if isinstance(overrides, list) and overrides:
            metadata["drawingAnalysisOverrides"] = overrides

        from app.application.services.chat_drawing_metrics_service import (
            ChatDrawingMetricsService,
        )

        ChatDrawingMetricsService.attach_to_assistant_metadata(
            metadata,
            intelligence=intelligence,
            tool_context=tool_context,
            latency_ms=latency_ms,
        )

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
        critical, warnings, errors = cls._status_counts(drawing)

        if critical <= 0 and "Ver só erros críticos" in labels:
            labels = [label for label in labels if label != "Ver só erros críticos"]

        # Chip de revisão manual: oferece enquanto houver pendente/erro ajustável.
        # Críticos permanecem (override não os remove); não esconder o atalho por causa deles.
        if warnings <= 0 and errors <= 0:
            labels = [
                label
                for label in labels
                if label not in {"Confirmar revisão manual", "Descartar ressalva"}
            ]

        if warnings > 0 or errors > 0:
            manual_review = ("Confirmar revisão manual", "Descartar ressalva")
            front = [label for label in manual_review if label in labels]
            rest = [label for label in labels if label not in manual_review]
            labels = front + rest

        if not cls._should_offer_bom_reextract(drawing) and "Reextrair BOM do PDF" in labels:
            labels = [label for label in labels if label != "Reextrair BOM do PDF"]
        elif "Reextrair BOM do PDF" in labels:
            labels = [label for label in labels if label != "Reextrair BOM do PDF"]
            # Após chips de revisão manual (se houver); senão após «Ver só erros críticos».
            insert_at = 0
            for index, label in enumerate(labels):
                if label in {"Confirmar revisão manual", "Descartar ressalva", "Ver só erros críticos"}:
                    insert_at = index + 1
            labels.insert(min(insert_at, len(labels)), "Reextrair BOM do PDF")

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or label).strip()
            code = str(drawing.get("productCode") or "").strip()

            if code and "{{productCode}}" in template:
                template = template.replace("{{productCode}}", code)

            suggestions.append({"label": str(label), "query": template})

        return suggestions

    @classmethod
    def _status_counts(cls, drawing: dict) -> tuple[int, int, int]:
        """Contagens a partir dos itens (fonte de verdade) com fallback nos totais."""
        items = drawing.get("items") if isinstance(drawing.get("items"), list) else []

        if items:
            critical = sum(
                1
                for item in items
                if isinstance(item, dict) and str(item.get("status") or "") == "critical_error"
            )
            errors = sum(
                1
                for item in items
                if isinstance(item, dict) and str(item.get("status") or "") == "error"
            )
            warnings = sum(
                1
                for item in items
                if isinstance(item, dict) and str(item.get("status") or "") == "pending"
            )
            return critical, warnings, errors

        return (
            int(drawing.get("criticalErrors") or 0),
            int(drawing.get("warnings") or 0),
            int(drawing.get("errors") or 0),
        )

    @classmethod
    def _should_offer_bom_reextract(cls, drawing: dict) -> bool:
        vision = drawing.get("visionRefinement")

        if not isinstance(vision, dict) or not vision.get("attempted"):
            return False

        bom_issue_keys = {
            "bom_extra",
            "bom_missing",
            "bom_quantity_mismatch",
            "bom_quantity_pending",
        }
        items = drawing.get("items") if isinstance(drawing.get("items"), list) else []

        for item in items:
            if not isinstance(item, dict):
                continue

            template_key = str(item.get("templateKey") or "").strip()

            if template_key not in bom_issue_keys:
                continue

            if str(item.get("status") or "").strip() in {
                "critical_error",
                "error",
                "pending",
            }:
                return True

        return int(drawing.get("criticalErrors") or 0) > 0

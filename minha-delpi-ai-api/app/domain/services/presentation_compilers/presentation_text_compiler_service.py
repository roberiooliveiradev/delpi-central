"""Compila spec.text.sectionPlan → framing metadata (sem reescrever markdown)."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_spec import PresentationSpec

_SECTION_TO_NARRATIVE: dict[str, str] = {
    "summary": "lead",
    "highlights": "highlights",
    "attention": "attention",
    "narrative": "lead",
    "details": "operationalTables",
    "next_steps": "attention",
}

_SECTION_VISIBILITY: dict[str, str] = {
    "summary": "scope",
    "highlights": "highlights",
    "attention": "attention",
    "narrative": "scope",
    "details": "guide",
    "next_steps": "attention",
}


class PresentationTextCompilerService:
    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
    ) -> None:
        if spec.text is None:
            return

        section_plan = list(spec.text.section_plan)
        if not section_plan and not spec.text.prose_density:
            return

        stack_plan = metadata.get("stackPresentationPlan")
        if not isinstance(stack_plan, dict):
            stack_plan = {}
            metadata["stackPresentationPlan"] = stack_plan

        if section_plan:
            narrative_order: list[str] = []
            for marker in section_plan:
                slot = _SECTION_TO_NARRATIVE.get(marker)
                if slot and slot not in narrative_order:
                    narrative_order.append(slot)
            if narrative_order:
                stack_plan["narrativeOrder"] = narrative_order

            visibility = dict(stack_plan.get("sectionVisibility") or {})
            for marker in section_plan:
                section_id = _SECTION_VISIBILITY.get(marker)
                if section_id:
                    visibility[section_id] = True
            if visibility:
                stack_plan["sectionVisibility"] = visibility
            stack_plan["sectionPlan"] = section_plan

        if spec.text.prose_density:
            stack_plan["proseDensity"] = spec.text.prose_density

        decision = metadata.setdefault("presentationDecision", {})
        if isinstance(decision, dict):
            framing = dict(decision.get("textFraming") or {})
            if section_plan:
                framing["sectionPlan"] = section_plan
            if spec.text.prose_density:
                framing["proseDensity"] = spec.text.prose_density
            framing["bindingProvenance"] = "COMPILED"
            decision["textFraming"] = framing

        text_presentation = metadata.get("textPresentation")
        if isinstance(text_presentation, dict):
            original_markdown = text_presentation.get("markdown")
            config = dict(text_presentation.get("config") or {})
            if section_plan:
                config["sectionPlan"] = section_plan
            if spec.text.prose_density:
                config["proseDensity"] = spec.text.prose_density
            config["bindingProvenance"] = "COMPILED"
            text_presentation["config"] = config
            if original_markdown is not None:
                text_presentation["markdown"] = original_markdown

"""Ordem canônica de narrativa + tabelas + visuais no layout stack (qualquer rota)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_section_availability_service import (
    ChatPresentationSectionAvailabilityService,
)


class ChatPresentationStackOrderService:
    """Plano consumido pelo MFE (`stackPresentationPlan`) para intercalar segmentos."""

    _DEFAULT_TABLE_ROLES = (
        "profile",
        "guide",
        "inspection",
        "stock",
        "pricing",
        "structure",
        "list",
        "other",
    )

    @classmethod
    def resolve_plan(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        path = str(metadata.get("path") or "")
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        stack_config = ChatPresentationProfileService.stack_plan_config(path, entity)
        has_attention = cls._markdown_has_attention(metadata)
        has_highlights = cls._markdown_has_highlights(metadata)
        table_roles = list(stack_config.get("tableRoleOrder") or cls._DEFAULT_TABLE_ROLES)
        profile_first = bool(stack_config.get("profileFirst", True))
        highlights_after_profile = bool(
            stack_config.get("highlightsAfterProfile", has_highlights)
        )

        if ChatPresentationProfileService.has_flag(path, "analyser", entity=entity):
            highlights_after_profile = True

        tail_visuals = cls._resolve_tail_visual_order(metadata)

        plan = {
            "profileFirst": profile_first,
            "highlightsAfterProfile": highlights_after_profile,
            "attentionLast": has_attention,
            "tableRoleOrder": table_roles,
            "tailVisualOrder": tail_visuals,
            "narrativeOrder": cls._narrative_order(
                profile_first=profile_first,
                highlights_after_profile=highlights_after_profile,
                attention_last=has_attention,
            ),
            "presentationProfileKey": ChatPresentationProfileService.resolve_profile_key(
                path,
                entity,
            ),
        }

        from app.domain.services.chat_presentation_stack_markdown_service import (
            ChatPresentationStackMarkdownService,
        )

        plan = ChatPresentationSectionAvailabilityService.enrich_stack_plan(metadata, plan)
        return ChatPresentationStackMarkdownService.enrich_stack_plan(metadata, plan)

    @classmethod
    def enrich_metadata(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        metadata["stackPresentationPlan"] = cls.resolve_plan(metadata)

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            decision["stackPresentationPlan"] = metadata["stackPresentationPlan"]

    @classmethod
    def _narrative_order(
        cls,
        *,
        profile_first: bool,
        highlights_after_profile: bool,
        attention_last: bool,
    ) -> list[str]:
        order = ["lead"]

        if profile_first:
            order.append("profileTables")

        if highlights_after_profile:
            order.append("highlights")

        order.append("operationalTables")

        order.append("tailVisuals")

        if attention_last:
            order.append("attention")

        return order

    @classmethod
    def _resolve_tail_visual_order(cls, metadata: dict[str, Any]) -> list[str]:
        from app.domain.services.chat_presentation_rich_stack_policy_service import (
            ChatPresentationRichStackPolicyService,
        )

        path = str(metadata.get("path") or "")
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        profile_order = ChatPresentationRichStackPolicyService.resolve_tail_visual_order(
            metadata,
            path=path,
            entity=entity,
        )

        if profile_order:
            return profile_order

        decision = metadata.get("presentationDecision")
        raw = []

        if isinstance(decision, dict):
            raw = list(decision.get("visualOrder") or [])

        preferred = ["kpi", "tree", "chart", "dashboard"]
        normalized = {str(item).strip().lower() for item in raw}
        ordered = [kind for kind in preferred if kind in normalized]

        for item in sorted(normalized):
            if item in {"text", "table"}:
                continue

            if item not in ordered and not item.endswith("chart"):
                ordered.append(item)

        for chart_token in (
            "line_chart",
            "bar_chart",
            "horizontal_bar",
            "donut",
            "grouped_bar",
            "stacked_bar",
        ):
            if chart_token in normalized and "chart" not in ordered:
                ordered.insert(1 if "tree" in ordered else 0, "chart")
                break

        return ordered or ["kpi", "tree", "chart"]

    @classmethod
    def _markdown_has_highlights(cls, metadata: dict[str, Any]) -> bool:
        markdown = cls._text_markdown(metadata)
        header = cls._humanized_narrative_text("highlightsHeader")

        return bool(markdown and header and header in markdown)

    @classmethod
    def _markdown_has_attention(cls, metadata: dict[str, Any]) -> bool:
        markdown = cls._text_markdown(metadata)
        prefix = cls._humanized_narrative_text("attentionHeaderPrefix") or cls._humanized_narrative_text(
            "attentionHeader"
        )

        return bool(markdown and prefix and prefix in markdown)

    @classmethod
    def _humanized_narrative_text(cls, key: str) -> str:
        return str(
            ChatAssistantContentService.get(
                "presenter_content",
                "humanizedNarrative",
                key,
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def _text_markdown(cls, metadata: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return ""

        return str(text_presentation.get("markdown") or "").strip()

"""Ordem canônica de narrativa + tabelas + visuais no layout stack (qualquer rota)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
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

    _ANALYSER_TABLE_ROLES = ("profile", "guide", "inspection", "other")

    _STOCK_TABLE_ROLES = ("profile", "stock", "other")

    _TREE_ROUTE_TABLE_ROLES = ("profile", "structure", "list", "other")

    _TABLE_ROUTE_ROLES = ("profile", "guide", "inspection", "list", "other")

    @classmethod
    def resolve_plan(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        path = str(metadata.get("path") or "")
        lowered = ChatPresentationRoutePolicyService.path_lowered(path)
        has_attention = cls._markdown_has_attention(metadata)
        has_highlights = cls._markdown_has_highlights(metadata)

        if ChatPresentationRoutePolicyService.is_analyser_route(lowered):
            table_roles = list(cls._ANALYSER_TABLE_ROLES)
            profile_first = True
            highlights_after_profile = True
        elif ChatPresentationRoutePolicyService.is_stock_route(lowered):
            table_roles = list(cls._STOCK_TABLE_ROLES)
            profile_first = True
            highlights_after_profile = has_highlights
        elif ChatPresentationRoutePolicyService.is_tree_route(lowered):
            table_roles = list(cls._TREE_ROUTE_TABLE_ROLES)
            profile_first = True
            highlights_after_profile = has_highlights
        elif ChatPresentationRoutePolicyService.is_table_route(lowered):
            table_roles = list(cls._TABLE_ROUTE_ROLES)
            profile_first = True
            highlights_after_profile = has_highlights
        else:
            table_roles = list(cls._DEFAULT_TABLE_ROLES)
            profile_first = True
            highlights_after_profile = has_highlights

        tail_visuals = cls._resolve_tail_visual_order(metadata)

        return {
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
        }

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
        decision = metadata.get("presentationDecision")
        raw = []

        if isinstance(decision, dict):
            raw = list(decision.get("visualOrder") or [])

        preferred = ["tree", "chart", "kpi", "dashboard"]
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

        return ordered or ["tree", "chart"]

    @classmethod
    def _markdown_has_highlights(cls, metadata: dict[str, Any]) -> bool:
        markdown = cls._text_markdown(metadata)

        return bool(markdown and "**Destaques**" in markdown)

    @classmethod
    def _markdown_has_attention(cls, metadata: dict[str, Any]) -> bool:
        markdown = cls._text_markdown(metadata)

        return bool(markdown and "**Pontos de atenção" in markdown)

    @classmethod
    def _text_markdown(cls, metadata: dict[str, Any]) -> str:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return ""

        return str(text_presentation.get("markdown") or "").strip()

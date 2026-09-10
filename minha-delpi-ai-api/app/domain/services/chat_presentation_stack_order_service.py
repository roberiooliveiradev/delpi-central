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
        plan = ChatPresentationStackMarkdownService.enrich_stack_plan(metadata, plan)
        cls._materialize_display_titles(metadata, plan)
        return plan

    _STABLE_TITLE_SOURCES = frozenset(
        {
            "SLOT_TITLE",
            "PRESENTATION_TITLE",
            "ACTION_DISPLAY_LABEL",
        }
    )

    @classmethod
    def _materialize_display_titles(
        cls,
        metadata: dict[str, Any],
        plan: dict[str, Any],
    ) -> None:
        """Materializa títulos/framing da resposta atual (não o catálogo inteiro)."""
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )
        from app.domain.services.result_presentation_title_resolver import (
            ResultPresentationTitleResolver,
        )

        route_key = cls._current_route_key(metadata, plan)
        catalog_titles = ChatProductOperationalContentService.get_mapping(
            "presentation",
            "routeTitles",
        )
        catalog_framing = ChatProductOperationalContentService.get_mapping(
            "presentation",
            "routeFraming",
        )
        catalog_section_titles = ChatProductOperationalContentService.get_mapping(
            "presentation",
            "sectionTitles",
        )
        if not catalog_section_titles:
            catalog_section_titles = {
                "scope": "Escopo da consulta",
                "profile": "Ficha cadastral",
                "highlights": "Síntese executiva (Destaques)",
                "guide": "Roteiro de produção",
                "inspection": "Plano de inspeção",
                "structure": "Estrutura (BOM)",
                "attention": "Alertas e divergências",
            }

        path = str(metadata.get("path") or "")
        # E7.S6 — write-once: título materializado estável não é reinferido no rematerialize (F5).
        prior_source = str(
            plan.get("titleSource") or metadata.get("titleSource") or ""
        ).strip()
        prior_title = str(
            plan.get("resolvedRouteTitle")
            or metadata.get("routeTitle")
            or metadata.get("title")
            or ""
        ).strip()
        if not prior_title:
            presentation = metadata.get("presentation")
            if isinstance(presentation, dict):
                prior_title = str(presentation.get("title") or "").strip()

        if prior_title and prior_source in cls._STABLE_TITLE_SOURCES:
            route_title = prior_title
            title_source = prior_source
        else:
            resolved = ResultPresentationTitleResolver.resolve(
                path=path,
                summary=str(
                    metadata.get("summary") or metadata.get("actionSummary") or ""
                ),
                action_id=str(metadata.get("actionId") or ""),
                metadata=metadata,
                fallback="",
            )
            route_title = (
                resolved.title
                or str((catalog_titles or {}).get(route_key) or "").strip()
                or str((catalog_titles or {}).get("other") or "").strip()
            )
            title_source = (
                resolved.source if resolved.title else "ROUTE_CATALOG"
            )

        if route_title:
            metadata["routeTitle"] = route_title
            metadata["title"] = metadata.get("title") or route_title
            metadata["titleSource"] = title_source
            plan["resolvedRouteTitle"] = route_title
            plan["titleSource"] = title_source
            plan["routeTitles"] = {route_key: route_title}

        framing = str((catalog_framing or {}).get(route_key) or "").strip() or str(
            (catalog_framing or {}).get("other") or ""
        ).strip()
        if framing:
            plan["routeFraming"] = {route_key: framing}
            metadata["routeFraming"] = framing

        active_sections = cls._active_section_ids(plan)
        section_titles = {
            section_id: str(catalog_section_titles.get(section_id) or "").strip()
            for section_id in active_sections
            if str(catalog_section_titles.get(section_id) or "").strip()
        }
        if section_titles:
            plan["sectionTitles"] = section_titles

        existing_framing = plan.get("sectionFraming")
        if isinstance(existing_framing, dict) and existing_framing:
            plan["sectionFraming"] = {
                key: value
                for key, value in existing_framing.items()
                if key in active_sections or not active_sections
            }
        else:
            catalog_section_framing = ChatProductOperationalContentService.get_mapping(
                "presentation",
                "sectionFraming",
            )
            if catalog_section_framing:
                plan["sectionFraming"] = {
                    key: value
                    for key, value in catalog_section_framing.items()
                    if key in active_sections or not active_sections
                }

    @classmethod
    def _current_route_key(cls, metadata: dict[str, Any], plan: dict[str, Any]) -> str:
        for candidate in (
            plan.get("presentationProfileKey"),
            plan.get("presentationProfile"),
            metadata.get("routeKey"),
            metadata.get("presentationProfileKey"),
        ):
            token = str(candidate or "").strip()
            if token:
                # profile keys like product_stock → stock
                if "_" in token:
                    tail = token.rsplit("_", 1)[-1]
                    if tail in {
                        "stock",
                        "structure",
                        "guide",
                        "inspection",
                        "profile",
                        "analyser",
                        "parents",
                    }:
                        return tail
                return token
        path = str(metadata.get("path") or "").lower()
        for marker in (
            "stock",
            "structure",
            "guide",
            "inspection",
            "analyser",
            "parents",
        ):
            if f"/{marker}" in path:
                return marker
        return "other"

    @classmethod
    def _active_section_ids(cls, plan: dict[str, Any]) -> set[str]:
        active: set[str] = set()
        for key in ("narrativeOrder", "tableRoleOrder", "tailVisualOrder"):
            values = plan.get(key)
            if isinstance(values, list):
                for item in values:
                    token = str(item or "").strip()
                    if token in {
                        "scope",
                        "profile",
                        "highlights",
                        "guide",
                        "inspection",
                        "structure",
                        "attention",
                    }:
                        active.add(token)
                    if token == "profileTables":
                        active.add("profile")
                    if token == "highlights":
                        active.add("highlights")
                    if token == "attention":
                        active.add("attention")
        availability = plan.get("sectionAvailability")
        if isinstance(availability, dict):
            for key, enabled in availability.items():
                if enabled and str(key) in {
                    "scope",
                    "profile",
                    "highlights",
                    "guide",
                    "inspection",
                    "structure",
                    "attention",
                }:
                    active.add(str(key))
        # Always allow scope framing when humanized stack is present
        if plan.get("humanizedStack") or plan.get("sectionFraming"):
            active.add("scope")
        return active

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

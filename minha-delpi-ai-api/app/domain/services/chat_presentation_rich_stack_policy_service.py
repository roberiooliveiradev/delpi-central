"""Política canônica de stack rico — texto + KPI/árvore/gráfico/painel por rota operacional."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_rich_presentation_text_service import (
    ChatRichPresentationTextService,
)

_VISUAL_SLOTS: dict[str, str] = {
    "tree": "treePresentation",
    "chart": "chartPresentation",
    "kpi": "kpiPresentation",
    "dashboard": "dashboardPresentation",
    "table": "tablePresentation",
}

_RICH_PROFILE_FLAGS = (
    "analyser",
    "factory_status",
    "structure_exclusivity",
    "raw_material_price_intelligence",
    "cost_impact_simulation",
    "sale_pricing",
    "production_status",
    "shipping_status",
    "stock",
    "tree",
)


class ChatPresentationRichStackPolicyService:
    @classmethod
    def is_rich_playbook_route(cls, path: str | None, *, entity: str | None = None) -> bool:
        profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)

        if profile_key in {
            "analyser",
            "factory_status",
            "structure_exclusivity",
            "raw_material_price_intelligence",
            "cost_impact_simulation",
            "sale_pricing",
            "production_status",
            "shipping_status",
            "stock",
            "tree_hierarchy",
        }:
            return True

        return any(
            ChatPresentationProfileService.has_flag(path, flag, entity=entity)
            for flag in _RICH_PROFILE_FLAGS
        )

    @classmethod
    def has_rich_text_narrative(cls, metadata: dict[str, Any]) -> bool:
        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return False

        return bool(str(text_presentation.get("markdown") or "").strip())

    @classmethod
    def count_auxiliary_visuals(cls, metadata: dict[str, Any]) -> int:
        count = 0
        primary = metadata.get("presentation")

        for slot_key in _VISUAL_SLOTS.values():
            presentation = metadata.get(slot_key)

            if isinstance(presentation, dict) and presentation.get("type"):
                count += 1

        if isinstance(primary, dict):
            primary_type = str(primary.get("type") or "").strip().lower()

            if primary_type in {"tree", "chart", "kpi", "dashboard", "table"}:
                if primary_type == "table":
                    from app.domain.services.chat_presentation_structure_dedup_service import (
                        ChatPresentationStructureDedupService,
                    )

                    if not ChatPresentationStructureDedupService.is_hierarchy_duplicate_table(primary):
                        count += 1
                else:
                    count += 1

        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            from app.domain.services.chat_presentation_structure_dedup_service import (
                ChatPresentationStructureDedupService,
            )

            for item in bundled:
                if not isinstance(item, dict) or item.get("type") != "table":
                    continue

                if ChatPresentationStructureDedupService.is_hierarchy_duplicate_table(item):
                    continue

                count += 1
                break

        return count

    @classmethod
    def should_default_to_text_stack(
        cls,
        *,
        path: str | None,
        metadata: dict[str, Any],
        entity: str | None = None,
        user_preference: str | None = None,
    ) -> bool:
        if user_preference:
            return False

        from app.domain.services.chat_presentation_route_policy_service import (
            ChatPresentationRoutePolicyService,
        )

        # Estoque: tabela nativa por defaultViewPolicy; stack narrativo só com mensagem do usuário.
        if ChatPresentationRoutePolicyService.is_stock_route(path):
            return False

        if not cls.is_rich_playbook_route(path, entity=entity):
            return False

        if not cls.has_rich_text_narrative(metadata):
            return False

        return cls.count_auxiliary_visuals(metadata) >= 1

    @classmethod
    def resolve_available_views(
        cls,
        metadata: dict[str, Any],
        *,
        path: str | None,
        entity: str | None = None,
        available_formats: list[str] | None = None,
    ) -> list[str]:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        profile_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]
        present: list[str] = []

        if cls.has_rich_text_narrative(metadata):
            present.append("text")

        primary = metadata.get("presentation")

        if isinstance(primary, dict):
            primary_type = str(primary.get("type") or "").strip().lower()

            if primary_type == "table":
                from app.domain.services.chat_presentation_structure_dedup_service import (
                    ChatPresentationStructureDedupService,
                )

                if not ChatPresentationStructureDedupService.is_hierarchy_duplicate_table(primary):
                    present.append("table")
            elif primary_type in _VISUAL_SLOTS:
                present.append(primary_type)

        for view, slot_key in _VISUAL_SLOTS.items():
            presentation = metadata.get(slot_key)

            if isinstance(presentation, dict) and presentation.get("type"):
                if view not in present:
                    present.append(view)

        if isinstance(metadata.get("tablePresentations"), list):
            from app.domain.services.chat_presentation_structure_dedup_service import (
                ChatPresentationStructureDedupService,
            )

            has_aux_table = any(
                isinstance(item, dict)
                and item.get("type") == "table"
                and not ChatPresentationStructureDedupService.is_hierarchy_duplicate_table(item)
                for item in metadata["tablePresentations"]
            )

            if has_aux_table and "table" not in present:
                present.append("table")

        ordered = [view for view in profile_order if view in present]

        for view in present:
            if view not in ordered:
                ordered.append(view)

        if available_formats:
            allowed = {str(token).strip().lower() for token in available_formats if str(token).strip()}

            if allowed:
                ordered = [view for view in ordered if view in allowed]

        return list(dict.fromkeys(ordered))

    @classmethod
    def resolve_tail_visual_order(
        cls,
        metadata: dict[str, Any],
        *,
        path: str | None,
        entity: str | None = None,
    ) -> list[str]:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        profile_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]
        tail_candidates = ("kpi", "tree", "chart", "dashboard")
        present = set(cls.resolve_available_views(metadata, path=path, entity=entity))
        ordered = [view for view in profile_order if view in tail_candidates and view in present]

        for view in tail_candidates:
            if view in present and view not in ordered:
                ordered.append(view)

        return ordered

    @classmethod
    def stack_reason_for_route(cls, path: str | None, *, entity: str | None = None) -> str:
        from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

        profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)
        reasons = ChatAssistantContentService.get_node(
            "presenter_content",
            "richStackReasons",
        )

        if isinstance(reasons, dict):
            reason = reasons.get(profile_key)

            if isinstance(reason, str) and reason.strip():
                return reason.strip()

        return ChatAssistantContentService.get(
            "presenter_content",
            "richStackReasons",
            "default",
            default="consulta operacional — narrativa com painéis complementares (stack)",
        )

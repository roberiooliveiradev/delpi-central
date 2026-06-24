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


class ChatPresentationRichStackPolicyService:
    @classmethod
    def is_rich_playbook_route(cls, path: str | None, *, entity: str | None = None) -> bool:
        profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)

        return ChatPresentationProfileService.is_rich_stack_profile(profile_key)

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
    def count_narrative_stack_visuals(cls, metadata: dict[str, Any]) -> int:
        count = 0

        for slot_key in (
            "treePresentation",
            "kpiPresentation",
            "chartPresentation",
            "dashboardPresentation",
        ):
            presentation = metadata.get(slot_key)

            if isinstance(presentation, dict) and presentation.get("type"):
                count += 1

        primary = metadata.get("presentation")

        if isinstance(primary, dict):
            primary_type = str(primary.get("type") or "").strip().lower()

            if primary_type in {"tree", "chart", "kpi", "dashboard"}:
                count += 1

        return count

    @classmethod
    def should_default_to_text_stack(
        cls,
        *,
        path: str | None,
        metadata: dict[str, Any],
        entity: str | None = None,
        user_preference: str | None = None,
        user_message: str | None = None,
    ) -> bool:
        if user_preference:
            return False

        from app.domain.services.chat_presentation_route_policy_service import (
            ChatPresentationRoutePolicyService,
        )
        from app.domain.services.chat_presentation_text_first_policy_service import (
            ChatPresentationTextFirstPolicyService,
        )

        # Estoque: tabela nativa por defaultViewPolicy; stack narrativo só com mensagem do usuário.
        if ChatPresentationRoutePolicyService.is_stock_route(path):
            return False

        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        stack_policy = str(profile.get("stackLayoutPolicy") or "on_demand").strip().lower()

        if stack_policy != "always":
            if not ChatPresentationTextFirstPolicyService.looks_like_integrated_stack_request(
                user_message,
            ):
                return False

        if not cls.has_rich_text_narrative(metadata):
            return False

        if cls.count_narrative_stack_visuals(metadata) >= 1:
            return True

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

        if cls._should_use_dashboard_only_tail(metadata, profile):
            return ["dashboard"]

        if cls._should_omit_dashboard_for_table_primary(metadata, profile):
            ordered = [view for view in ordered if view != "dashboard"]

        return ordered

    @classmethod
    def _should_omit_dashboard_for_table_primary(
        cls,
        metadata: dict[str, Any],
        profile: dict[str, Any],
    ) -> bool:
        tail_policy = str(profile.get("stackTailPolicy") or "").strip().lower()

        if tail_policy != "table_primary":
            return False

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if explicit == "dashboard":
            return False

        return cls.metadata_has_operational_table(metadata)

    @classmethod
    def metadata_has_operational_table(cls, metadata: dict[str, Any]) -> bool:
        bulk = metadata.get("tablePresentations")

        if isinstance(bulk, list):
            for item in bulk:
                if isinstance(item, dict) and str(item.get("type") or "").strip().lower() == "table":
                    return True

        for key in ("tablePresentation", "profileTablePresentation", "presentation"):
            presentation = metadata.get(key)

            if (
                isinstance(presentation, dict)
                and str(presentation.get("type") or "").strip().lower() == "table"
            ):
                return True

        return False

    @classmethod
    def _metadata_has_dashboard(cls, metadata: dict[str, Any]) -> bool:
        for key in ("dashboardPresentation", "presentation"):
            presentation = metadata.get(key)

            if (
                isinstance(presentation, dict)
                and str(presentation.get("type") or "").strip().lower() == "dashboard"
            ):
                return True

        return False

    @classmethod
    def _should_use_dashboard_only_tail(
        cls,
        metadata: dict[str, Any],
        profile: dict[str, Any],
    ) -> bool:
        tail_policy = str(profile.get("stackTailPolicy") or "").strip().lower()

        if tail_policy != "dashboard_only":
            return False

        return cls._metadata_has_dashboard(metadata)

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

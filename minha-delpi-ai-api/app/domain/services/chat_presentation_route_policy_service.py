"""Política de formato nativo por rota DELPI — delegada a presentation_profiles.json."""

from __future__ import annotations

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)


class ChatPresentationRoutePolicyService:
    @classmethod
    def path_lowered(cls, path: str | None) -> str:
        return ChatPresentationProfileService.path_lowered(path)

    @classmethod
    def is_tree_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "tree")

    @classmethod
    def is_table_route(cls, path: str | None) -> bool:
        flags = ChatPresentationProfileService.flags(path)

        return "table" in flags or "analyser" in flags

    @classmethod
    def is_stock_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "stock")

    @classmethod
    def is_analyser_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "analyser")

    @classmethod
    def is_factory_status_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "factory_status")

    @classmethod
    def is_production_status_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "production_status")

    @classmethod
    def is_shipping_status_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "shipping_status")

    @classmethod
    def is_structure_exclusivity_route(cls, path: str | None) -> bool:
        return ChatPresentationProfileService.has_flag(path, "structure_exclusivity")

    @classmethod
    def resolve_default_preferred_format(
        cls,
        *,
        path: str | None,
        session_format: str | None = None,
        has_tree: bool = False,
        has_table: bool = False,
        has_chart: bool = False,
        has_text: bool = False,
        has_kpi: bool = False,
        entity: str | None = None,
    ) -> str | None:
        return ChatPresentationProfileService.resolve_default_preferred_format(
            path=path,
            session_format=session_format,
            entity=entity,
            has_tree=has_tree,
            has_table=has_table,
            has_chart=has_chart,
            has_text=has_text,
            has_kpi=has_kpi,
        )

    @classmethod
    def apply_visual_order(cls, decision: dict, *, path: str | None) -> None:
        ChatPresentationProfileService.apply_visual_order(
            decision,
            path=path,
        )

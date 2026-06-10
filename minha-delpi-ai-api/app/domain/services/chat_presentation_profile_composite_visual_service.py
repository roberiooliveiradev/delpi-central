"""Orquestração declarativa do quartet visual — Playbook 12 R6."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.domain.services.chat_presentation_composite_visual_builder import (
    ChatPresentationCompositeVisualBuilder,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationProfileCompositeVisualService:
    @classmethod
    def resolve_spec_key(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        profile_key: str | None = None,
    ) -> str:
        if profile_key:
            profile = ChatPresentationProfileService.profile(profile_key)
        else:
            profile = ChatPresentationProfileService.resolve_profile(path, entity)

        token = str(profile.get("compositeVisualSpec") or profile.get("profileKey") or "").strip()

        return token or ChatPresentationProfileService.resolve_profile_key(path, entity)

    @classmethod
    def spec(
        cls,
        path: str | None = None,
        entity: str | None = None,
        *,
        profile_key: str | None = None,
    ) -> dict[str, Any]:
        spec_key = cls.resolve_spec_key(path, entity, profile_key=profile_key)

        return ChatPresentationCompositeVisualBuilder.spec(spec_key)

    @classmethod
    def build_kpi(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        *,
        profile_key: str | None = None,
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        spec = cls.spec(path, entity, profile_key=profile_key)

        if not spec:
            return None

        return ChatPresentationCompositeVisualBuilder.build_kpi(host, root, path, spec)

    @classmethod
    def build_chart(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        *,
        profile_key: str | None = None,
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        spec = cls.spec(path, entity, profile_key=profile_key)

        if not spec:
            return None

        return ChatPresentationCompositeVisualBuilder.build_chart(host, root, path, spec)

    @classmethod
    def build_tree(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        *,
        profile_key: str | None = None,
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        spec = cls.spec(path, entity, profile_key=profile_key)

        if not spec:
            return None

        return ChatPresentationCompositeVisualBuilder.build_tree(host, root, path, spec)

    @classmethod
    def build_dashboard(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        *,
        profile_key: str | None = None,
        entity: str | None = None,
        kpi: dict[str, Any] | None = None,
        tree: dict[str, Any] | None = None,
        chart: dict[str, Any] | None = None,
        table: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        spec = cls.spec(path, entity, profile_key=profile_key)

        if not spec:
            return None

        return ChatPresentationCompositeVisualBuilder.build_dashboard(
            host,
            root,
            path,
            spec,
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table,
        )

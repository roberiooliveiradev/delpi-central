"""Registry declarativo de texto por perfil — Playbook 12 R5."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

TextBuilderFn = Callable[
    ["ExternalActionResultPresenter", dict[str, Any], str],
    dict[str, Any] | None,
]


class ChatPresentationProfileTextBuilderService:
    @classmethod
    def builder_registry(
        cls,
        presenter: ExternalActionResultPresenter,
    ) -> dict[str, TextBuilderFn]:
        del presenter

        def _none(
            _presenter: ExternalActionResultPresenter,
            _root: dict[str, Any],
            _path: str,
        ) -> None:
            return None

        legacy_keys = (
            "build_analyser_text",
            "build_stock_text",
            "build_factory_status_text",
            "build_production_status_text",
            "build_shipping_status_text",
            "build_structure_exclusivity_text",
            "build_raw_material_price_text",
            "build_cost_impact_text",
            "build_product_pricing_text",
            "build_purchase_history_text",
            "build_tree_hierarchy_text",
        )

        return {key: _none for key in legacy_keys}

    @classmethod
    def build(
        cls,
        presenter: ExternalActionResultPresenter,
        data: Any,
        *,
        path: str,
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        builder_name = str(profile.get("textBuilder") or "").strip()
        options = profile.get("textBuildOptions")

        if not builder_name:
            return None

        builder = cls.builder_registry(presenter).get(builder_name)

        if not builder:
            return None

        root = presenter._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        if isinstance(options, dict) and options.get("requiresProduct") is True:
            if not isinstance(root.get("product"), dict):
                return None

        if isinstance(options, dict) and options.get("requiresItems") is True:
            items = root.get("items")

            if not isinstance(items, list) or not items:
                return None

        return builder(presenter, root, path)

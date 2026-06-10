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
    ["ExternalActionResultPresenter", dict[str, Any], dict[str, Any], str],
    dict[str, Any] | None,
]


class ChatPresentationProfileTextBuilderService:
    @classmethod
    def builder_registry(
        cls,
        presenter: ExternalActionResultPresenter,
    ) -> dict[str, TextBuilderFn]:
        text_presenter = presenter._text()

        return {
            "build_analyser_text": cls._build_analyser_text,
            "build_stock_text": cls._build_stock_text,
            "build_factory_status_text": lambda p, root, path: p._build_factory_status_text_presentation(root, path),
            "build_production_status_text": lambda p, root, path: p._build_production_status_text_presentation(root, path),
            "build_shipping_status_text": lambda p, root, path: p._build_shipping_status_text_presentation(root, path),
            "build_structure_exclusivity_text": lambda p, root, path: p._build_structure_exclusivity_text_presentation(root, path),
            "build_raw_material_price_text": lambda p, root, path: p._build_raw_material_price_intelligence_text_presentation(root, path),
            "build_cost_impact_text": lambda p, root, path: p._build_cost_impact_simulation_text_presentation(root, path),
            "build_product_pricing_text": lambda p, root, path: p._build_product_pricing_text_presentation(root, path),
            "build_last_purchase_text": lambda p, root, path: p._build_last_purchase_text_presentation(root, path),
            "build_purchase_history_text": lambda p, root, path: p._build_purchase_history_text_presentation(root, path),
            "build_purchases_text": lambda p, root, path: p._build_purchases_text_presentation(root, path),
            "build_tree_hierarchy_text": lambda p, root, path: text_presenter.build_tree_hierarchy_text(root, path),
        }

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

    @staticmethod
    def _build_analyser_text(
        presenter: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
    ) -> dict[str, Any] | None:
        normalized = presenter._normalize_analyser_root(root)
        product = normalized.get("product")

        if not isinstance(product, dict):
            return None

        return presenter._build_product_analyser_text_presentation(
            normalized,
            presenter._normalize_api_section(product),
            path,
        )

    @staticmethod
    def _build_stock_text(
        presenter: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
    ) -> dict[str, Any] | None:
        items = root.get("items")

        if not isinstance(items, list) or not items:
            return None

        return presenter._build_stock_text_presentation(root, path)

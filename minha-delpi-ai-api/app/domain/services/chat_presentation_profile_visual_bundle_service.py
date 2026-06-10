"""Registry declarativo de bundles visuais por perfil — Playbook 12 R2."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TYPE_CHECKING

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_tree_meta_caption_service import (
    ChatPresentationTreeMetaCaptionService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

VisualBuilderFn = Callable[..., dict[str, Any] | None]


class ChatPresentationProfileVisualBundleService:
    @classmethod
    def builder_registry(
        cls,
        presenter: ExternalActionResultPresenter,
    ) -> dict[str, VisualBuilderFn]:
        stock = presenter._stock()

        return {
            "build_stock_kpi": stock.build_stock_kpi_presentation,
            "build_stock_tree": stock.build_stock_tree_presentation,
            "build_stock_chart": stock.build_stock_chart_presentation,
            "build_stock_dashboard": stock.build_stock_dashboard_presentation,
            "build_analyser_tree": presenter.build_analyser_tree_presentation,
            "build_analyser_chart": presenter.build_analyser_chart_presentation,
            "build_analyser_kpi": presenter.build_analyser_kpi_presentation,
            "build_analyser_dashboard": presenter.build_analyser_dashboard_presentation,
            "build_factory_kpi": presenter.build_factory_kpi_presentation,
            "build_factory_tree": presenter.build_factory_tree_presentation,
            "build_factory_chart": presenter.build_factory_chart_presentation,
            "build_factory_dashboard": presenter.build_factory_dashboard_presentation,
            "build_raw_material_price_kpi": presenter.build_raw_material_price_kpi_presentation,
            "build_raw_material_price_tree": presenter.build_raw_material_price_tree_presentation,
            "build_raw_material_price_chart": presenter.build_raw_material_price_chart_presentation,
            "build_raw_material_price_dashboard": presenter.build_raw_material_price_dashboard_presentation,
            "build_cost_impact_kpi": presenter.build_cost_impact_kpi_presentation,
            "build_cost_impact_tree": presenter.build_cost_impact_tree_presentation,
            "build_cost_impact_chart": presenter.build_cost_impact_chart_presentation,
            "build_cost_impact_dashboard": presenter.build_cost_impact_dashboard_presentation,
            "build_product_pricing_kpi": presenter.build_product_pricing_kpi_presentation,
            "build_product_pricing_tree": presenter.build_product_pricing_tree_presentation,
            "build_product_pricing_chart": presenter.build_product_pricing_chart_presentation,
            "build_product_pricing_dashboard": presenter.build_product_pricing_dashboard_presentation,
            "build_production_status_kpi": presenter.build_production_status_kpi_presentation,
            "build_production_status_tree": presenter.build_production_status_tree_presentation,
            "build_production_status_chart": presenter.build_production_status_chart_presentation,
            "build_production_status_dashboard": presenter.build_production_status_dashboard_presentation,
            "build_shipping_status_kpi": presenter.build_shipping_status_kpi_presentation,
            "build_shipping_status_tree": presenter.build_shipping_status_tree_presentation,
            "build_shipping_status_chart": presenter.build_shipping_status_chart_presentation,
            "build_shipping_status_dashboard": presenter.build_shipping_status_dashboard_presentation,
            "build_structure_exclusivity_kpi": presenter.build_structure_exclusivity_kpi_presentation,
            "build_structure_exclusivity_tree": presenter.build_structure_exclusivity_tree_presentation,
            "build_structure_exclusivity_chart": presenter.build_structure_exclusivity_chart_presentation,
            "build_structure_exclusivity_dashboard": presenter.build_structure_exclusivity_dashboard_presentation,
            "build_last_purchase_kpi": presenter.build_last_purchase_kpi_presentation,
            "build_last_purchase_tree": presenter.build_last_purchase_tree_presentation,
            "build_last_purchase_chart": presenter.build_last_purchase_chart_presentation,
            "build_last_purchase_dashboard": presenter.build_last_purchase_dashboard_presentation,
            "build_purchase_history_kpi": presenter.build_purchase_history_kpi_presentation,
            "build_purchase_history_tree": presenter.build_purchase_history_tree_presentation,
            "build_purchase_history_chart": presenter.build_purchase_history_chart_presentation,
            "build_purchase_history_dashboard": presenter.build_purchase_history_dashboard_presentation,
            "build_purchases_kpi": presenter.build_purchases_kpi_presentation,
            "build_purchases_tree": presenter.build_purchases_tree_presentation,
            "build_purchases_chart": presenter.build_purchases_chart_presentation,
            "build_purchases_dashboard": presenter.build_purchases_dashboard_presentation,
        }

    @classmethod
    def visual_builders(cls, profile: dict[str, Any]) -> dict[str, str]:
        raw = profile.get("visualBuilders")

        if not isinstance(raw, dict):
            return {}

        return {
            str(view).strip().lower(): str(builder).strip()
            for view, builder in raw.items()
            if str(view).strip() and str(builder).strip()
        }

    @classmethod
    def chart_policy(cls, profile: dict[str, Any]) -> str:
        return str(profile.get("chartPolicy") or "auto").strip().lower() or "auto"

    @classmethod
    def visual_bundle_config(cls, profile: dict[str, Any]) -> dict[str, Any]:
        raw = profile.get("visualBundle")

        return dict(raw) if isinstance(raw, dict) else {}

    @classmethod
    def should_skip_bundle(cls, root: dict[str, Any], profile: dict[str, Any]) -> bool:
        bundle_config = cls.visual_bundle_config(profile)

        if bundle_config.get("requiresItems") is True:
            items = root.get("items")

            return not isinstance(items, list) or not items

        return False

    @classmethod
    def enrich_from_profile(
        cls,
        metadata: dict[str, Any],
        *,
        profile: dict[str, Any],
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
        attach_auxiliary: Callable[..., None],
        dashboard_input_slots: Callable[..., dict[str, dict[str, Any] | None]],
    ) -> bool:
        visual_builders = cls.visual_builders(profile)

        if not visual_builders:
            return False

        if cls.should_skip_bundle(root, profile):
            return False

        bundle_config = cls.visual_bundle_config(profile)
        registry = cls.builder_registry(presenter)
        dashboard_list_role = str(bundle_config.get("dashboardListRole") or "list").strip() or "list"
        dashboard_include_tree = bundle_config.get("dashboardIncludeTree") is True

        for view in view_order:
            builder_name = visual_builders.get(view)

            if not builder_name:
                continue

            builder = registry.get(builder_name)

            if not builder:
                continue

            if view == "dashboard":
                slots = dashboard_input_slots(metadata, list_role=dashboard_list_role)
                dashboard_kwargs: dict[str, Any] = {
                    "kpi": slots.get("kpi"),
                    "chart": slots.get("chart"),
                    "table": slots.get("table"),
                }

                if dashboard_include_tree:
                    dashboard_kwargs["tree"] = slots.get("tree")
                elif builder_name == "build_factory_dashboard":
                    dashboard_kwargs["tree"] = slots.get("tree")

                presentation = builder(root, path, **dashboard_kwargs)
            else:
                presentation = builder(root, path)

            if view == "tree" and isinstance(presentation, dict):
                ChatPresentationTreeMetaCaptionService.enrich(presentation, path=path)

            if presentation:
                attach_auxiliary(metadata, view, presentation, primary_type=primary_type)

        return True

    @classmethod
    def build_profile_view(
        cls,
        presenter: ExternalActionResultPresenter,
        *,
        path: str,
        view: str,
        data: Any,
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_api_delpi_response_profile_service import (
            ChatApiDelpiResponseProfileService,
        )
        from app.domain.services.chat_presentation_operational_root_service import (
            ChatPresentationOperationalRootService,
        )

        normalized_view = str(view or "").strip().lower()

        if not normalized_view:
            return None

        entity = entity or cls._resolve_entity(data, path=path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        builder_name = cls.visual_builders(profile).get(normalized_view)

        if not builder_name:
            return None

        builder = cls.builder_registry(presenter).get(builder_name)

        if not builder:
            return None

        root = presenter._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        builder_root = ChatPresentationOperationalRootService.resolve_bundle_root(
            root,
            path=path,
            entity=entity,
        )

        if builder_root is None:
            return None

        presentation = builder(builder_root, path)

        if normalized_view == "tree" and isinstance(presentation, dict):
            ChatPresentationTreeMetaCaptionService.enrich(presentation, path=path)

        return presentation if isinstance(presentation, dict) else None

    @classmethod
    def _resolve_entity(cls, data: Any, *, path: str) -> str | None:
        from app.domain.services.chat_api_delpi_response_profile_service import (
            ChatApiDelpiResponseProfileService,
        )

        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
        entity = str(profile.entity or "").strip()

        return entity or None

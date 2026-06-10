"""Pacote de visuais auxiliares — chat base (herdado por qualquer agente/rota)."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

_AUXILIARY_SLOTS: dict[str, str] = {
    "chart": "chartPresentation",
    "tree": "treePresentation",
    "kpi": "kpiPresentation",
    "dashboard": "dashboardPresentation",
    "table": "tablePresentation",
}


class ChatPresentationVisualBundleService:
    """Preenche slots auxiliares sem substituir a visão primária escolhida pelo decisor."""

    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        path: str,
        data: Any,
        presenter: ExternalActionResultPresenter,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        root = presenter._unwrap_data(data)

        if not isinstance(root, dict):
            return

        entity = cls._resolve_entity(data, path=path)
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        profile_key = str(profile.get("profileKey") or "generic")
        view_order = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]
        primary_type = cls._primary_type(metadata)
        is_factory_profile = profile_key == "factory_status" or ChatPresentationProfileService.has_flag(
            path,
            "factory_status",
            entity=entity,
        )
        is_mp_intelligence_profile = (
            profile_key == "raw_material_price_intelligence"
            or ChatPresentationProfileService.has_flag(
                path,
                "raw_material_price_intelligence",
                entity=entity,
            )
        )
        is_cost_impact_profile = (
            profile_key == "cost_impact_simulation"
            or ChatPresentationProfileService.has_flag(
                path,
                "cost_impact_simulation",
                entity=entity,
            )
        )
        is_sale_pricing_profile = (
            profile_key == "sale_pricing"
            or ChatPresentationProfileService.has_flag(path, "sale_pricing", entity=entity)
        )
        is_production_status_profile = (
            profile_key == "production_status"
            or ChatPresentationProfileService.has_flag(path, "production_status", entity=entity)
        )
        is_shipping_status_profile = (
            profile_key == "shipping_status"
            or ChatPresentationProfileService.has_flag(path, "shipping_status", entity=entity)
        )
        is_structure_exclusivity_profile = (
            profile_key == "structure_exclusivity"
            or ChatPresentationProfileService.has_flag(path, "structure_exclusivity", entity=entity)
        )
        is_last_purchase_profile = (
            profile_key == "last_purchase"
            or ChatPresentationProfileService.has_flag(path, "last_purchase", entity=entity)
        )
        is_purchase_price_history_profile = (
            profile_key == "purchase_price_history"
            or ChatPresentationProfileService.has_flag(path, "purchase_price_history", entity=entity)
        )
        is_purchase_budget_history_profile = (
            profile_key == "purchase_budget_history"
            or ChatPresentationProfileService.has_flag(path, "purchase_budget_history", entity=entity)
        )
        is_purchase_list_profile = (
            profile_key == "purchase_list"
            or ChatPresentationProfileService.has_flag(path, "purchase_list", entity=entity)
        )

        if (
            not is_factory_profile
            and not is_mp_intelligence_profile
            and not is_cost_impact_profile
            and not is_sale_pricing_profile
            and not is_production_status_profile
            and not is_shipping_status_profile
            and not is_structure_exclusivity_profile
            and not is_last_purchase_profile
            and not is_purchase_price_history_profile
            and not is_purchase_budget_history_profile
            and not is_purchase_list_profile
        ):
            cls._ensure_chart(metadata, root=root, path=path, presenter=presenter, primary_type=primary_type)

        if profile_key == "stock" or ChatPresentationProfileService.has_flag(path, "stock", entity=entity):
            cls._enrich_stock_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_factory_profile:
            cls._enrich_factory_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_mp_intelligence_profile:
            cls._enrich_raw_material_price_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_cost_impact_profile:
            cls._enrich_cost_impact_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_sale_pricing_profile:
            cls._enrich_sale_pricing_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
            )

        if is_production_status_profile:
            cls._enrich_playbook_status_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
                profile="production",
            )

        if is_shipping_status_profile:
            cls._enrich_playbook_status_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
                profile="shipping",
            )

        if is_structure_exclusivity_profile:
            cls._enrich_playbook_status_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
                profile="structure_exclusivity",
            )

        if is_last_purchase_profile:
            cls._enrich_mp_purchase_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
                profile="last_purchase",
            )

        if is_purchase_price_history_profile or is_purchase_budget_history_profile:
            cls._enrich_mp_purchase_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
                profile="purchase_history",
            )

        if is_purchase_list_profile:
            cls._enrich_mp_purchase_bundle(
                metadata,
                root=root,
                path=path,
                presenter=presenter,
                primary_type=primary_type,
                view_order=view_order,
                profile="purchase_list",
            )

        cls._ensure_generic_kpi_bundle(
            metadata,
            root=root,
            path=path,
            presenter=presenter,
            primary_type=primary_type,
            view_order=view_order,
        )

        cls._sync_available_formats(metadata, view_order)

    @classmethod
    def _enrich_stock_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        items = root.get("items")

        if not isinstance(items, list) or not items:
            return

        stock = presenter._stock()

        if "kpi" in view_order:
            kpi = stock.build_stock_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = stock.build_stock_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role="list")

            dashboard = stock.build_stock_dashboard_presentation(
                root,
                path,
                kpi=slots.get("kpi"),
                chart=slots.get("chart"),
                table=slots.get("table"),
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_factory_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if "kpi" in view_order:
            kpi = presenter.build_factory_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = presenter.build_factory_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = presenter.build_factory_chart_presentation(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role="stock")

            dashboard = presenter.build_factory_dashboard_presentation(
                root,
                path,
                kpi=slots.get("kpi"),
                tree=slots.get("tree"),
                chart=slots.get("chart"),
                table=slots.get("table"),
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_raw_material_price_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if "kpi" in view_order:
            kpi = presenter.build_raw_material_price_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = presenter.build_raw_material_price_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = presenter.build_raw_material_price_chart_presentation(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role="profile")

            dashboard = presenter.build_raw_material_price_dashboard_presentation(
                root,
                path,
                kpi=slots.get("kpi"),
                tree=slots.get("tree"),
                chart=slots.get("chart"),
                table=slots.get("table"),
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_cost_impact_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if "kpi" in view_order:
            kpi = presenter.build_cost_impact_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = presenter.build_cost_impact_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = presenter.build_cost_impact_chart_presentation(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role="profile")

            dashboard = presenter.build_cost_impact_dashboard_presentation(
                root,
                path,
                kpi=slots.get("kpi"),
                chart=slots.get("chart"),
                table=slots.get("table"),
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_mp_purchase_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
        profile: str,
    ) -> None:
        builders = {
            "last_purchase": (
                presenter.build_last_purchase_kpi_presentation,
                presenter.build_last_purchase_tree_presentation,
                presenter.build_last_purchase_chart_presentation,
                presenter.build_last_purchase_dashboard_presentation,
            ),
            "purchase_history": (
                presenter.build_purchase_history_kpi_presentation,
                presenter.build_purchase_history_tree_presentation,
                presenter.build_purchase_history_chart_presentation,
                presenter.build_purchase_history_dashboard_presentation,
            ),
            "purchase_list": (
                presenter.build_purchases_kpi_presentation,
                presenter.build_purchases_tree_presentation,
                presenter.build_purchases_chart_presentation,
                presenter.build_purchases_dashboard_presentation,
            ),
        }
        profile_builders = builders.get(profile)

        if not profile_builders:
            return

        build_kpi, build_tree, build_chart, build_dashboard = profile_builders

        if "kpi" in view_order:
            kpi = build_kpi(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = build_tree(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = build_chart(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role="list")

            dashboard = build_dashboard(
                root,
                path,
                kpi=slots.get("kpi"),
                chart=slots.get("chart"),
                table=slots.get("table"),
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_playbook_status_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
        profile: str,
    ) -> None:
        builders = {
            "production": (
                presenter.build_production_status_kpi_presentation,
                presenter.build_production_status_tree_presentation,
                presenter.build_production_status_chart_presentation,
                presenter.build_production_status_dashboard_presentation,
            ),
            "shipping": (
                presenter.build_shipping_status_kpi_presentation,
                presenter.build_shipping_status_tree_presentation,
                presenter.build_shipping_status_chart_presentation,
                presenter.build_shipping_status_dashboard_presentation,
            ),
            "structure_exclusivity": (
                presenter.build_structure_exclusivity_kpi_presentation,
                presenter.build_structure_exclusivity_tree_presentation,
                presenter.build_structure_exclusivity_chart_presentation,
                presenter.build_structure_exclusivity_dashboard_presentation,
            ),
        }
        profile_builders = builders.get(profile)

        if not profile_builders:
            return

        build_kpi, build_tree, build_chart, build_dashboard = profile_builders
        list_role = "structure" if profile == "structure_exclusivity" else "list"

        if "kpi" in view_order:
            kpi = build_kpi(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = build_tree(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = build_chart(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role=list_role)
            dashboard_kwargs: dict[str, Any] = {
                "kpi": slots.get("kpi"),
                "chart": slots.get("chart"),
                "table": slots.get("table"),
            }

            if profile == "structure_exclusivity":
                dashboard_kwargs["tree"] = slots.get("tree")

            dashboard = build_dashboard(root, path, **dashboard_kwargs)

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _enrich_sale_pricing_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if "kpi" in view_order:
            kpi = presenter.build_product_pricing_kpi_presentation(root, path)

            if kpi:
                cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if "tree" in view_order:
            tree = presenter.build_product_pricing_tree_presentation(root, path)

            if tree:
                cls._attach_auxiliary(metadata, "tree", tree, primary_type=primary_type)

        if "chart" in view_order:
            chart = presenter.build_product_pricing_chart_presentation(root, path)

            if chart:
                cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

        if "dashboard" in view_order:
            slots = cls._dashboard_input_slots(metadata, list_role="profile")

            dashboard = presenter.build_product_pricing_dashboard_presentation(
                root,
                path,
                kpi=slots.get("kpi"),
                chart=slots.get("chart"),
                table=slots.get("table"),
            )

            if dashboard:
                cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _ensure_chart(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
    ) -> None:
        if cls._slot_value(metadata, "chart"):
            return

        chart = presenter.build_chart_presentation(
            root,
            path=path,
            force=True,
        )

        if chart:
            cls._attach_auxiliary(metadata, "chart", chart, primary_type=primary_type)

    @classmethod
    def _dashboard_input_slots(
        cls,
        metadata: dict[str, Any],
        *,
        list_role: str = "list",
    ) -> dict[str, dict[str, Any] | None]:
        kpi_slot = metadata.get("kpiPresentation")
        tree_slot = metadata.get("treePresentation")
        chart_slot = metadata.get("chartPresentation")
        table_slot = metadata.get("tablePresentation")

        if not isinstance(table_slot, dict) and isinstance(metadata.get("tablePresentations"), list):
            tables = metadata["tablePresentations"]

            for candidate in tables:
                if isinstance(candidate, dict) and candidate.get("role") == list_role:
                    table_slot = candidate
                    break

            if not isinstance(table_slot, dict):
                for candidate in tables:
                    if isinstance(candidate, dict) and candidate.get("type") == "table":
                        table_slot = candidate
                        break

            if not isinstance(table_slot, dict) and tables and isinstance(tables[-1], dict):
                table_slot = tables[-1]

        return {
            "kpi": kpi_slot if isinstance(kpi_slot, dict) else None,
            "tree": tree_slot if isinstance(tree_slot, dict) else None,
            "chart": chart_slot if isinstance(chart_slot, dict) else None,
            "table": table_slot if isinstance(table_slot, dict) else None,
        }

    @classmethod
    def _attach_auxiliary(
        cls,
        metadata: dict[str, Any],
        view: str,
        presentation: dict[str, Any],
        *,
        primary_type: str,
    ) -> None:
        slot = _AUXILIARY_SLOTS.get(view)

        if not slot or not isinstance(presentation, dict):
            return

        if primary_type == view:
            existing = metadata.get("presentation")

            if view == "dashboard" or not isinstance(existing, dict):
                metadata["presentation"] = presentation
            elif not existing:
                metadata["presentation"] = presentation

            return

        if not metadata.get(slot):
            metadata[slot] = presentation

    @classmethod
    def _slot_value(cls, metadata: dict[str, Any], view: str) -> dict[str, Any] | None:
        slot = _AUXILIARY_SLOTS.get(view)
        presentation = metadata.get(slot) if slot else None

        if isinstance(presentation, dict):
            return presentation

        primary = metadata.get("presentation")

        if isinstance(primary, dict) and str(primary.get("type") or "").strip().lower() == view:
            return primary

        return None

    @classmethod
    def _primary_type(cls, metadata: dict[str, Any]) -> str:
        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            return str(presentation.get("type") or "").strip().lower()

        return ""

    @classmethod
    def _ensure_generic_kpi_bundle(
        cls,
        metadata: dict[str, Any],
        *,
        root: dict[str, Any],
        path: str,
        presenter: ExternalActionResultPresenter,
        primary_type: str,
        view_order: list[str],
    ) -> None:
        if cls._slot_value(metadata, "kpi"):
            return

        if "kpi" not in view_order:
            return

        kpi = presenter._build_kpi_chart(root, path)

        if isinstance(kpi, dict) and str(kpi.get("type") or "").strip().lower() == "kpi":
            cls._attach_auxiliary(metadata, "kpi", kpi, primary_type=primary_type)

        if cls._slot_value(metadata, "dashboard") or "dashboard" not in view_order:
            return

        dashboard = presenter.build_dashboard_presentation(root, path=path)

        if isinstance(dashboard, dict) and dashboard.get("type") == "dashboard":
            cls._attach_auxiliary(metadata, "dashboard", dashboard, primary_type=primary_type)

    @classmethod
    def _sync_available_formats(cls, metadata: dict[str, Any], view_order: list[str]) -> None:
        formats = list(metadata.get("availableFormats") or [])
        seen = {str(token).strip().lower() for token in formats}

        for view in view_order:
            if view in {"line_chart", "bar_chart", "horizontal_bar", "donut", "area_chart"}:
                mapped = "chart"
            else:
                mapped = view

            if mapped == "text":
                token = "text"

                if token not in seen and metadata.get("textPresentation"):
                    formats.append(token)
                    seen.add(token)

                continue

            if cls._slot_value(metadata, mapped) and mapped not in seen:
                formats.append(mapped)
                seen.add(mapped)

        if metadata.get("textPresentation") and "text" not in seen:
            formats.append("text")
            seen.add("text")

        if metadata.get("textPresentation"):
            canvas = "canvas"

            if canvas not in seen:
                formats.append(canvas)

        metadata["availableFormats"] = formats

    @classmethod
    def _resolve_entity(cls, data: Any, *, path: str) -> str | None:
        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
        entity = str(profile.entity or "").strip()

        return entity or None

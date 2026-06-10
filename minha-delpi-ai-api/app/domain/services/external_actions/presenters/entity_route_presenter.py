"""Roteamento por meta.entity do ExternalActionResultPresenter — Fase 3A lote 10."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_api_delpi_response_profile_service import (
    ApiDelpiResponseProfile,
    ChatApiDelpiResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionEntityRoutePresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def prepare_presentation_root(self, data, *, path: str):
        """Alinha builders (`build_*_presentation`) ao mesmo root que `present()` usa por entidade."""
        root = self._host._unwrap_data(data)

        if not isinstance(root, dict):
            return data

        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
        normalized = self._normalize_root_for_entity(root, profile)

        if normalized is root:
            return data

        return normalized

    def _normalize_root_for_entity(self, root: dict, profile: ApiDelpiResponseProfile) -> dict:
        entity = profile.entity

        if entity == "product_analyser":
            return self._host._normalize_analyser_root(root)

        return root

    def _present_entity_first(
            self,
            data,
            *,
            path: str,
            profile: ApiDelpiResponseProfile,
        ) -> dict | None:
            entity = profile.entity

            if not ChatApiDelpiResponseProfileService.is_entity_routed_for_present(entity):
                return None

            error = self._host._detect_api_error(data, path=path)

            if error:
                return error

            root = self._host._unwrap_data(data)

            empty_operational = self._host._present_empty_operational_result(
                path=path,
                root=root,
            )

            if empty_operational:
                return empty_operational

            if entity == "product_analyser" and isinstance(root, dict):
                root = self._normalize_root_for_entity(root, profile)
                product = root.get("product")

                if isinstance(product, dict):
                    return self._host._present_product_analyser(
                        root,
                        self._host._normalize_api_section(product),
                        path,
                    )

            if entity == "product_factory_status" and isinstance(root, dict):
                return self._host._present_product_factory_status(root, path)

            if entity == "product_production_status" and isinstance(root, dict):
                return self._host._present_product_production_status(root, path)

            if entity == "product_shipping_status" and isinstance(root, dict):
                return self._host._present_product_shipping_status(root, path)

            if entity == "product_structure_exclusivity" and isinstance(root, dict):
                return self._host._present_product_structure_exclusivity(root, path)

            if entity == "product_raw_material_price_intelligence" and isinstance(root, dict):
                return self._host._present_product_raw_material_price_intelligence(root, path)

            if entity == "product_cost_impact_simulation" and isinstance(root, dict):
                return self._host._present_product_cost_impact_simulation(root, path)

            if entity == "product_last_purchase" and isinstance(root, dict):
                return self._host._present_product_last_purchase(root, path)

            if entity in {
                "product_purchase_price_history",
                "product_purchase_budget_history",
            } and isinstance(root, dict):
                playbook = self._host._present_playbook_report(root, path, entity=entity)

                if playbook:
                    return playbook

            if entity == "product_structure" and isinstance(root, dict):
                structure_result = self._host._present_product_structure(root, path)

                if structure_result:
                    return structure_result

            if entity == "product_parents" and isinstance(root, dict):
                structure_result = self._host._present_product_structure(root, path)

                if structure_result:
                    return structure_result

            product = root.get("product") if isinstance(root, dict) else None

            if entity == "product" and isinstance(product, dict):
                return self._host._present_product(root, self._host._normalize_api_section(product))

            if isinstance(root, dict):
                items = root.get("items")

                if isinstance(items, list) and items:
                    title = self._host._infer_items_title(items, path)
                    first_item = items[0] if isinstance(items[0], dict) else {}

                    if entity == "product_stock" or self._host._is_stock_data(first_item):
                        return self._host._present_product_stock(
                            items,
                            path=path,
                            title=title,
                            root=root,
                        )

                    if entity == "product_guide" or (
                        isinstance(first_item, dict)
                        and (
                            "operation_description" in first_item
                            or "operation_code" in first_item
                        )
                    ):
                        return self._host._present_product_guide(items, path=path, title=title)

                    if entity == "product_inspection" or self._host._looks_like_inspection_item(
                        first_item
                    ):
                        return self._host._present_product_inspection(items, path=path, title=title)

                    if entity == "product_search" and isinstance(first_item, dict) and (
                        "code" in first_item and "description" in first_item
                    ):
                        return self._host._present_product_search(root, items, title=title)

                    path_routed = self._host._present_path_routed_items(root, path)

                    if path_routed:
                        return path_routed

            return self._present_entity_extensions(
                root,
                path=path,
                profile=profile,
            )

    def _present_entity_extensions(
            self,
            root,
            *,
            path: str,
            profile: ApiDelpiResponseProfile,
        ) -> dict | None:
            entity = profile.entity
            effective_path = ChatApiDelpiResponseProfileService.presentation_path(
                path=path,
                entity=entity,
            )

            if entity == "product_billing":
                billing = self._host._present_product_billing_summary(
                    root,
                    effective_path,
                    entity=entity,
                )

                if billing:
                    return billing

            if entity == "product_pricing" and isinstance(root, dict):
                prices = root.get("prices")

                if isinstance(prices, list) and prices:
                    title = self._host._infer_items_title(prices, effective_path)

                    return self._host._present_items(
                        prices,
                        title=title or self._host._presenter_text("productDetailTitles", "prices", code=""),
                    )

                pricing_fallback = self._host._present_dict_fallback(root, effective_path)

                if pricing_fallback:
                    return pricing_fallback

            if entity in ChatApiDelpiResponseProfileService.PRODUCT_LIST_PRESENT_ENTITIES:
                items = root.get("items") if isinstance(root, dict) else None

                if isinstance(items, list):
                    if not items:
                        title = self._host._infer_items_title([], effective_path) or self._host._presenter_text(
                            "generic",
                            "defaultQueryTitle",
                        )
                        return {
                            "titulo": title,
                            "linhas": [
                                self._host._presenter_text("generic", "emptyItemsQuery")
                            ],
                            "dados": root,
                        }

                    if entity == "product_open_orders":
                        return self._host._present_items(
                            items,
                            title=self._host._infer_items_title(items, effective_path),
                        )

                    title = self._host._infer_items_title(items, effective_path)
                    return self._host._present_items(items, title=title)

            if entity == "product_sales" and isinstance(root, dict):
                kpi = self._host._present_kpi_response(root, effective_path, entity=entity)

                if kpi:
                    return kpi

            if ChatApiDelpiResponseProfileService.is_kpi_entity(entity) and isinstance(root, dict):
                specialized = (
                    self._host._present_stock_value_summary(root, effective_path, entity=entity)
                    or self._host._present_financial_pmr(root, effective_path, entity=entity)
                )

                if specialized:
                    return specialized

                kpi = self._host._present_kpi_response(root, effective_path, entity=entity)

                if kpi:
                    return kpi

            if entity in ChatApiDelpiResponseProfileService.LMP_PRESENT_ENTITIES and isinstance(
                root, dict
            ):
                lmp_page = self._host._present_lmp_page(root)

                if lmp_page:
                    return lmp_page

                lmp_detail = self._host._present_lmp_detail(root)

                if lmp_detail:
                    return lmp_detail

            if entity in ChatApiDelpiResponseProfileService.SALE_ORDER_PRESENT_ENTITIES:
                items = root.get("items") if isinstance(root, dict) else None

                if isinstance(items, list) and items:
                    return self._host._present_sale_orders(root, items)

            if entity in ChatApiDelpiResponseProfileService.SQL_PRESENT_ENTITIES:
                sql_resultsets = self._host._present_sql_resultsets(root, effective_path)

                if sql_resultsets:
                    return sql_resultsets

                sql_rows = self._host._present_sql_rows(root)

                if sql_rows:
                    return sql_rows

            if entity in ChatApiDelpiResponseProfileService.SYSTEM_PRESENT_ENTITIES and isinstance(
                root, dict
            ):
                system = (
                    self._host._present_system_tables_search(root, effective_path, entity=entity)
                    or self._host._present_system_table_columns(root, effective_path, entity=entity)
                )

                if system:
                    return system

                system_fallback = self._host._present_dict_fallback(root, effective_path)

                if system_fallback:
                    return system_fallback

            if entity == "commercial_proposal" and isinstance(root, dict):
                items = root.get("items")

                if isinstance(items, list):
                    title = self._host._infer_items_title(items, effective_path)
                    return self._host._present_items(items, title=title)

            if entity == "eficiencia_fabril_appointment" and isinstance(root, dict):
                items = root.get("items")

                if isinstance(items, list) and items:
                    title = self._host._infer_items_title(items, effective_path)
                    return self._host._present_items(items, title=title)

            return None

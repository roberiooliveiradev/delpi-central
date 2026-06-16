"""Roteamento legacy sem meta.entity — Fase 3A lote 9"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionLegacyRoutePresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _present_legacy(self, data, *, path: str = "") -> dict:
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

            if isinstance(root, dict):
                profile = ChatOperationalResponseProfileService.resolve(data, path=path)

                if profile.entity in ChatOperationalResponseProfileService.PLAYBOOK_OPERATIONAL_ENTITIES:
                    playbook = self._host._present_playbook_report(
                        root,
                        path,
                        entity=profile.entity,
                    )

                    if playbook:
                        return playbook

            if isinstance(root, dict) and "/analyser" in str(path or "").lower():
                root = self._host._normalize_analyser_root(root)

            product = root.get("product") if isinstance(root, dict) else None

            if isinstance(product, dict):
                product = self._host._normalize_api_section(product)

                if "/analyser" in str(path or "").lower():
                    return self._host._present_product_analyser(root, product, path)

                return self._host._present_product(root, product)

            if isinstance(root, dict):
                lmp_page = self._host._present_lmp_page(root)

                if lmp_page:
                    return lmp_page

                lmp_detail = self._host._present_lmp_detail(root)

                if lmp_detail:
                    return lmp_detail

                path_routed = self._host._present_path_routed_items(root, path)

                if path_routed:
                    return path_routed

                if not self._host._is_product_operational_path(path):
                    sql_resultsets = self._host._present_sql_resultsets(root, path)

                    if sql_resultsets:
                        return sql_resultsets

            if isinstance(root, list) and root:
                if self._host._is_product_operational_path(path):
                    path_routed = self._host._present_path_routed_items({"items": root}, path)

                    if path_routed:
                        return path_routed

                sql_result = self._host._present_sql_rows(root)

                if sql_result:
                    return sql_result

            if isinstance(root, dict) and "/structure" in str(path or "").lower():
                structure_result = self._host._present_product_structure(root, path)

                if structure_result:
                    return structure_result

            if isinstance(root, dict):
                specialized = (
                    self._host._present_stock_value_summary(root, path)
                    or self._host._present_product_billing_summary(root, path)
                    or self._host._present_financial_pmr(root, path)
                    or self._host._present_system_tables_search(root, path)
                    or self._host._present_system_table_columns(root, path)
                )

                if specialized:
                    return specialized

            items = root.get("items") if isinstance(root, dict) else None

            if isinstance(items, list):
                if not items:
                    title = self._host._infer_items_title([], path) or self._host._presenter_text(
                        "generic", "defaultQueryTitle"
                    )
                    return {
                        "titulo": title,
                        "linhas": [
                            self._host._presenter_text("generic", "emptyItemsQuery")
                        ],
                        "dados": root,
                    }

                if items and isinstance(items[0], dict) and "sale_number" in items[0]:
                    return self._host._present_lmp_page(root)

                lowered_path = str(path or "").lower()

                if (
                    items
                    and isinstance(items[0], dict)
                    and "order_number" in items[0]
                    and "/production/" not in lowered_path
                    and not ChatOperationalResponseProfileService.is_playbook_operational_path(path)
                ):
                    return self._host._present_sale_orders(root, items)

                title = self._host._infer_items_title(items, path)
                first_item = items[0] if items and isinstance(items[0], dict) else {}

                if "/stock" in lowered_path or self._host._is_stock_data(first_item):
                    return self._host._present_product_stock(
                        items,
                        path=path,
                        title=title,
                        root=root if isinstance(root, dict) else None,
                    )

                if "/inspection" in lowered_path or self._host._looks_like_inspection_item(first_item):
                    return self._host._present_product_inspection(items, path=path, title=title)

                if items and isinstance(items[0], dict) and "code" in items[0] and "description" in items[0]:
                    return self._host._present_product_search(root, items, title=title)

                if items and isinstance(items[0], dict) and (
                    "operation_description" in items[0] or "operation_code" in items[0]
                ):
                    return self._host._present_product_guide(items, path=path, title=title)

                return self._host._present_items(items, title=title)

            if isinstance(root, dict) and self._host._looks_like_kpi_response(root, path):
                kpi = self._host._present_kpi_response(root, path)

                if kpi:
                    return kpi

            if isinstance(root, dict) and root:
                fallback = self._host._present_dict_fallback(root, path)
                if fallback:
                    return fallback

            return {
                "titulo": self._host._fallback_title(path)
                or self._host._presenter_text("generic", "apiResultTitle"),
                "linhas": [self._host._presenter_text("generic", "apiAuthorized")],
                "dados": root,
            }

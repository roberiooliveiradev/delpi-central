"""Construção de tabelas/gráficos ricos (presentation) — Fase 3A lote 11."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_api_delpi_response_profile_service import (
    ApiDelpiResponseProfile,
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionPresentationBuilderPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _build_items_table_for_path(
        self,
        items: list,
        *,
        title: str | None,
        path: str,
        entity: str | None = None,
        profile_name: str | None = None,
        role: str = "generic",
    ) -> dict | None:
        return self._host._product_list()._build_items_table(
            items,
            title=title,
            path=path,
            entity=entity,
            profile_name=profile_name,
            role=role,
        )

    def _build_presentation_by_entity(
            self,
            data,
            *,
            path: str,
            profile: ApiDelpiResponseProfile,
        ) -> dict | None:
            entity = profile.entity

            if not ChatApiDelpiResponseProfileService.is_entity_routed_for_present(entity):
                return None

            root = self._host._unwrap_data(data)

            if not isinstance(root, dict):
                return None

            if entity in ChatApiDelpiResponseProfileService.PLAYBOOK_OPERATIONAL_ENTITIES:
                return self._host._build_playbook_report_table(root, path, entity=entity)

            if entity == "product_factory_status":
                tables = self._host.build_factory_status_table_presentations(root, path)

                if tables:
                    return tables[0]

                return self._build_factory_status_table(root, path)

            if entity == "product_production_status":
                tables = self._host.build_production_status_table_presentations(root, path)

                if tables:
                    return tables[0]

                return self._host._build_playbook_report_table(root, path, entity=entity)

            if entity == "product_shipping_status":
                tables = self._host.build_shipping_status_table_presentations(root, path)

                if tables:
                    return tables[0]

                return self._host._build_playbook_report_table(root, path, entity=entity)

            if entity == "product_structure_exclusivity":
                tables = self._host.build_structure_exclusivity_table_presentations(root, path)

                if tables:
                    return tables[0]

                return self._host._build_playbook_report_table(root, path, entity=entity)

            if entity == "product_directives":
                tables = self._host.build_product_directives_table_presentations(root, path)

                if tables:
                    return tables[0]

            if entity == "product_raw_material_price_intelligence":
                tables = self._host.build_raw_material_price_intelligence_table_presentations(
                    root,
                    path,
                )

                if tables:
                    return tables[0]

            if entity == "product_cost_impact_simulation":
                tables = self._host.build_cost_impact_simulation_table_presentations(root, path)

                if tables:
                    return tables[0]

            if entity == "product_pricing":
                tables = self._host.build_product_pricing_table_presentations(root, path)

                if tables:
                    return tables[0]

            if entity == "product_last_purchase":
                tables = self._host.build_last_purchase_table_presentations(root, path)

                if tables:
                    return tables[0]

            if entity in {
                "product_purchase_price_history",
                "product_purchase_budget_history",
            }:
                tables = self._host.build_purchase_history_table_presentations(root, path)

                if tables:
                    return tables[0]

            if entity == "product_purchases":
                tables = self._host.build_purchases_table_presentations(root, path)

                if tables:
                    return tables[0]

            product = root.get("product")

            if entity == "product_analyser" and isinstance(product, dict):
                guide_table = self._host._build_product_analyser_guide_table(root)

                if guide_table:
                    return guide_table

                return self._host._build_product_analyser_profile_table(product, root, path=path)

            if entity == "product" and isinstance(product, dict):
                detail_list = self._host._extract_product_detail_list(root)

                if detail_list:
                    return self._build_product_detail_table(product, detail_list, root)

                return self._build_product_table(product, root, path=path)

            if entity in {"product_structure", "product_parents"}:
                if isinstance(root.get("root"), dict) and isinstance(root.get("items"), list):
                    if entity == "product_parents":
                        return None

                    structure_table = self._host._build_analyser_structure_components_table(root)

                    if structure_table:
                        return structure_table

            items = root.get("items")

            if isinstance(items, list) and items and isinstance(items[0], dict):
                title = self._host._infer_items_title(items, path)
                first_item = items[0]

                if entity == "product_stock" or self._host._is_stock_data(first_item):
                    return self._build_items_table_for_path(
                        items,
                        title=title,
                        path=path,
                        entity=entity,
                        role="stock",
                    )

                if entity == "product_inspection" or self._host._looks_like_inspection_item(first_item):
                    return self._host._build_inspection_items_table(items, path=path)

                if entity == "product_search" and "code" in first_item and "description" in first_item:
                    return self._build_product_search_table(items, root, title=title)

                if entity == "product_guide" or (
                    "operation_description" in first_item or "operation_code" in first_item
                ):
                    return self._build_items_table_for_path(
                        items,
                        title=title,
                        path=path,
                        entity=entity or "product_guide",
                        role="guide",
                    )

                if len(items) >= 2 or self._host._is_tabular_data(first_item):
                    return self._build_items_table_for_path(
                        items,
                        title=title,
                        path=path,
                        entity=entity,
                    )

            if entity in {
                "product_shipping_status",
                "product_structure_exclusivity",
            }:
                return self._host._build_playbook_report_table(root, path, entity=entity)

            return self._build_presentation_entity_extensions(
                root,
                path=path,
                profile=profile,
            )

    def _build_presentation_entity_extensions(
            self,
            root: dict,
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
                billing_table = self._host._build_product_billing_table(
                    root,
                    effective_path,
                    entity=entity,
                )

                if billing_table:
                    return billing_table

            if entity in ChatApiDelpiResponseProfileService.PRODUCT_LIST_PRESENT_ENTITIES:
                items = root.get("items")

                if isinstance(items, list) and items and isinstance(items[0], dict):
                    title = self._host._infer_items_title(items, effective_path)

                    if len(items) >= 2 or self._host._is_tabular_data(items[0]):
                        return self._build_items_table_for_path(
                            items,
                            title=title,
                            path=effective_path,
                            entity=entity,
                        )

            if entity in ChatApiDelpiResponseProfileService.SALE_ORDER_PRESENT_ENTITIES:
                items = root.get("items")

                if isinstance(items, list) and items:
                    return self._build_sale_orders_table(items, root)

            if entity in ChatApiDelpiResponseProfileService.SQL_PRESENT_ENTITIES:
                rows = self._host._collect_sql_resultset_rows(root.get("resultsets") or [])
                title = self._host._sql_result_title(root, effective_path)

                if rows:
                    return self._build_items_table_for_path(
                        rows,
                        title=title,
                        path=effective_path,
                        entity=entity,
                        role="list",
                    )

            if ChatApiDelpiResponseProfileService.is_kpi_entity(entity):
                stock_value_table = self._host._build_stock_value_branch_table(
                    root,
                    effective_path,
                    entity=entity,
                )

                if stock_value_table:
                    return stock_value_table

            if entity in ChatApiDelpiResponseProfileService.SYSTEM_PRESENT_ENTITIES:
                columns_table = self._host._build_system_columns_table(
                    root,
                    effective_path,
                    entity=entity,
                )

                if columns_table:
                    return columns_table

            if entity in ChatApiDelpiResponseProfileService.LMP_PRESENT_ENTITIES:
                items = root.get("items")

                if isinstance(items, list) and items and isinstance(items[0], dict):
                    if "sale_number" in items[0] or "saleNumber" in items[0]:
                        return self._host._build_lmp_table(items, root)

            if (
                entity in ChatApiDelpiResponseProfileService.PLAYBOOK_OPERATIONAL_ENTITIES
                and isinstance(root, dict)
            ):
                return self._host._build_playbook_report_table(
                    root,
                    effective_path,
                    entity=entity,
                )

            return None

    def _build_factory_status_table(self, root: dict, path: str) -> dict:
            product = root.get("product") if isinstance(root.get("product"), dict) else {}
            code = str(product.get("product_code") or product.get("code") or "").strip()
            columns = self._host._column_labels.kv_table_column_defs()
            rows = [
                {
                    "campo": "Status fabril",
                    "valor": str(root.get("factory_status") or "—"),
                },
                {
                    "campo": "Produto",
                    "valor": f"{code} — {product.get('description', '')}".strip(" —"),
                },
            ]

            indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

            rows.extend(
                _OpsTable.summary_kv_rows(
                    self._host.column_label_context,
                    dict(list(indicators.items())[:8]),
                    path=path,
                    profile_name="factoryStatusOverview",
                )
            )

            title = (
                self._host._route_presentation("factoryStatus", "titleWithCode", code=code)
                if code
                else self._host._route_presentation("factoryStatus", "titleGeneric")
            )

            return {
                "type": "table",
                "title": title,
                "columns": columns,
                "rows": rows,
            }

    def _build_presentation(self, data, *, path: str = "") -> dict | None:
            from app.domain.services.chat_product_operational_content_service import (
                ChatProductOperationalContentService,
            )

            root = self._host._unwrap_data(data)

            if isinstance(root, list) and root and isinstance(root[0], dict):
                sql_title = ExternalActionResponseContentService.get("sql", "defaultTitle")
                return self._build_items_table_for_path(
                    root,
                    title=sql_title,
                    path=path,
                    role="list",
                )

            if not isinstance(root, dict):
                return None

            product = root.get("product")
            if isinstance(product, dict):
                detail_list = self._host._extract_product_detail_list(root)

                if detail_list:
                    return self._build_product_detail_table(product, detail_list, root)

                if "/analyser" in str(path or "").lower():
                    guide_table = self._host._build_product_analyser_guide_table(root)

                    if guide_table:
                        return guide_table

                    return self._host._build_product_analyser_profile_table(product, root, path=path)

                return self._build_product_table(product, root, path=path)

            if isinstance(root.get("root"), dict) and isinstance(root.get("items"), list):
                lowered = str(path or "").lower()

                if "/structure" in lowered or "/parents" in lowered:
                    return None

                if "/parents" not in lowered:
                    structure_table = self._host._build_analyser_structure_components_table(root)

                    if structure_table:
                        return structure_table

            items = root.get("items")
            if isinstance(items, list) and items and isinstance(items[0], dict):
                lowered_items = str(path or "").lower()

                if "/inspection" in lowered_items or self._host._looks_like_inspection_item(items[0]):
                    inspection_table = self._host._build_inspection_items_table(items, path=path)

                    if inspection_table:
                        return inspection_table

                if "sale_number" in items[0] or "saleNumber" in items[0]:
                    return self._host._build_lmp_table(items, root)

                lowered_items_path = str(path or "").lower()

                if (
                    "order_number" in items[0]
                    and "/production/" not in lowered_items_path
                    and not ChatApiDelpiResponseProfileService.is_playbook_operational_path(path)
                ):
                    return self._build_sale_orders_table(items, root)

                title = self._host._infer_items_title(items, path)

                if "code" in items[0] and "description" in items[0]:
                    if len(items) >= 3:
                        return self._build_product_search_table(items, root, title=title)
                    return self._build_product_search_table(items, root, title=title)

                if len(items) >= 2 or self._host._is_tabular_data(items[0]):
                    return self._build_items_table_for_path(
                        items,
                        title=title,
                        path=path,
                    )

                return None

            stock = root.get("stock")
            if isinstance(stock, dict) and isinstance(stock.get("items"), list):
                stock_title = self._host._path_fragment_title("/stock") or ChatProductOperationalContentService.get(
                    "presenter",
                    "stock",
                    "titleDefault",
                )
                return self._build_items_table_for_path(
                    stock.get("items") or [],
                    title=stock_title,
                    path=path,
                    entity="product_stock",
                    role="stock",
                )

            parents = root.get("parents")
            if isinstance(parents, list) and parents:
                parents_title = (
                    self._host._path_fragment_title("/parents")
                    or ChatProductOperationalContentService.get(
                        "presenter",
                        "parents",
                        "titleGeneric",
                    )
                )
                return self._build_items_table_for_path(
                    parents,
                    title=parents_title,
                    path=path,
                    entity="product_parents",
                    role="structure",
                )

            structure = root.get("structure")
            if isinstance(structure, dict) and isinstance(structure.get("items"), list):
                structure_title = self._host._path_fragment_title("/structure")
                return self._build_items_table_for_path(
                    structure["items"],
                    title=structure_title or self._host._path_fragment_title("structure"),
                    path=path,
                    entity="product_structure",
                    role="structure",
                )

            stock_value_table = self._host._build_stock_value_branch_table(root, path)

            if stock_value_table:
                return stock_value_table

            billing_table = self._host._build_product_billing_table(root, path)

            if billing_table:
                return billing_table

            columns_table = self._host._build_system_columns_table(root, path)

            if columns_table:
                return columns_table

            if isinstance(root.get("resultsets"), list):
                rows = self._host._collect_sql_resultset_rows(root.get("resultsets") or [])
                title = self._host._sql_result_title(root, path)

                if rows:
                    return self._build_items_table_for_path(
                        rows,
                        title=title,
                        path=path,
                        role="list",
                    )

                if self._host._looks_like_inventory_below_minimum_sql_context(root, path):
                    empty_table = self._host._build_sql_resultset_empty_table(
                        root,
                        title=title,
                        path=path,
                    )

                    if empty_table:
                        return empty_table

            return None

    def _build_product_table(self, product: dict, root: dict, *, path: str = "") -> dict:
        columns = self._host._column_labels.kv_table_column_defs()
        rows = self._host._column_labels.build_kv_profile_rows(
            product,
            skip_empty=False,
            schema_labels=self._host._active_schema_labels,
            path=path,
            profile_name="productProfileStandard",
        )
        rows = [row for row in rows if row.get("valor") is not None]

        for key in ("guide", "inspection", "structure", "customers", "suppliers"):
            value = root.get(key)
            if isinstance(value, dict) and value.get("total") is not None:
                rows.append(
                    {
                        "campo": self._host._label_collection(key),
                        "valor": self._host._column_labels.format_collection_total(value["total"]),
                    }
                )

        code = str(product.get("code") or "").strip()

        return {
            "type": "table",
            "title": self._host._presenter_root_format("productProfileTableTitle", code=code),
            "columns": columns,
            "rows": rows,
        }

    def _build_product_detail_table(self, product: dict, detail_list: list, root: dict) -> dict:
            code = product.get("code", "")
            title = self._host._product_detail_title(code, root)

            all_keys = {}
            for item in detail_list:
                for k in item:
                    if k not in all_keys:
                        all_keys[k] = True

            columns = [self._host._enrich_column(k, self._host._humanize_key(k)) for k in all_keys]
            rows = detail_list

            return {
                "type": "table",
                "title": title,
                "columns": columns,
                "rows": rows,
            }

    def _build_sale_orders_table(self, items: list, root: dict) -> dict:
            rows = [item for item in items if isinstance(item, dict)]

            table = self._host._build_profile_items_table(
                rows,
                profile_name="saleOrders",
                title=self._host._route_presentation(
                    "tableTitles",
                    "saleOrders",
                    total=str(root.get("total", len(rows))),
                ),
                role="generic",
                path="/sales",
            )

            if table:
                return table

            return {
                "type": "table",
                "title": self._host._route_presentation(
                    "tableTitles",
                    "saleOrders",
                    total=str(root.get("total", len(rows))),
                ),
                "columns": [],
                "rows": [],
            }

    def _flatten_nested_field(self, items: list) -> list:
            """Converte campos complexos (list/dict) em texto legível para tabela."""
            flattened = []
            for item in items:
                if not isinstance(item, dict):
                    flattened.append(item)
                    continue
                row = {}
                for k, v in item.items():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        codes = [sub.get("code") or sub.get("description") or str(sub) for sub in v[:5]]
                        row[k] = " → ".join(codes)
                        if len(v) > 5:
                            row[k] += f" (+{len(v) - 5})"
                    elif isinstance(v, dict):
                        row[k] = v.get("code") or v.get("description") or str(v)
                    else:
                        row[k] = v
                flattened.append(row)
            return flattened

    def _build_product_search_table(self, items: list, root: dict, *, title: str | None = None) -> dict:
            table_title = title or self._host._presenter_root_format(
                "productSearchTableTitle",
                total=str(root.get("total", len(items))),
            )
            first = items[0] if items else {}
            has_extra = any(k in first for k in ("quantity", "level", "lot_quantity"))

            if has_extra:
                rows = self._flatten_nested_field(items)
                table = self._host._build_profile_items_table(
                    rows,
                    title=table_title,
                    role="generic",
                    path="/products/search",
                )
            else:
                table = self._host._build_profile_items_table(
                    [item for item in items if isinstance(item, dict)],
                    profile_name="productSearchBasic",
                    title=table_title,
                    role="generic",
                    path="/products/search",
                )

            if table:
                return table

            return {
                "type": "table",
                "title": table_title,
                "columns": [],
                "rows": [],
            }

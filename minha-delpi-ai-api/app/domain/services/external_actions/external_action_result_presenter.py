import re

from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.domain.services.external_actions.external_action_sql_capability_service import (
    ExternalActionSqlCapabilityService,
)
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.chat_api_delpi_response_profile_service import (
    ApiDelpiResponseProfile,
    ChatApiDelpiResponseProfileService,
)
from app.domain.services.external_actions.presenters.kpi_chart_presenter import (
    ExternalActionKpiChartPresenter,
)

from app.domain.services.external_actions.presenters.product_analyser_presenter import (
    ExternalActionProductAnalyserPresenter,
)
from app.domain.services.external_actions.presenters.product_list_presenter import (
    ExternalActionProductListPresenter,
)

from app.domain.services.external_actions.presenters.sql_presenter import (
    ExternalActionSqlPresenter,
)

from app.domain.services.external_actions.presenters.billing_presenter import (
    ExternalActionBillingPresenter,
)
from app.domain.services.external_actions.presenters.system_tables_presenter import (
    ExternalActionSystemTablesPresenter,
)


class ExternalActionResultPresenter:
    def __init__(
        self,
        column_label_service: ExternalActionColumnLabelService | None = None,
    ):
        self._column_labels = column_label_service or ExternalActionColumnLabelService()
        self._active_schema_labels: dict[str, str] | None = None
        self._active_schema_formats: dict[str, str] | None = None
        self._kpi_chart_presenter: ExternalActionKpiChartPresenter | None = None
        self._product_analyser_presenter: ExternalActionProductAnalyserPresenter | None = None
        self._product_list_presenter: ExternalActionProductListPresenter | None = None
        self._sql_presenter: ExternalActionSqlPresenter | None = None
        self._billing_presenter: ExternalActionBillingPresenter | None = None
        self._system_tables_presenter: ExternalActionSystemTablesPresenter | None = None

    def _kpi_chart(self) -> ExternalActionKpiChartPresenter:
        if self._kpi_chart_presenter is None:
            self._kpi_chart_presenter = ExternalActionKpiChartPresenter(self)

        return self._kpi_chart_presenter

    def _analyser(self) -> ExternalActionProductAnalyserPresenter:
        if self._product_analyser_presenter is None:
            self._product_analyser_presenter = ExternalActionProductAnalyserPresenter(self)

        return self._product_analyser_presenter

    def _product_list(self) -> ExternalActionProductListPresenter:
        if self._product_list_presenter is None:
            self._product_list_presenter = ExternalActionProductListPresenter(self)

        return self._product_list_presenter


    def _sql(self) -> ExternalActionSqlPresenter:
        if self._sql_presenter is None:
            self._sql_presenter = ExternalActionSqlPresenter(self)

        return self._sql_presenter


    def _billing(self) -> ExternalActionBillingPresenter:
        if self._billing_presenter is None:
            self._billing_presenter = ExternalActionBillingPresenter(self)

        return self._billing_presenter

    def _system_tables(self) -> ExternalActionSystemTablesPresenter:
        if self._system_tables_presenter is None:
            self._system_tables_presenter = ExternalActionSystemTablesPresenter(self)

        return self._system_tables_presenter

    def present(self, data, *, path: str = "") -> dict:
        previous_labels = self._active_schema_labels
        previous_formats = self._active_schema_formats
        self._active_schema_labels = self._column_labels.merge_meta_field_labels(
            {},
            data,
        )
        self._active_schema_formats = self._column_labels.merge_meta_field_formats(
            {},
            data,
        )

        try:
            profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
            routed = self._present_entity_first(data, path=path, profile=profile)

            if routed is not None:
                return routed

            return self._present_legacy(data, path=path)
        finally:
            self._active_schema_labels = previous_labels
            self._active_schema_formats = previous_formats

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

        error = self._detect_api_error(data, path=path)

        if error:
            return error

        root = self._unwrap_data(data)

        empty_operational = self._present_empty_operational_result(
            path=path,
            root=root,
        )

        if empty_operational:
            return empty_operational

        if entity == "product_analyser" and isinstance(root, dict):
            root = self._normalize_analyser_root(root)
            product = root.get("product")

            if isinstance(product, dict):
                return self._present_product_analyser(
                    root,
                    self._normalize_api_section(product),
                    path,
                )

        if entity == "product_factory_status" and isinstance(root, dict):
            return self._present_product_factory_status(root, path)

        if entity == "product_structure" and isinstance(root, dict):
            structure_result = self._present_product_structure(root, path)

            if structure_result:
                return structure_result

        if entity == "product_parents" and isinstance(root, dict):
            structure_result = self._present_product_structure(root, path)

            if structure_result:
                return structure_result

        product = root.get("product") if isinstance(root, dict) else None

        if entity == "product" and isinstance(product, dict):
            return self._present_product(root, self._normalize_api_section(product))

        if isinstance(root, dict):
            items = root.get("items")

            if isinstance(items, list) and items:
                title = self._infer_items_title(items, path)
                first_item = items[0] if isinstance(items[0], dict) else {}

                if entity == "product_stock" or self._is_stock_data(first_item):
                    return self._present_product_stock(items, path=path, title=title)

                if entity == "product_guide" or (
                    isinstance(first_item, dict)
                    and (
                        "operation_description" in first_item
                        or "operation_code" in first_item
                    )
                ):
                    return self._present_product_guide(items, path=path, title=title)

                if entity == "product_inspection" or self._looks_like_inspection_item(
                    first_item
                ):
                    return self._present_product_inspection(items, path=path, title=title)

                if entity == "product_search" and isinstance(first_item, dict) and (
                    "code" in first_item and "description" in first_item
                ):
                    return self._present_product_search(root, items, title=title)

                path_routed = self._present_path_routed_items(root, path)

                if path_routed:
                    return path_routed

        if entity in {
            "product_production_status",
            "product_shipping_status",
            "product_structure_exclusivity",
        } and isinstance(root, dict):
            fallback = self._present_playbook_report(root, path, entity=entity)

            if fallback:
                return fallback

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
            billing = self._present_product_billing_summary(
                root,
                effective_path,
                entity=entity,
            )

            if billing:
                return billing

        if entity == "product_pricing" and isinstance(root, dict):
            prices = root.get("prices")

            if isinstance(prices, list) and prices:
                title = self._infer_items_title(prices, effective_path)

                return self._present_items(
                    prices,
                    title=title or self._presenter_text("productDetailTitles", "prices", code=""),
                )

            pricing_fallback = self._present_dict_fallback(root, effective_path)

            if pricing_fallback:
                return pricing_fallback

        if entity in ChatApiDelpiResponseProfileService.PRODUCT_LIST_PRESENT_ENTITIES:
            items = root.get("items") if isinstance(root, dict) else None

            if isinstance(items, list):
                if not items:
                    title = self._infer_items_title([], effective_path) or self._presenter_text(
                        "generic",
                        "defaultQueryTitle",
                    )
                    return {
                        "titulo": title,
                        "linhas": [
                            self._presenter_text("generic", "emptyItemsQuery")
                        ],
                        "dados": root,
                    }

                if entity == "product_open_orders":
                    return self._present_items(
                        items,
                        title=self._infer_items_title(items, effective_path),
                    )

                title = self._infer_items_title(items, effective_path)
                return self._present_items(items, title=title)

        if entity == "product_sales" and isinstance(root, dict):
            kpi = self._present_kpi_response(root, effective_path, entity=entity)

            if kpi:
                return kpi

        if ChatApiDelpiResponseProfileService.is_kpi_entity(entity) and isinstance(root, dict):
            specialized = (
                self._present_stock_value_summary(root, effective_path, entity=entity)
                or self._present_financial_pmr(root, effective_path, entity=entity)
            )

            if specialized:
                return specialized

            kpi = self._present_kpi_response(root, effective_path, entity=entity)

            if kpi:
                return kpi

        if entity in ChatApiDelpiResponseProfileService.LMP_PRESENT_ENTITIES and isinstance(
            root, dict
        ):
            lmp_page = self._present_lmp_page(root)

            if lmp_page:
                return lmp_page

            lmp_detail = self._present_lmp_detail(root)

            if lmp_detail:
                return lmp_detail

        if entity in ChatApiDelpiResponseProfileService.SALE_ORDER_PRESENT_ENTITIES:
            items = root.get("items") if isinstance(root, dict) else None

            if isinstance(items, list) and items:
                return self._present_sale_orders(root, items)

        if entity in ChatApiDelpiResponseProfileService.SQL_PRESENT_ENTITIES:
            sql_resultsets = self._present_sql_resultsets(root, effective_path)

            if sql_resultsets:
                return sql_resultsets

            sql_rows = self._present_sql_rows(root)

            if sql_rows:
                return sql_rows

        if entity in ChatApiDelpiResponseProfileService.SYSTEM_PRESENT_ENTITIES and isinstance(
            root, dict
        ):
            system = (
                self._present_system_tables_search(root, effective_path, entity=entity)
                or self._present_system_table_columns(root, effective_path, entity=entity)
            )

            if system:
                return system

            system_fallback = self._present_dict_fallback(root, effective_path)

            if system_fallback:
                return system_fallback

        if entity == "commercial_proposal" and isinstance(root, dict):
            items = root.get("items")

            if isinstance(items, list):
                title = self._infer_items_title(items, effective_path)
                return self._present_items(items, title=title)

        if entity == "eficiencia_fabril_appointment" and isinstance(root, dict):
            items = root.get("items")

            if isinstance(items, list) and items:
                title = self._infer_items_title(items, effective_path)
                return self._present_items(items, title=title)

        return None

    def _present_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> dict | None:
        return self._kpi_chart().present_kpi_response(root, path, entity=entity)

    def _present_legacy(self, data, *, path: str = "") -> dict:
        error = self._detect_api_error(data, path=path)
        if error:
            return error

        root = self._unwrap_data(data)

        empty_operational = self._present_empty_operational_result(
            path=path,
            root=root,
        )

        if empty_operational:
            return empty_operational

        if isinstance(root, dict) and "/analyser" in str(path or "").lower():
            root = self._normalize_analyser_root(root)

        product = root.get("product") if isinstance(root, dict) else None

        if isinstance(product, dict):
            product = self._normalize_api_section(product)

            if "/analyser" in str(path or "").lower():
                return self._present_product_analyser(root, product, path)

            return self._present_product(root, product)

        if isinstance(root, dict):
            lmp_page = self._present_lmp_page(root)

            if lmp_page:
                return lmp_page

            lmp_detail = self._present_lmp_detail(root)

            if lmp_detail:
                return lmp_detail

            path_routed = self._present_path_routed_items(root, path)

            if path_routed:
                return path_routed

            if not self._is_product_operational_path(path):
                sql_resultsets = self._present_sql_resultsets(root, path)

                if sql_resultsets:
                    return sql_resultsets

        if isinstance(root, list) and root:
            if self._is_product_operational_path(path):
                path_routed = self._present_path_routed_items({"items": root}, path)

                if path_routed:
                    return path_routed

            sql_result = self._present_sql_rows(root)

            if sql_result:
                return sql_result

        if isinstance(root, dict) and "/structure" in str(path or "").lower():
            structure_result = self._present_product_structure(root, path)

            if structure_result:
                return structure_result

        if isinstance(root, dict):
            specialized = (
                self._present_stock_value_summary(root, path)
                or self._present_product_billing_summary(root, path)
                or self._present_financial_pmr(root, path)
                or self._present_system_tables_search(root, path)
                or self._present_system_table_columns(root, path)
            )

            if specialized:
                return specialized

        items = root.get("items") if isinstance(root, dict) else None

        if isinstance(items, list):
            if not items:
                title = self._infer_items_title([], path) or self._presenter_text(
                    "generic", "defaultQueryTitle"
                )
                return {
                    "titulo": title,
                    "linhas": [
                        self._presenter_text("generic", "emptyItemsQuery")
                    ],
                    "dados": root,
                }

            if items and isinstance(items[0], dict) and "sale_number" in items[0]:
                return self._present_lmp_page(root)

            if items and isinstance(items[0], dict) and "order_number" in items[0]:
                return self._present_sale_orders(root, items)

            title = self._infer_items_title(items, path)
            lowered_path = str(path or "").lower()
            first_item = items[0] if items and isinstance(items[0], dict) else {}

            if "/stock" in lowered_path or self._is_stock_data(first_item):
                return self._present_product_stock(items, path=path, title=title)

            if "/inspection" in lowered_path or self._looks_like_inspection_item(first_item):
                return self._present_product_inspection(items, path=path, title=title)

            if items and isinstance(items[0], dict) and "code" in items[0] and "description" in items[0]:
                return self._present_product_search(root, items, title=title)

            if items and isinstance(items[0], dict) and (
                "operation_description" in items[0] or "operation_code" in items[0]
            ):
                return self._present_product_guide(items, path=path, title=title)

            return self._present_items(items, title=title)

        if isinstance(root, dict) and self._looks_like_kpi_response(root, path):
            kpi = self._present_kpi_response(root, path)

            if kpi:
                return kpi

        if isinstance(root, dict) and root:
            fallback = self._present_dict_fallback(root, path)
            if fallback:
                return fallback

        return {
            "titulo": self._fallback_title(path)
            or self._presenter_text("generic", "apiResultTitle"),
            "linhas": [self._presenter_text("generic", "apiAuthorized")],
            "dados": root,
        }

    def _fallback_title(self, path: str) -> str | None:
        if not path:
            return None

        lowered = path.lower()
        triggers = (
            "dashboard",
            "/commercial/",
            "/financial/",
            "/finacial/",
            "/production/",
            "/hr/",
            "/quality/",
        )

        if not any(fragment in lowered for fragment in triggers):
            return None

        return self._kpi_title(path)

    def _present_dict_fallback(self, root: dict, path: str) -> dict | None:
        if not root:
            return None

        linhas = []
        title = self._fallback_title(path) or self._presenter_text(
            "generic", "queryResultTitle"
        )

        for key, value in root.items():
            if isinstance(value, dict):
                sub_items = [
                    self._presenter_text(
                        "generic",
                        "dictNestedValue",
                        key=str(nested_key),
                        value=str(nested_value),
                    )
                    for nested_key, nested_value in value.items()
                ]
                linhas.append(
                    self._presenter_text(
                        "generic",
                        "dictNestedLine",
                        label=self._humanize_key(key),
                        items=", ".join(sub_items),
                    )
                )
            elif isinstance(value, list) and value:
                linhas.append(
                    self._presenter_text(
                        "generic",
                        "dictListItems",
                        label=self._humanize_key(key),
                        count=str(len(value)),
                    )
                )
            elif value is not None:
                linhas.append(
                    self._presenter_text(
                        "generic",
                        "dictScalarLine",
                        label=self._humanize_key(key),
                        value=self._format_field_value(key, value),
                    )
                )

        if linhas:
            return {
                "titulo": title,
                "linhas": linhas[:12],
                "dados": root,
            }

        return None

    def _extract_product_code_from_path(self, path: str) -> str:
        match = re.search(r"/products/(\d+)/", str(path or ""), flags=re.IGNORECASE)

        if match:
            return match.group(1)

        return ""

    def _present_empty_operational_result(self, *, path: str, root) -> dict | None:
        if not self._is_product_operational_path(path):
            return None

        if not self._is_empty_operational_payload(root):
            return None

        lowered_path = str(path or "").lower()
        product_code = self._extract_product_code_from_path(path)

        route_key = None

        if "/suppliers" in lowered_path:
            route_key = "suppliers"
        elif "/customers" in lowered_path:
            route_key = "customers"
        elif "/stock" in lowered_path:
            route_key = "stock"
        elif "/structure" in lowered_path:
            route_key = "structure"
        elif "/parents" in lowered_path:
            route_key = "parents"
        elif "/guide" in lowered_path:
            route_key = "guide"
        elif "/inspection" in lowered_path:
            route_key = "inspection"
        elif "/sales" in lowered_path or "/purchases" in lowered_path:
            route_key = "salesPurchases"

        if route_key and product_code:
            linha = self._presenter_text(
                "operationalEmpty", route_key, code=product_code
            )
        elif route_key:
            linha = self._presenter_text("operationalEmpty", f"{route_key}Generic")
        else:
            linha = self._presenter_text("operationalEmpty", "default")

        titulo = self._infer_items_title([], path) or self._presenter_text(
            "generic", "defaultQueryTitle"
        )

        return {
            "titulo": titulo,
            "linhas": [linha],
            "dados": {
                "items": [],
                "total": 0,
                "product_code": product_code or None,
            },
        }

    @staticmethod
    def _is_empty_operational_payload(root) -> bool:
        if isinstance(root, list):
            return len(root) == 0

        if not isinstance(root, dict):
            return False

        total = root.get("total")

        if total == 0:
            return True

        items = root.get("items")

        if isinstance(items, list) and not items:
            return True

        nested = root.get("data")

        if isinstance(nested, list) and not nested:
            return True

        if isinstance(nested, dict) and nested.get("total") == 0:
            inner = nested.get("data") or nested.get("items")

            if inner is None or inner == []:
                return True

        return False

    def _format_protheus_date(self, value) -> str | None:
        raw = str(value or "").strip()

        if len(raw) != 8 or not raw.isdigit():
            return raw or None

        return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"

    def _format_currency(self, value) -> str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)

        formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return formatted

    def _kpi_cards_to_linhas(self, kpi: dict) -> list[str]:
        return self._kpi_chart().kpi_cards_to_linhas(kpi)










    def _path_fragment_title(self, fragment: str) -> str | None:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        key = str(fragment or "").strip()
        if not key:
            return None

        if not key.startswith("/"):
            key = f"/{key}"

        return ChatAssistantContentService.get(
            "presenter_content",
            "titlesByPathFragment",
            key,
        ) or ChatAssistantContentService.get(
            "presenter_content",
            "titlesByPathFragment",
            key.lstrip("/"),
        )


    def _is_product_operational_path(cls, path: str) -> bool:
        lowered = str(path or "").lower()

        return any(
            segment in lowered
            for segment in (
                "/guide",
                "/inspection",
                "/stock",
                "/structure",
                "/parents",
                "/purchases",
                "/sales",
                "/suppliers",
                "/customers",
            )
        )


    def _detect_api_error(self, data, *, path: str = "") -> dict | None:
        if not isinstance(data, dict):
            return None

        detail = data.get("detail") or data.get("error") or data.get("message")
        status = data.get("status_code") or data.get("status")

        is_error_detail = isinstance(detail, str) and detail.lower() in (
            "not found", "unauthorized", "forbidden", "internal server error",
            "bad request", "service unavailable",
        )

        is_error_status = isinstance(status, int) and status >= 400

        if not is_error_detail and not is_error_status:
            if isinstance(data.get("success"), bool) and not data["success"]:
                from app.domain.services.chat_sql_execution_error_interpretation_service import (
                    ChatSqlExecutionErrorInterpretationService,
                )

                raw_msg = str(
                    data.get("message")
                    or self._presenter_text("apiErrors", "unknown")
                )
                friendly = ChatSqlExecutionErrorInterpretationService.user_facing_message(
                    raw_msg,
                    path=path,
                )
                msg = friendly or raw_msg

                if ChatSqlExecutionErrorInterpretationService.is_raw_driver_dump(raw_msg):
                    msg = friendly or self._analyser_markdown("sqlEnvironmentFailed")

                return {
                    "titulo": self._presenter_text("generic", "queryErrorTitle"),
                    "linhas": [msg],
                    "dados": None,
                }
            return None

        if isinstance(detail, str):
            error_key_map = {
                "not found": "notFound",
                "unauthorized": "unauthorized",
                "forbidden": "forbidden",
            }
            mapped = error_key_map.get(detail.lower())
            msg = (
                self._presenter_text("apiErrors", mapped)
                if mapped
                else self._presenter_text("apiErrors", "withDetail", detail=detail)
            )
        else:
            msg = self._presenter_text("apiErrors", "withStatus", status=str(status))

        return {
            "titulo": self._presenter_text("generic", "queryErrorTitle"),
            "linhas": [msg],
            "dados": None,
        }

    def _unwrap_data(self, data):
        root = data

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        if isinstance(root, dict) and "data" in root:
            root = root["data"]

        return root

    def _normalize_api_section(self, block, *, _depth: int = 0):
        """Desembrulha blocos `{ success, data }` retornados pela API DELPI."""
        if not isinstance(block, dict):
            return block

        inner = block.get("data")

        if inner is None and "success" not in block and "total" not in block:
            return block

        if isinstance(inner, list):
            normalized: dict = {"items": inner}
            total = block.get("total")

            if total is not None:
                normalized["total"] = total

            return normalized

        if isinstance(inner, dict):
            merged = dict(inner)

            for key in ("total", "page", "page_size", "total_pages", "filters", "success"):
                if key in block and key not in merged:
                    merged[key] = block[key]

            if "components" in merged and "items" not in merged:
                components = merged.get("components")

                if isinstance(components, list):
                    merged["items"] = components

            if merged.get("code") and "root" not in merged:
                merged.setdefault(
                    "root",
                    {
                        "code": merged.get("code"),
                        "description": merged.get("description"),
                        "type": merged.get("type"),
                        "unit": merged.get("unit"),
                        "quantity": merged.get("quantity", 1),
                    },
                )

            if (
                _depth < 4
                and isinstance(merged.get("data"), dict)
                and not str(merged.get("code") or "").strip()
            ):
                return self._normalize_api_section(merged, _depth=_depth + 1)

            return merged

        return block


    def _overview_missing(self) -> str:
        return self._presenter_text("productOverview", "missingValue")

    def _build_product_overview_narrative_lines(self, product: dict, root: dict) -> list[str]:
        code = str(product.get("code") or "").strip()
        description = str(product.get("description") or "").strip()
        product_type = str(product.get("type") or "").strip()
        unit = str(product.get("unit") or "").strip()
        group_code = str(product.get("group_code") or "").strip()
        active = str(product.get("active") or "").strip()
        warehouse = str(product.get("default_warehouse") or "").strip()
        missing = self._overview_missing()

        lines = [
            self._presenter_text(
                "productOverview",
                "identityLine",
                code=code,
                description=description
                or self._presenter_text("productOverview", "noDescription"),
            ),
            self._presenter_text(
                "productOverview",
                "classificationLine",
                type=product_type or missing,
                unit=unit or missing,
                group_code=group_code or missing,
            ),
            self._presenter_text("productOverview", "cadastralActive", active=active or missing)
            + (
                self._presenter_text(
                    "productOverview",
                    "cadastralWarehouseSuffix",
                    warehouse=warehouse,
                )
                if warehouse
                else self._presenter_text("productOverview", "cadastralEnd")
            ),
        ]

        purchase_price = product.get("last_purchase_price")
        purchase_date = str(product.get("last_purchase_date") or "").strip()
        standard_cost = product.get("standard_cost")

        if purchase_price in (0, 0.0, None) and not purchase_date:
            lines.append(self._analyser_markdown("noRecentPurchase"))
        else:
            price_text = self._format_currency(purchase_price)
            date_text = self._format_revision_date(purchase_date) if purchase_date else ""
            date_suffix = (
                self._presenter_text(
                    "productOverview",
                    "lastPurchaseDateSuffix",
                    date=date_text,
                )
                if date_text
                else ""
            )
            lines.append(
                self._presenter_text(
                    "productOverview",
                    "lastPurchase",
                    price=price_text,
                    date_suffix=date_suffix,
                )
            )

        if standard_cost not in (None, ""):
            lines.append(
                self._analyser_markdown(
                    "standardCost",
                    cost=self._format_currency(standard_cost),
                )
            )

        revision = str(product.get("last_revision_date") or "").strip()
        ncm = str(product.get("ncm_ipi_position") or "").strip()

        if revision:
            lines.append(
                self._presenter_text(
                    "productOverview",
                    "revisionLine",
                    revision=self._format_revision_date(revision),
                )
            )

        if ncm:
            lines.append(
                self._presenter_text("productOverview", "ncmLine", ncm=ncm)
            )

        blocked = str(product.get("blocked") or "").strip()
        if blocked and blocked not in {"N", "0", ""}:
            lines.append(
                self._presenter_text(
                    "productOverview",
                    "blockedLine",
                    blocked=blocked,
                )
            )

        for key in ["guide", "inspection", "structure", "customers", "suppliers"]:
            value = root.get(key)
            if isinstance(value, dict):
                total = value.get("total")
                if total is not None:
                    label = self._label_collection(key)
                    from app.domain.services.chat_product_operational_content_service import (
                        ChatProductOperationalContentService,
                    )

                    if int(total or 0) == 0:
                        lines.append(
                            ChatProductOperationalContentService.format(
                                "presenter",
                                "profile",
                                "collectionEmpty",
                                label=label,
                            )
                        )
                    else:
                        lines.append(
                            ChatProductOperationalContentService.format(
                                "presenter",
                                "profile",
                                "collectionWithTotal",
                                label=label,
                                total=total,
                            )
                        )

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        lines.append(
            ChatProductOperationalContentService.get("presenter", "profile", "nextStepsHint")
        )

        return lines

    def _format_revision_date(self, token: str) -> str:
        raw = str(token or "").strip()

        if len(raw) == 8 and raw.isdigit():
            return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"

        return raw

    def _present_product(self, root: dict, product: dict) -> dict:
        product_summary = {
            "code": product.get("code"),
            "description": product.get("description"),
            "type": product.get("type"),
            "unit": product.get("unit"),
            "groupCode": product.get("group_code"),
            "active": product.get("active"),
            "defaultWarehouse": product.get("default_warehouse"),
            "lastPurchasePrice": product.get("last_purchase_price"),
            "standardCost": product.get("standard_cost"),
            "lastRevisionDate": product.get("last_revision_date"),
            "ncm": product.get("ncm_ipi_position"),
        }

        detail_list = self._extract_product_detail_list(root)

        if detail_list:
            return self._present_product_with_details(product_summary, detail_list, root)

        linhas = self._build_product_overview_narrative_lines(product, root)

        return {
            "titulo": self._presenter_text(
                "productPresentationTitles",
                "overviewWithCode",
                code=str(product_summary["code"]),
            ),
            "linhas": [line for line in linhas if "None" not in line],
            "campos": self._alias_dict(product_summary),
            "dados": {
                "product": product_summary,
                "guideTotal": self._total(root.get("guide")),
                "inspectionTotal": self._total(root.get("inspection")),
                "structureTotal": self._total(root.get("structure")),
            },
        }


























    def _extract_product_detail_list(self, root: dict) -> list | None:
        detail_keys = (
            "prices", "stock", "purchases", "sales", "billing",
            "suppliers", "customers", "movements", "invoices",
            "open_orders", "items",
        )
        for key in detail_keys:
            value = root.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return None

    def _format_detail_preview_line(self, item: dict) -> str:
        parts: list[str] = []

        for key, value in list(item.items())[:8]:
            if value is None:
                continue

            label = self._humanize_key(key)

            if key in {
                "sale_price",
                "max_price",
                "discount_value",
                "last_price",
                "last_purchase_price",
                "standard_cost",
            }:
                parts.append(f"{label}: {self._format_currency(value)}")
            elif key == "discount_percent":
                parts.append(f"{label}: {self._format_num(value)}%")
            elif key in {
                "current_quantity",
                "available_quantity",
                "committed_quantity",
                "reserved_quantity",
                "lot_quantity",
            }:
                parts.append(f"{label}: {self._format_num(value)}")
            else:
                parts.append(f"{label}: {value}")

        return ", ".join(parts) if parts else "—"

    def _present_product_with_details(
        self, product_summary: dict, detail_list: list, root: dict
    ) -> dict:
        code = product_summary.get("code") or ""
        desc = product_summary.get("description") or ""

        linhas = [
            self._presenter_text(
                "productWithDetails",
                "introLine",
                code=str(code),
                description=str(desc),
            )
        ]

        for item in detail_list[:5]:
            preview = self._format_detail_preview_line(item)
            linhas.append(f"- {preview}")

        if len(detail_list) > 5:
            linhas.append(
                self._presenter_text(
                    "pagination",
                    "moreDetailRecords",
                    count=str(len(detail_list) - 5),
                )
            )

        all_keys = {}
        for item in detail_list:
            for k in item:
                if k not in all_keys:
                    all_keys[k] = True

        columns = [self._enrich_column(k, self._humanize_key(k)) for k in all_keys]
        rows = detail_list

        title = self._product_detail_title(code, root)

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": {"product": product_summary, "items": rows},
            "apresentacao": {
                "type": "table",
                "title": title,
                "columns": columns,
                "rows": rows,
            },
        }
















    def _present_product_structure(self, root: dict, path: str) -> dict | None:
        root_node = root.get("root")

        if not isinstance(root_node, dict):
            return None

        items = root.get("items")

        if not isinstance(items, list):
            return None

        code = str(root_node.get("code") or "").strip()
        description = str(root_node.get("description") or "").strip()
        total = root.get("total")
        level1_count = len(items)

        description = (
            str(description or "").strip()
            or self._route_presentation("structureItems", "noDescription")
        )
        linhas: list[str] = [
            self._route_presentation(
                "structureItems",
                "productLine",
                code=code,
                description=description,
            ),
        ]

        if total is not None:
            linhas.append(
                self._route_presentation(
                    "structureItems", "totalFromApi", total=str(total)
                )
            )
        elif level1_count:
            linhas.append(
                self._route_presentation(
                    "structureItems", "countFromItems", count=str(level1_count)
                )
            )

        mp_codes: set[str] = set()

        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            item_code = str(item.get("code") or "?").strip()
            item_desc = str(item.get("description") or "").strip()
            item_type = str(item.get("type") or "").strip()
            quantity = item.get("quantity")

            if str(item_type).upper() == "MP":
                mp_codes.add(item_code)

            line = self._format_structure_component_line(
                item_code,
                item_desc,
                item_type,
                quantity,
            )

            if line:
                linhas.append(line)

        if level1_count > 10:
            linhas.append(
                self._presenter_text(
                    "pagination",
                    "moreStructureComponents",
                    count=str(level1_count - 10),
                )
            )

        if mp_codes:
            preview = ", ".join(sorted(mp_codes)[:6])
            suffix = "…" if len(mp_codes) > 6 else ""
            linhas.append(
                self._route_presentation(
                    "structureItems",
                    "rawMaterials",
                    count=str(len(mp_codes)),
                    preview=preview,
                    suffix=suffix,
                )
            )

        return {
            "titulo": (
                self._route_presentation("structureItems", "titleWithCode", code=code)
                if code
                else self._route_presentation("structureItems", "titleGeneric")
            ),
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
        }

    def _present_product_factory_status(self, root: dict, path: str) -> dict:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(
            product.get("product_code") or product.get("code") or self._extract_product_code_from_path(path)
        ).strip()
        description = str(product.get("description") or "").strip()
        status = str(root.get("factory_status") or "").strip()
        linhas: list[str] = []

        if status:
            linhas.append(f"Status fabril: {status}")

        if description:
            linhas.append(f"Produto: {code} — {description}")
        elif code:
            linhas.append(f"Produto: {code}")

        indicators = root.get("indicators") if isinstance(root.get("indicators"), dict) else {}

        for key, value in list(indicators.items())[:6]:
            linhas.append(
                f"{self._humanize_key(str(key))}: {self._format_field_value(str(key), value)}"
            )

        structure_summary = (root.get("structure") or {}).get("summary") if isinstance(root.get("structure"), dict) else None

        if isinstance(structure_summary, dict):
            exclusive = structure_summary.get("total_exclusive_raw_materials")

            if exclusive is not None:
                linhas.append(f"MPs exclusivas: {exclusive}")

        return {
            "titulo": f"Status fabril — {code}" if code else "Status fabril do produto",
            "linhas": linhas or [self._presenter_text("generic", "apiAuthorized")],
            "dados": root,
            "sourcePath": path,
        }

    def _present_playbook_report(
        self,
        root: dict,
        path: str,
        *,
        entity: str,
    ) -> dict | None:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(product.get("product_code") or product.get("code") or "").strip()
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else {}
        items = root.get("items") if isinstance(root.get("items"), list) else []
        linhas: list[str] = []

        if summary:
            for key, value in list(summary.items())[:8]:
                linhas.append(
                    f"{self._humanize_key(str(key))}: {self._format_field_value(str(key), value)}"
                )

        if items:
            linhas.append(f"Itens retornados: {len(items)}")

        if not linhas:
            return None

        titles = {
            "product_production_status": "Situação produtiva",
            "product_shipping_status": "Status de expedição",
            "product_structure_exclusivity": "Estrutura com exclusividade",
        }

        title = titles.get(entity, "Relatório do produto")

        if code:
            title = f"{title} — {code}"

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
            "sourcePath": path,
        }




    def _looks_like_inspection_item(self, item: dict) -> bool:
        return any(
            key in item
            for key in (
                "inspection_type",
                "characteristic",
                "specification",
                "has_inspection",
                "measurable_tests",
                "textual_tests",
                "QP6",
                "QP7",
                "QP8",
                "qp6",
                "qp7",
                "qp8",
            )
        )




    def _alias_dict(self, payload: dict) -> dict:
        return {
            self._humanize_key(key): value
            for key, value in payload.items()
            if value is not None
        }

    def _label_collection(self, key: str) -> str:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        labels = ChatProductOperationalContentService.get_mapping(
            "presenter",
            "collections",
            "labels",
        )

        return labels.get(key, key)

    def _total(self, value):
        if isinstance(value, dict):
            return value.get("total")

        return None

    def _collection_is_empty(self, value) -> bool:
        if not isinstance(value, dict):
            return True

        total = value.get("total")

        try:
            if total is not None and int(total) > 0:
                return False
        except (TypeError, ValueError):
            pass

        items = value.get("items")

        if isinstance(items, list) and items:
            return False

        data = value.get("data")

        if isinstance(data, list) and data:
            return False

        return True


    def _build_parents_text_presentation(self, root: dict, path: str) -> dict | None:
        root_node = root.get("root") if isinstance(root.get("root"), dict) else {}
        code = str(root_node.get("code") or "").strip()
        total = root.get("total")
        items = root.get("items") if isinstance(root.get("items"), list) else []
        shown = len(items)

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        title = (
            ChatProductOperationalContentService.format(
                "presenter",
                "parents",
                "titleWithCode",
                code=code,
            )
            if code
            else ChatProductOperationalContentService.get(
                "presenter",
                "parents",
                "titleGeneric",
            )
        )

        description = (
            str(root_node.get("description") or "").strip()
            or self._route_narrative("parents", "noDescription")
        )
        summary_parts = [
            self._route_narrative(
                "parents",
                "productLine",
                code=code,
                description=description,
            ),
        ]

        if total is not None:
            summary_parts.append(
                self._route_narrative(
                    "parents",
                    "totalFound",
                    total=str(total),
                )
            )

            if shown and int(total) > shown:
                summary_parts.append(
                    self._route_narrative(
                        "parents",
                        "pagePartial",
                        shown=str(shown),
                    )
                )
        elif shown:
            summary_parts.append(
                self._route_narrative(
                    "parents",
                    "shownLinks",
                    shown=str(shown),
                )
            )

        if items:
            summary_parts.append(self._route_narrative("parents", "treeAndTable"))
        else:
            summary_parts.append(self._analyser_markdown("parentsEmpty"))

        markdown = "\n\n".join([f"### {title}", "", *summary_parts])

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    def _build_structure_text_presentation(self, root: dict, path: str) -> dict | None:
        root_node = root.get("root") if isinstance(root.get("root"), dict) else {}
        code = str(root_node.get("code") or "").strip()
        total = root.get("total")
        items = root.get("items") if isinstance(root.get("items"), list) else []

        title = (
            self._route_narrative("structure", "titleWithCode", code=code)
            if code
            else self._route_narrative("structure", "titleGeneric")
        )
        description = (
            str(root_node.get("description") or "").strip()
            or self._route_narrative("parents", "noDescription")
        )

        summary_parts = [
            self._route_narrative(
                "structure",
                "productLine",
                code=code,
                description=description,
            ),
        ]

        component_total = total if total is not None else (len(items) if items else None)

        if component_total is not None:
            summary_parts.append(
                self._route_narrative(
                    "structure",
                    "totalComponents",
                    total=str(component_total),
                )
            )

        if items or total:
            summary_parts.append(self._route_narrative("structure", "treeAndTable"))

        markdown = "\n\n".join([f"### {title}", "", *summary_parts])

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    def build_text_presentation(self, data, *, path: str = "") -> dict | None:
        """Markdown legível para a aba Texto do chat (complementa tabela/gráfico)."""
        root = self._unwrap_data(data)
        lowered = str(path or "").lower()

        if isinstance(root, dict) and "/analyser" in lowered:
            root = self._normalize_analyser_root(root)

        if isinstance(root, dict) and isinstance(root.get("product"), dict):
            if "/analyser" in lowered:
                product = self._normalize_api_section(root["product"])

                return self._build_product_analyser_text_presentation(
                    root,
                    product,
                    path,
                )

        if isinstance(root, dict) and "/parents" in lowered:
            from app.domain.services.chat_product_structure_presentation_service import (
                ChatProductStructurePresentationService,
            )

            normalized = ChatProductStructurePresentationService._normalize_parents_payload(
                root
            )

            if normalized is not None:
                root = normalized

        if (
            isinstance(root, dict)
            and isinstance(root.get("root"), dict)
            and isinstance(root.get("items"), list)
        ):
            if "/parents" in lowered:
                return self._build_parents_text_presentation(root, path)

            if "/structure" in lowered:
                return self._build_structure_text_presentation(root, path)

        humanized = self.present(data, path=path)

        if not isinstance(humanized, dict):
            return None

        lines = humanized.get("linhas") or []
        detail_lines = humanized.get("linhas_detalhe") or []
        title = str(humanized.get("titulo") or "").strip()
        summary_parts = [str(line).strip() for line in lines if str(line).strip()]

        if not summary_parts and not title and not detail_lines:
            return None

        markdown_parts: list[str] = []

        if title:
            markdown_parts.append(f"### {title}")

        if "/stock" in lowered and detail_lines:
            markdown_parts.extend(summary_parts)
            markdown_parts.append("**Detalhamento por filial e armazém**")
            markdown_parts.extend(
                f"- {line}" if not str(line).strip().startswith("-") else str(line).strip()
                for line in detail_lines
            )
        else:
            markdown_parts.extend(summary_parts)
            for line in detail_lines:
                cleaned = str(line).strip()

                if cleaned:
                    markdown_parts.append(cleaned)

        markdown = "\n\n".join(markdown_parts).strip()

        if not markdown:
            return None

        return {
            "type": "markdown",
            "title": title
            or self._fallback_title(path)
            or self._presenter_text("generic", "textPresentationFallback"),
            "markdown": markdown,
        }

    def build_tree_presentation(self, data, *, path: str = "") -> dict | None:
        from app.domain.services.chat_product_structure_presentation_service import (
            ChatProductStructurePresentationService,
        )

        return ChatProductStructurePresentationService.build_tree_presentation(
            data,
            source_path=path,
            path=path,
        )

    def build_presentation(
        self,
        data,
        *,
        path: str = "",
        response_schema: dict | None = None,
    ) -> dict | None:
        schema_labels = self._column_labels.resolve_schema_labels(response_schema)
        self._active_schema_labels = self._column_labels.merge_meta_field_labels(
            schema_labels,
            data,
        )
        self._active_schema_formats = self._column_labels.merge_meta_field_formats(
            {},
            data,
        )

        try:
            profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)
            entity_first = self._build_presentation_by_entity(
                data,
                path=path,
                profile=profile,
            )

            if entity_first is not None:
                return entity_first

            return self._build_presentation(data, path=path)
        finally:
            self._active_schema_labels = None
            self._active_schema_formats = None

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

        root = self._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        if entity == "product_factory_status":
            return self._build_factory_status_table(root, path)

        product = root.get("product")

        if entity == "product_analyser" and isinstance(product, dict):
            guide_table = self._build_product_analyser_guide_table(root)

            if guide_table:
                return guide_table

            return self._build_product_analyser_profile_table(product, root)

        if entity == "product" and isinstance(product, dict):
            detail_list = self._extract_product_detail_list(root)

            if detail_list:
                return self._build_product_detail_table(product, detail_list, root)

            return self._build_product_table(product, root)

        if entity in {"product_structure", "product_parents"}:
            if isinstance(root.get("root"), dict) and isinstance(root.get("items"), list):
                if entity == "product_parents":
                    return None

                structure_table = self._build_analyser_structure_components_table(root)

                if structure_table:
                    return structure_table

        items = root.get("items")

        if isinstance(items, list) and items and isinstance(items[0], dict):
            title = self._infer_items_title(items, path)
            first_item = items[0]

            if entity == "product_stock" or self._is_stock_data(first_item):
                return self._build_items_table(items, title=title, path=path)

            if entity == "product_inspection" or self._looks_like_inspection_item(first_item):
                return self._build_inspection_items_table(items, path=path)

            if entity == "product_search" and "code" in first_item and "description" in first_item:
                return self._build_product_search_table(items, root, title=title)

            if entity == "product_guide" or (
                "operation_description" in first_item or "operation_code" in first_item
            ):
                return self._build_items_table(items, title=title, path=path)

            if len(items) >= 2 or self._is_tabular_data(first_item):
                return self._build_items_table(items, title=title, path=path)

        if entity in {
            "product_production_status",
            "product_shipping_status",
            "product_structure_exclusivity",
        }:
            return self._build_playbook_report_table(root, path, entity=entity)

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
            billing_table = self._build_product_billing_table(
                root,
                effective_path,
                entity=entity,
            )

            if billing_table:
                return billing_table

        if entity in ChatApiDelpiResponseProfileService.PRODUCT_LIST_PRESENT_ENTITIES:
            items = root.get("items")

            if isinstance(items, list) and items and isinstance(items[0], dict):
                title = self._infer_items_title(items, effective_path)

                if len(items) >= 2 or self._is_tabular_data(items[0]):
                    return self._build_items_table(items, title=title, path=effective_path)

        if entity == "product_pricing" and isinstance(root.get("prices"), list):
            prices = root["prices"]

            if prices and isinstance(prices[0], dict):
                title = self._infer_items_title(prices, effective_path)
                return self._build_items_table(prices, title=title, path=effective_path)

        if entity in ChatApiDelpiResponseProfileService.SALE_ORDER_PRESENT_ENTITIES:
            items = root.get("items")

            if isinstance(items, list) and items:
                return self._build_sale_orders_table(items, root)

        if entity in ChatApiDelpiResponseProfileService.SQL_PRESENT_ENTITIES:
            rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])
            title = self._sql_result_title(root, effective_path)

            if rows:
                return self._build_items_table(rows, title=title, path=effective_path)

        if ChatApiDelpiResponseProfileService.is_kpi_entity(entity):
            stock_value_table = self._build_stock_value_branch_table(
                root,
                effective_path,
                entity=entity,
            )

            if stock_value_table:
                return stock_value_table

        if entity in ChatApiDelpiResponseProfileService.SYSTEM_PRESENT_ENTITIES:
            columns_table = self._build_system_columns_table(
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
                    return self._build_lmp_table(items, root)

        return None

    def _build_factory_status_table(self, root: dict, path: str) -> dict:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(product.get("product_code") or product.get("code") or "").strip()
        columns = self._column_labels.kv_table_column_defs()
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

        for key, value in list(indicators.items())[:8]:
            rows.append(
                {
                    "campo": self._humanize_key(str(key)),
                    "valor": str(value),
                }
            )

        return {
            "type": "table",
            "title": f"Status fabril — {code}" if code else "Status fabril do produto",
            "columns": columns,
            "rows": rows,
        }

    def _build_playbook_report_table(
        self,
        root: dict,
        path: str,
        *,
        entity: str,
    ) -> dict | None:
        summary = root.get("summary") if isinstance(root.get("summary"), dict) else None
        items = root.get("items") if isinstance(root.get("items"), list) else None

        if items and isinstance(items[0], dict):
            title = self._infer_items_title(items, path)
            return self._build_items_table(items, title=title, path=path)

        if not summary:
            return None

        columns = self._column_labels.kv_table_column_defs()
        rows = [
            {"campo": self._humanize_key(str(key)), "valor": str(value)}
            for key, value in summary.items()
        ]

        titles = {
            "product_production_status": "Situação produtiva",
            "product_shipping_status": "Expedição",
            "product_structure_exclusivity": "Exclusividade de MPs",
        }

        return {
            "type": "table",
            "title": titles.get(entity, "Relatório"),
            "columns": columns,
            "rows": rows,
        }

    def _build_presentation(self, data, *, path: str = "") -> dict | None:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        root = self._unwrap_data(data)

        if isinstance(root, list) and root and isinstance(root[0], dict):
            sql_title = ExternalActionResponseContentService.get("sql", "defaultTitle")
            return self._build_items_table(root, title=sql_title)

        if not isinstance(root, dict):
            return None

        product = root.get("product")
        if isinstance(product, dict):
            detail_list = self._extract_product_detail_list(root)

            if detail_list:
                return self._build_product_detail_table(product, detail_list, root)

            if "/analyser" in str(path or "").lower():
                guide_table = self._build_product_analyser_guide_table(root)

                if guide_table:
                    return guide_table

                return self._build_product_analyser_profile_table(product, root)

            return self._build_product_table(product, root)

        if isinstance(root.get("root"), dict) and isinstance(root.get("items"), list):
            lowered = str(path or "").lower()

            if "/structure" in lowered or "/parents" in lowered:
                return None

            if "/parents" not in lowered:
                structure_table = self._build_analyser_structure_components_table(root)

                if structure_table:
                    return structure_table

        items = root.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            lowered_items = str(path or "").lower()

            if "/inspection" in lowered_items or self._looks_like_inspection_item(items[0]):
                inspection_table = self._build_inspection_items_table(items, path=path)

                if inspection_table:
                    return inspection_table

            if "sale_number" in items[0] or "saleNumber" in items[0]:
                return self._build_lmp_table(items, root)

            if "order_number" in items[0]:
                return self._build_sale_orders_table(items, root)

            title = self._infer_items_title(items, path)

            if "code" in items[0] and "description" in items[0]:
                if len(items) >= 3:
                    return self._build_product_search_table(items, root, title=title)
                return self._build_product_search_table(items, root, title=title)

            if len(items) >= 2 or self._is_tabular_data(items[0]):
                return self._build_items_table(items, title=title, path=path)

            return None

        stock = root.get("stock")
        if isinstance(stock, dict) and isinstance(stock.get("items"), list):
            stock_title = self._path_fragment_title("/stock") or ChatProductOperationalContentService.get(
                "presenter",
                "stock",
                "titleDefault",
            )
            return self._build_items_table(
                stock.get("items") or [],
                title=stock_title,
            )

        parents = root.get("parents")
        if isinstance(parents, list) and parents:
            parents_title = (
                self._path_fragment_title("/parents")
                or ChatProductOperationalContentService.get(
                    "presenter",
                    "parents",
                    "titleGeneric",
                )
            )
            return self._build_items_table(parents, title=parents_title)

        structure = root.get("structure")
        if isinstance(structure, dict) and isinstance(structure.get("items"), list):
            structure_title = self._path_fragment_title("/structure")
            return self._build_items_table(
                structure["items"],
                title=structure_title or self._path_fragment_title("structure"),
            )

        stock_value_table = self._build_stock_value_branch_table(root, path)

        if stock_value_table:
            return stock_value_table

        billing_table = self._build_product_billing_table(root, path)

        if billing_table:
            return billing_table

        columns_table = self._build_system_columns_table(root, path)

        if columns_table:
            return columns_table

        if isinstance(root.get("resultsets"), list):
            rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])
            title = self._sql_result_title(root, path)

            if rows:
                return self._build_items_table(
                    rows,
                    title=title,
                    path=path,
                )

            if self._looks_like_inventory_below_minimum_sql_context(root, path):
                empty_table = self._build_sql_resultset_empty_table(
                    root,
                    title=title,
                    path=path,
                )

                if empty_table:
                    return empty_table

        return None

    def _build_product_table(self, product: dict, root: dict) -> dict:
        columns = self._column_labels.kv_table_column_defs()
        rows = self._column_labels.build_kv_profile_rows(
            product,
            skip_empty=False,
            schema_labels=self._active_schema_labels,
        )
        rows = [row for row in rows if row.get("valor") is not None]

        for key in ("guide", "inspection", "structure", "customers", "suppliers"):
            value = root.get(key)
            if isinstance(value, dict) and value.get("total") is not None:
                rows.append(
                    {
                        "campo": self._label_collection(key),
                        "valor": self._column_labels.format_collection_total(value["total"]),
                    }
                )

        code = str(product.get("code") or "").strip()

        return {
            "type": "table",
            "title": self._presenter_root_format("productProfileTableTitle", code=code),
            "columns": columns,
            "rows": rows,
        }

    def _build_product_detail_table(self, product: dict, detail_list: list, root: dict) -> dict:
        code = product.get("code", "")
        title = self._product_detail_title(code, root)

        all_keys = {}
        for item in detail_list:
            for k in item:
                if k not in all_keys:
                    all_keys[k] = True

        columns = [self._enrich_column(k, self._humanize_key(k)) for k in all_keys]
        rows = detail_list

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": rows,
        }


    def _build_sale_orders_table(self, items: list, root: dict) -> dict:
        rows = [item for item in items if isinstance(item, dict)]

        return {
            "type": "table",
            "title": self._route_presentation(
                "tableTitles",
                "saleOrders",
                total=str(root.get("total", len(rows))),
            ),
            "columns": self._fixed_columns("saleOrders"),
            "rows": rows,
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
        first = items[0] if items else {}
        has_extra = any(k in first for k in ("quantity", "level", "lot_quantity"))

        if has_extra:
            flat_items = self._flatten_nested_field(items)
            first_flat = flat_items[0] if flat_items else {}
            all_keys = {}
            for item in flat_items:
                for k in item:
                    if k not in all_keys:
                        all_keys[k] = True
            columns = [self._enrich_column(k, self._humanize_key(k)) for k in all_keys]
            rows = flat_items
        else:
            columns = self._fixed_columns("productSearchBasic")
            rows = [
                {"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")}
                for i in items
                if isinstance(i, dict)
            ]

        table_title = title or self._presenter_root_format(
            "productSearchTableTitle",
            total=str(root.get("total", len(rows))),
        )

        return {
            "type": "table",
            "title": table_title,
            "columns": columns,
            "rows": rows,
        }

    _COLUMN_TYPE_MAP = {
        "currency": (
            "valor", "preco", "price", "custo", "cost", "total", "revenue",
            "faturamento", "receita", "vlr", "vl_", "last_purchase_price",
            "standard_cost", "unit_price", "net_value", "gross_value",
        ),
        "percent": (
            "pct", "percent", "taxa", "rate", "margem", "margin", "otd",
            "giro", "eficiencia", "yield",
        ),
        "date": (
            "data", "date", "emissao", "criacao", "atualizacao", "inicio",
            "fim", "vencimento", "dt_", "created", "updated", "last_revision",
        ),
        "quantity": (
            "qtd", "quantidade", "qty", "quantity", "saldo", "disponivel",
            "reservado", "estoque", "volume", "current_quantity",
            "available_quantity", "committed_quantity", "reserved_quantity",
        ),
    }

    def _infer_column_type(self, key: str) -> str | None:
        lowered = key.lower()
        for data_type, tokens in self._COLUMN_TYPE_MAP.items():
            if any(token in lowered for token in tokens):
                return data_type
        return None

    def _enrich_column(self, key: str, label: str) -> dict:
        col = {"key": key, "label": label}
        data_type = self._infer_column_type(key)
        if data_type:
            col["dataType"] = data_type
        return col



    def _humanize_key(self, key: str) -> str:
        return self._column_labels.label_for(
            key,
            schema_labels=self._active_schema_labels,
        )

    def _format_field_value(self, key: str, value: object) -> str:
        return self._column_labels.format_field_value(
            key,
            value,
            schema_formats=self._active_schema_formats,
        )

    def _fixed_columns(self, table_id: str) -> list[dict]:
        return self._column_labels.fixed_table_columns(
            table_id,
            schema_labels=self._active_schema_labels,
        )

    def _markdown_column_pairs(self, table_id: str) -> list[tuple[str, str]]:
        return self._column_labels.markdown_column_pairs(
            table_id,
            schema_labels=self._active_schema_labels,
        )

    def _format_structure_component_line(
        self,
        code: str,
        description: str,
        item_type: str,
        quantity: object,
    ) -> str:
        separator = self._route_presentation("structureItems", "componentSeparator")
        parts = [
            self._route_presentation(
                "structureItems",
                "componentCode",
                code=code,
            )
        ]

        if description:
            parts.append(description)

        line = separator.join(parts[:2])

        if item_type:
            line += self._route_presentation(
                "structureItems",
                "componentType",
                type=item_type,
            )

        if quantity is not None:
            line += self._route_presentation(
                "structureItems",
                "componentQuantity",
                quantity=self._format_num(quantity),
            )

        return (
            self._route_presentation("structureItems", "componentBulletPrefix")
            + line
        )

    def _format_measurable_test_specs(self, test: dict) -> str | None:
        if not isinstance(test, dict):
            return None

        unit = str(test.get("unit") or "")
        spec_parts: list[str] = []
        nominal = test.get("nominal_value")
        lower = test.get("lower_spec_limit")
        upper = test.get("upper_spec_limit")
        missing = self._route_presentation("inspection", "missingLimit")

        if nominal is not None:
            spec_parts.append(
                self._route_presentation(
                    "inspection",
                    "specNominal",
                    nominal=str(nominal),
                    unit=unit,
                )
            )

        if lower is not None or upper is not None:
            spec_parts.append(
                self._route_presentation(
                    "inspection",
                    "specLimits",
                    lower=str(lower if lower is not None else missing),
                    upper=str(upper if upper is not None else missing),
                    unit=unit,
                )
            )

        return ", ".join(spec_parts) if spec_parts else None

    def _format_inspection_characteristic_line(self, item: dict) -> str | None:
        if not isinstance(item, dict):
            return None

        characteristic = str(
            item.get("characteristic")
            or item.get("specification")
            or item.get("step_description")
            or item.get("description")
            or "?"
        ).strip()
        inspection_type = str(item.get("inspection_type") or item.get("method") or "").strip()
        sequence = item.get("sequence")
        step = item.get("step")
        separator = self._route_presentation(
            "inspection",
            "characteristicPartsSeparator",
        )
        parts = [
            self._route_presentation(
                "inspection",
                "characteristicBold",
                characteristic=characteristic,
            )
        ]

        if inspection_type:
            parts.append(
                self._route_presentation(
                    "inspection",
                    "typeSuffix",
                    inspection_type=inspection_type,
                )
            )

        if sequence not in (None, ""):
            parts.append(
                self._route_presentation(
                    "inspection",
                    "sequenceSuffix",
                    sequence=str(sequence),
                )
            )
        elif step not in (None, ""):
            parts.append(
                self._route_presentation(
                    "inspection",
                    "sequenceSuffix",
                    sequence=str(step),
                )
            )

        return (
            self._route_presentation("inspection", "characteristicBulletPrefix")
            + separator.join(parts)
        )

    def _format_product_search_line(
        self,
        *,
        code: str,
        description: str,
        item_type: str,
        unit: str,
        quantity: object,
        level: object,
        is_hierarchy: bool,
    ) -> str:
        separator = self._route_presentation("productSearch", "separator")
        parts = [
            self._route_presentation("productSearch", "codeBold", code=code or "?")
        ]

        if description:
            parts.append(description)

        line = separator.join(parts[:2])

        if item_type:
            line += self._route_presentation(
                "productSearch",
                "typePart",
                type=item_type,
            )

        if unit:
            line += self._route_presentation(
                "productSearch",
                "unitPart",
                unit=unit,
            )

        if is_hierarchy:
            extras: list[str] = []

            if quantity is not None:
                extras.append(
                    self._route_presentation(
                        "productSearch",
                        "qtyExtra",
                        qty=str(quantity),
                    )
                )

            if level is not None:
                extras.append(
                    self._route_presentation(
                        "productSearch",
                        "levelExtra",
                        level=str(level),
                    )
                )

            if extras:
                line += self._route_presentation(
                    "productSearch",
                    "extrasSeparator",
                ) + ", ".join(extras)

        return line

    def _product_detail_scope(self, root: dict) -> str:
        if "prices" in root:
            return "prices"

        if "stock" in root:
            return "stock"

        if "purchases" in root:
            return "purchases"

        if "sales" in root or "billing" in root:
            return "sales"

        if "open_orders" in root:
            return "open_orders"

        return "default"

    def _product_detail_title(self, code: object, root: dict) -> str:
        scope = self._product_detail_scope(root)

        return self._presenter_text(
            "productDetailTitles",
            scope,
            code=str(code or "").strip(),
        )







    # --- Billing / estoque / PMR (delegação Fase 3A lote 8) ---

    def _present_stock_value_summary(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._billing()._present_stock_value_summary(root, path, entity=entity)

    def _present_product_billing_summary(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._billing()._present_product_billing_summary(root, path, entity=entity)

    def _present_financial_pmr(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._billing()._present_financial_pmr(root, path, entity=entity)

    def _build_stock_value_kpi(self, root: dict, path: str) -> dict | None:
        return self._billing()._build_stock_value_kpi(root, path)

    def _build_stock_value_branch_table(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._billing()._build_stock_value_branch_table(root, path, entity=entity)

    def _build_product_billing_table(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._billing()._build_product_billing_table(root, path, entity=entity)

    def _billing_title(self, path: str) -> str:
        return self._billing()._billing_title(path)

    def _billing_table_rows(self, root: dict) -> list[dict]:
        return self._billing()._billing_table_rows(root)

    def _stock_value_summary_lines(self, summary: dict, by_branch: object) -> list[str]:
        return self._billing()._stock_value_summary_lines(summary, by_branch)

    # --- System tables (delegação Fase 3A lote 8) ---

    def _present_system_tables_search(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._system_tables()._present_system_tables_search(root, path, entity=entity)

    def _present_system_table_columns(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._system_tables()._present_system_table_columns(root, path, entity=entity)

    def _build_system_columns_table(self, root: dict, path: str, *, entity: str | None = None) -> dict | None:
        return self._system_tables()._build_system_columns_table(root, path, entity=entity)

    # --- SQL (delegação Fase 3A lote 7) ---

    def _present_sql_rows(self, rows: list) -> dict | None:
        return self._sql()._present_sql_rows(rows)

    def _present_sql_resultsets(self, root: dict, path: str) -> dict | None:
        return self._sql()._present_sql_resultsets(root, path)

    def _collect_sql_resultset_rows(self, resultsets: list) -> list[dict]:
        return self._sql()._collect_sql_resultset_rows(resultsets)

    @staticmethod
    def _sql_resultset_record_total(resultsets: list) -> int | None:
        return ExternalActionSqlPresenter._sql_resultset_record_total(resultsets)

    def _sql_result_title(self, root: dict, path: str) -> str:
        return self._sql()._sql_result_title(root, path)

    def _sql_empty_message(self, root: dict, path: str) -> str:
        return self._sql()._sql_empty_message(root, path)

    def _resolve_production_schedule_from_root(self, root: dict):
        return self._sql()._resolve_production_schedule_from_root(root)

    def _looks_like_production_sql_context(self, root: dict, path: str) -> bool:
        return self._sql()._looks_like_production_sql_context(root, path)

    def _looks_like_inventory_below_minimum_sql_context(self, root: dict, path: str) -> bool:
        return self._sql()._looks_like_inventory_below_minimum_sql_context(root, path)

    def _looks_like_inventory_below_minimum_row(self, row: dict) -> bool:
        return self._sql()._looks_like_inventory_below_minimum_row(row)

    def _present_sql_dict_rows(
        self,
        rows: list[dict],
        *,
        title: str | None = None,
        record_total: int | None = None,
    ) -> dict:
        return self._sql()._present_sql_dict_rows(rows, title=title, record_total=record_total)

    def _looks_like_production_schedule_row(self, row: dict) -> bool:
        return self._sql()._looks_like_production_schedule_row(row)

    def _format_production_schedule_row(self, row: dict) -> str:
        return self._sql()._format_production_schedule_row(row)

    def _build_sql_resultset_empty_table(
        self,
        root: dict,
        *,
        title: str,
        path: str = "",
    ) -> dict | None:
        return self._sql()._build_sql_resultset_empty_table(root, title=title, path=path)

    # --- Product list (delegação Fase 3A lote 3) ---

    def _infer_items_title(self, items: list, path: str) -> str | None:
        return self._product_list()._infer_items_title(items, path)

    def _present_path_routed_items(self, root: dict, path: str) -> dict | None:
        return self._product_list()._present_path_routed_items(root, path)

    def _present_lmp_page(self, root: dict) -> dict | None:
        return self._product_list()._present_lmp_page(root)

    def _present_lmp_detail(self, root: dict) -> dict | None:
        return self._product_list()._present_lmp_detail(root)

    def _present_product_search(self, root: dict, items: list, *, title: str | None = None) -> dict:
        return self._product_list()._present_product_search(root, items, title=title)

    def _present_sale_orders(self, root: dict, items: list) -> dict:
        return self._product_list()._present_sale_orders(root, items)
    def _present_product_guide(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        return self._product_list()._present_product_guide(items, path=path, title=title)

    def _present_product_inspection(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        return self._product_list()._present_product_inspection(items, path=path, title=title)

    def _present_product_stock(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        return self._product_list()._present_product_stock(items, path=path, title=title)

    def _present_items(self, items: list, *, title: str | None = None) -> dict:
        return self._product_list()._present_items(items, title=title)

    def _build_lmp_table(self, items: list, root: dict) -> dict:
        return self._product_list()._build_lmp_table(items, root)

    def _build_items_table(
        self,
        items: list,
        title: str | None = None,
        *,
        path: str = "",
    ) -> dict | None:
        return self._product_list()._build_items_table(items, title=title, path=path)

    # --- Product analyser (delegação Fase 3A lote 2) ---

    def _normalize_analyser_root(self, root: dict) -> dict:
        return self._analyser()._normalize_analyser_root(root)

    def _present_product_analyser(self, root: dict, product: dict, path: str) -> dict:
        return self._analyser()._present_product_analyser(root, product, path)

    def _product_analyser_summary(self, product: dict) -> dict:
        return self._analyser()._product_analyser_summary(product)

    def _build_product_analyser_profile_lines(self, product: dict) -> list[str]:
        return self._analyser()._build_product_analyser_profile_lines(product)

    def _escape_markdown_table_cell(self, value) -> str:
        return self._analyser()._escape_markdown_table_cell(value)

    def _markdown_table(self, columns: list[tuple[str, str]], rows: list[dict]) -> list[str]:
        return self._analyser()._markdown_table(columns, rows)

    def _build_product_analyser_profile_markdown(self, product: dict) -> list[str]:
        return self._analyser()._build_product_analyser_profile_markdown(product)

    def _flatten_analyser_guide_rows(self, guide_items: list) -> list[dict]:
        return self._analyser()._flatten_analyser_guide_rows(guide_items)

    def _build_product_analyser_guide_markdown(self, guide_items: list) -> list[str]:
        return self._analyser()._build_product_analyser_guide_markdown(guide_items)

    def _build_product_analyser_guide_table(self, root: dict) -> dict | None:
        return self._analyser()._build_product_analyser_guide_table(root)

    def _flatten_analyser_inspection_rows(self, inspection_items: list) -> list[dict]:
        return self._analyser()._flatten_analyser_inspection_rows(inspection_items)

    def _build_product_analyser_inspection_table(self, root: dict) -> dict | None:
        return self._analyser()._build_product_analyser_inspection_table(root)

    def _build_inspection_items_table(
        self,
        items: list,
        *,
        path: str = "",
    ) -> dict | None:
        return self._analyser()._build_inspection_items_table(items, path=path)

    def _has_protheus_inspection_blocks(self, item: dict) -> bool:
        return self._analyser()._has_protheus_inspection_blocks(item)

    def _inspection_list(self, item: dict, *keys: str) -> list:
        return self._analyser()._inspection_list(item, *keys)

    def build_analyser_auxiliary_table_presentations(self, root: dict) -> list[dict]:
        return self._analyser().build_analyser_auxiliary_table_presentations(root)

    def _build_product_analyser_inspection_markdown(self, inspection_items: list) -> list[str]:
        return self._analyser()._build_product_analyser_inspection_markdown(inspection_items)

    def _build_product_analyser_collection_sections(self, root: dict) -> list[str]:
        return self._analyser()._build_product_analyser_collection_sections(root)

    def _build_product_analyser_body_lines(
        self,
        root: dict,
        product: dict,
        *,
        compact_for_rich_ui: bool = False,
    ) -> list[str]:
        return self._analyser()._build_product_analyser_body_lines(
            root,
            product,
            compact_for_rich_ui=compact_for_rich_ui,
        )

    def _format_collection_item_lines(self, items: list) -> list[str]:
        return self._analyser()._format_collection_item_lines(items)

    def _format_guide_like_item(self, item: dict) -> str | None:
        return self._analyser()._format_guide_like_item(item)

    def _build_product_analyser_insights(self, root: dict, product: dict) -> list[str]:
        return self._analyser()._build_product_analyser_insights(root, product)

    def _flatten_analyser_structure_rows(self, structure: dict | None) -> list[dict]:
        return self._analyser()._flatten_analyser_structure_rows(structure)

    def _build_analyser_structure_components_table(
        self,
        structure: dict | None,
    ) -> dict | None:
        return self._analyser()._build_analyser_structure_components_table(structure)

    def _build_product_analyser_profile_table(self, product: dict, root: dict) -> dict:
        return self._analyser()._build_product_analyser_profile_table(product, root)

    def _build_product_analyser_text_presentation(
        self,
        root: dict,
        product: dict,
        path: str,
    ) -> dict | None:
        return self._analyser()._build_product_analyser_text_presentation(root, product, path)

    def _analyser_table_title(self, kind: str, product_code: str) -> str:
        return self._analyser()._analyser_table_title(kind, product_code)

    def _kpi_cards_from_presenter_section(
        self,
        section: str,
        data: dict,
    ) -> list[dict]:
        return self._kpi_chart().kpi_cards_from_presenter_section(section, data)

    def build_dashboard_presentation(self, data, *, path: str = "") -> dict | None:
        return self._kpi_chart().build_dashboard_presentation(data, path=path)

    def build_chart_presentation(self, data, *, path: str = "", force: bool = False) -> dict | None:
        return self._kpi_chart().build_chart_presentation(data, path=path, force=force)

    def _is_tabular_data(self, row: dict) -> bool:
        """Dados que naturalmente beneficiam de apresentação em tabela mesmo com 1 registro."""
        tabular_markers = [
            "warehouse", "current_quantity", "available_quantity",
            "supplier_code", "supplier_name", "customer_code", "customer_name",
            "table_code", "sale_price", "invoice_number",
            "order_number", "sale_number",
            "step", "sequence", "inspection_type", "characteristic",
            "origin_warehouse", "destination_warehouse", "movement_date",
            "operation_code", "operation_description", "route_code", "work_center",
        ]
        return any(k in row for k in tabular_markers)

    def _is_stock_data(self, row: dict) -> bool:
        return self._kpi_chart()._is_stock_data(row)

    def _looks_like_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> bool:
        return self._kpi_chart().looks_like_kpi_response(root, path, entity=entity)

    def _build_kpi_chart(self, root: dict, path: str) -> dict | None:
        return self._kpi_chart().build_kpi_chart(root, path)

    def _build_generic_kpi_cards(self, root: dict, path: str) -> list | None:
        return self._kpi_chart().build_generic_kpi_cards(root, path)

    def _kpi_title(self, path: str) -> str:
        return self._kpi_chart().kpi_title(path)

    def _try_chart_from_rows(
        self,
        rows: list,
        *,
        force: bool = False,
        path: str = "",
        user_message: str | None = None,
    ) -> dict | None:
        return self._kpi_chart().try_chart_from_rows(
            rows,
            force=force,
            path=path,
            user_message=user_message,
        )

    def _try_heatmap_from_rows(
        self,
        rows: list,
        *,
        force: bool = False,
        user_message: str | None = None,
    ) -> dict | None:
        return self._kpi_chart().try_heatmap_from_rows(
            rows,
            force=force,
            user_message=user_message,
        )

    def _format_num(self, value) -> str:
        try:
            num = float(value)
            if num == int(num):
                return str(int(num))
            return f"{num:.2f}"
        except (ValueError, TypeError):
            return str(value)

    def _analyser_markdown(self, key: str, **values: str) -> str:
        return self._presenter_text("analyserMarkdown", key, **values)

    def _route_narrative(self, route: str, key: str, **values: str) -> str:
        return self._presenter_text("routeNarratives", route, key, **values)

    def _route_presentation(self, route: str, key: str, **values: str) -> str:
        return self._presenter_text("routePresentations", route, key, **values)

    def _presenter_text(
        self,
        section: str,
        text_key: str,
        *extra_path: str,
        **values: str,
    ) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        path = (section, text_key, *extra_path)

        if values:
            return ChatAssistantContentService.format(
                "presenter_content",
                *path,
                **values,
            )

        return ChatAssistantContentService.get("presenter_content", *path)

    def _presenter_root_format(self, key: str, **values: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return ChatAssistantContentService.format(
            "presenter_content",
            key,
            **values,
        )

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


class ExternalActionResultPresenter:
    def __init__(
        self,
        column_label_service: ExternalActionColumnLabelService | None = None,
    ):
        self._column_labels = column_label_service or ExternalActionColumnLabelService()
        self._active_schema_labels: dict[str, str] | None = None

    def present(self, data, *, path: str = "") -> dict:
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
            kpi = self._build_kpi_chart(root, path)
            if kpi:
                linhas = self._kpi_cards_to_linhas(kpi)

                return {
                    "titulo": kpi.get("title", "Indicador"),
                    "linhas": linhas
                    or [
                        self._presenter_text(
                            "generic",
                            "kpiSeeData",
                            title=kpi.get("title", "Indicador"),
                        )
                    ],
                    "dados": root,
                    "apresentacao": kpi,
                }

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
                sub_items = [f"{k}: {v}" for k, v in value.items()]
                label = self._humanize_key(key)
                linhas.append(f"**{label}:** {', '.join(sub_items)}")
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
                linhas.append(f"**{self._humanize_key(key)}:** {value}")

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
        cards = kpi.get("cards")

        if not isinstance(cards, list):
            return []

        linhas: list[str] = []

        for card in cards:
            if not isinstance(card, dict):
                continue

            label = str(card.get("label") or "Indicador").strip()
            unit = str(card.get("unit") or "").strip()
            value = card.get("value")

            if value is None:
                continue

            suffix = f" {unit}".rstrip()
            linhas.append(f"**{label}:** {self._format_num(value)}{suffix}")

        return linhas

    def _present_stock_value_summary(self, root: dict, path: str) -> dict | None:
        if "stock-value" not in str(path or "").lower():
            return None

        summary = root.get("summary")

        if not isinstance(summary, dict):
            return None

        title = self._kpi_title(path)
        linhas = [
            f"**Valor total em estoque:** R$ {self._format_currency(summary.get('total_stock_value'))}",
            f"**Quantidade total:** {self._format_num(summary.get('total_stock_quantity'))}",
            f"**Produtos distintos:** {summary.get('total_products')}",
            f"**Registros:** {summary.get('total_records')}",
            f"**Localizações:** {summary.get('total_locations')}",
        ]

        by_branch = root.get("by_branch")

        if isinstance(by_branch, list):
            for item in by_branch:
                if not isinstance(item, dict):
                    continue

                branch = str(item.get("branch") or "").strip()

                if not branch:
                    continue

                linhas.append(
                    "Filial "
                    f"{branch}: R$ {self._format_currency(item.get('total_stock_value'))} "
                    f"({self._format_num(item.get('total_stock_quantity'))} un.)"
                )

        kpi = self._build_stock_value_kpi(root, path)

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
            "apresentacao": kpi,
        }

    def _present_product_billing_summary(self, root: dict, path: str) -> dict | None:
        lowered = str(path or "").lower()

        if "/sales/billing" not in lowered:
            return None

        if "value" not in root and "documents" not in root:
            return None

        product_code = self._extract_product_code_from_path(path)
        title = (
            f"Faturamento do produto {product_code}"
            if product_code
            else "Faturamento do produto"
        )
        linhas: list[str] = []

        if root.get("value") is not None:
            linhas.append(
                f"**Valor faturado:** R$ {self._format_currency(root.get('value'))}"
            )

        if root.get("documents") is not None:
            linhas.append(f"**Documentos:** {root.get('documents')}")

        first_date = self._format_protheus_date(root.get("first_billing_date"))

        if first_date:
            linhas.append(f"**Primeira emissão:** {first_date}")

        last_date = self._format_protheus_date(root.get("last_billing_date"))

        if last_date:
            linhas.append(f"**Última emissão:** {last_date}")

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
        }

    def _present_financial_pmr(self, root: dict, path: str) -> dict | None:
        if "pmr" not in str(path or "").lower():
            return None

        if "branch" not in root and "pmr_days" not in root:
            return None

        title = self._kpi_title(path)
        branch = str(root.get("branch") or "consolidado").strip()
        linhas = [f"**Filial:** {branch}"]
        pmr_days = root.get("pmr_days")

        if pmr_days is None:
            linhas.append(self._analyser_markdown("pmrUnavailable"))
        else:
            linhas.append(f"**PMR:** {self._format_num(pmr_days)} dias")

        return {
            "titulo": title,
            "linhas": linhas,
            "dados": root,
        }

    def _present_system_tables_search(self, root: dict, path: str) -> dict | None:
        if "/tables/search" not in str(path or "").lower():
            return None

        results = root.get("results")

        if not isinstance(results, list):
            return None

        total = root.get("total_records", len(results))
        linhas = [f"**Tabelas encontradas:** {total}"]

        for item in results[:12]:
            if not isinstance(item, dict):
                continue

            table_code = (
                item.get("X2_ARQUIVO")
                or item.get("table_name")
                or item.get("name")
            )
            label = item.get("X2_NOME") or item.get("description") or item.get("title")
            score = item.get("total_score") or item.get("score")

            if table_code and label:
                line = f"- **{table_code}:** {label}"
            elif table_code:
                line = f"- **{table_code}**"
            elif label:
                line = f"- {label}"
            else:
                continue

            if score is not None:
                try:
                    line += f" (relevância {float(score):.0f})"
                except (TypeError, ValueError):
                    pass

            linhas.append(line)

        if len(results) > 12:
            linhas.append(
                self._presenter_text(
                    "pagination", "moreTables", count=str(len(results) - 12)
                )
            )

        if len(linhas) <= 1:
            linhas.append(
                self._route_presentation("systemTables", "noMatch")
            )

        return {
            "titulo": self._route_presentation("systemTables", "searchTitle"),
            "linhas": linhas,
            "dados": root,
        }

    def _present_system_table_columns(self, root: dict, path: str) -> dict | None:
        if "/columns" not in str(path or "").lower():
            return None

        results = root.get("results")

        if not isinstance(results, list) or not results:
            return None

        table_name = str(path or "").rstrip("/").split("/")[-2]
        total = root.get("total", len(results))
        linhas = [f"**Total de colunas:** {total}"]

        for item in results:
            if not isinstance(item, dict):
                continue

            field = item.get("X3_CAMPO") or item.get("column_name") or item.get("field")
            label = item.get("X3_DESCRIC") or item.get("column_description") or item.get("label")

            if field and label:
                linhas.append(f"- **{field}:** {label}")
            elif field:
                linhas.append(f"- **{field}**")

        if len(results) > 8:
            linhas.append(f"… e mais {len(results) - 8} coluna(s).")

        return {
            "titulo": self._route_presentation(
                "systemTables",
                "columnsTitle",
                table=table_name.upper(),
            ),
            "linhas": linhas,
            "dados": root,
        }

    def _build_stock_value_kpi(self, root: dict, path: str) -> dict | None:
        summary = root.get("summary")

        if not isinstance(summary, dict):
            return None

        cards = [
            {
                "label": "Valor total",
                "value": summary.get("total_stock_value"),
                "unit": "R$",
                "color": "#0ea5e9",
            },
            {
                "label": "Quantidade total",
                "value": summary.get("total_stock_quantity"),
                "unit": "",
                "color": "#10b981",
            },
            {
                "label": "Produtos",
                "value": summary.get("total_products"),
                "unit": "",
                "color": "#f59e0b",
            },
            {
                "label": "Localizações",
                "value": summary.get("total_locations"),
                "unit": "",
                "color": "#ef4444",
            },
        ]

        return {
            "type": "kpi",
            "title": self._kpi_title(path),
            "cards": cards,
        }

    def _build_stock_value_branch_table(self, root: dict, path: str) -> dict | None:
        if "stock-value" not in str(path or "").lower():
            return None

        by_branch = root.get("by_branch")

        if not isinstance(by_branch, list):
            return None

        rows = [
            item
            for item in by_branch
            if isinstance(item, dict) and str(item.get("branch") or "").strip()
        ]

        if not rows:
            return None

        return {
            "type": "table",
            "title": "Valor de estoque por filial",
            "columns": [
                {"key": "branch", "label": "Filial"},
                {
                    "key": "total_stock_value",
                    "label": "Valor total",
                    "dataType": "currency",
                },
                {
                    "key": "total_stock_quantity",
                    "label": "Quantidade",
                    "dataType": "quantity",
                },
                {"key": "total_products", "label": "Produtos"},
            ],
            "rows": rows,
        }

    def _build_product_billing_table(self, root: dict, path: str) -> dict | None:
        if "/sales/billing" not in str(path or "").lower():
            return None

        if root.get("value") is None and root.get("documents") is None:
            return None

        product_code = self._extract_product_code_from_path(path)
        title = (
            f"Faturamento do produto {product_code}"
            if product_code
            else "Faturamento do produto"
        )

        return {
            "type": "table",
            "title": title,
            "columns": [
                {"key": "campo", "label": "Campo"},
                {"key": "valor", "label": "Valor"},
            ],
            "rows": [
                {"campo": "Valor faturado", "valor": root.get("value"), "valorType": "currency"},
                {"campo": "Documentos", "valor": root.get("documents"), "valorType": "quantity"},
                {
                    "campo": "Primeira emissão",
                    "valor": self._format_protheus_date(root.get("first_billing_date")),
                    "valorType": "date",
                },
                {
                    "campo": "Última emissão",
                    "valor": self._format_protheus_date(root.get("last_billing_date")),
                    "valorType": "date",
                },
            ],
        }

    def _build_system_columns_table(self, root: dict, path: str) -> dict | None:
        if "/columns" not in str(path or "").lower():
            return None

        results = root.get("results")

        if not isinstance(results, list) or not results:
            return None

        table_name = str(path or "").rstrip("/").split("/")[-2]
        rows = []

        for item in results:
            if not isinstance(item, dict):
                continue

            rows.append(
                {
                    "campo": item.get("X3_CAMPO") or item.get("column_name") or item.get("field"),
                    "descricao": item.get("X3_DESCRIC") or item.get("column_description") or item.get("label"),
                    "tipo": item.get("X3_TIPO") or item.get("type"),
                    "tamanho": item.get("X3_TAMANHO") or item.get("size"),
                }
            )

        if not rows:
            return None

        return {
            "type": "table",
            "title": f"Colunas da tabela {table_name.upper()}",
            "columns": [
                {"key": "campo", "label": "Campo"},
                {"key": "descricao", "label": "Descrição"},
                {"key": "tipo", "label": "Tipo"},
                {"key": "tamanho", "label": "Tamanho"},
            ],
            "rows": rows,
        }

    def _infer_items_title(self, items: list, path: str) -> str | None:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        bundle = "presenter_content"
        title = ChatAssistantContentService.title_for_path(
            bundle,
            path,
            path_key="titlesByPathFragment",
        )

        if title:
            return title

        if items and isinstance(items[0], dict):
            first = items[0]

            if ("level" in first or "quantity" in first) and "code" in first:
                return ChatAssistantContentService.get(
                    bundle,
                    "titlesByItemShape",
                    "structure",
                )

            if "branch" in first or "warehouse" in first:
                return ChatAssistantContentService.get(
                    bundle,
                    "titlesByItemShape",
                    "stock",
                )

            if "eficiencia_percentual" in first and (
                "tempo_real_horas" in first or "centro_trabalho" in first
            ):
                return ChatAssistantContentService.get(
                    bundle,
                    "titlesByItemShape",
                    "efficiency",
                )

        return None

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

    def _present_path_routed_items(self, root: dict, path: str) -> dict | None:
        items = root.get("items") if isinstance(root, dict) else None

        if not isinstance(items, list) or not items:
            return None

        lowered_path = str(path or "").lower()
        title = self._infer_items_title(items, path)
        first_item = items[0] if isinstance(items[0], dict) else {}

        if "/guide" in lowered_path:
            return self._present_product_guide(items, path=path, title=title)

        if "/inspection" in lowered_path or self._looks_like_inspection_item(first_item):
            return self._present_product_inspection(items, path=path, title=title)

        if "/stock" in lowered_path or self._is_stock_data(first_item):
            return self._present_product_stock(items, path=path, title=title)

        return None

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

                raw_msg = str(data.get("message") or "Erro desconhecido na API.")
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

    def _normalize_analyser_root(self, root: dict) -> dict:
        normalized = dict(root)

        for key in (
            "product",
            "guide",
            "inspection",
            "structure",
            "customers",
            "suppliers",
        ):
            value = normalized.get(key)

            if isinstance(value, dict):
                normalized[key] = self._normalize_api_section(value)

        return normalized

    def _build_product_overview_narrative_lines(self, product: dict, root: dict) -> list[str]:
        code = str(product.get("code") or "").strip()
        description = str(product.get("description") or "").strip()
        product_type = str(product.get("type") or "").strip()
        unit = str(product.get("unit") or "").strip()
        group_code = str(product.get("group_code") or "").strip()
        active = str(product.get("active") or "").strip()
        warehouse = str(product.get("default_warehouse") or "").strip()

        lines = [
            f"**{code}** — {description or 'sem descrição cadastrada'}.",
            (
                f"Classificação **{product_type or '—'}**, unidade **{unit or '—'}**, "
                f"grupo **{group_code or '—'}**."
            ),
            (
                f"Situação cadastral: ativo **{active or '—'}**"
                + (f", armazém padrão **{warehouse}**." if warehouse else ".")
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
            suffix = f" ({date_text})" if date_text else ""
            lines.append(f"Última compra registrada: **{price_text}**{suffix}.")

        if standard_cost not in (None, ""):
            lines.append(
                f"Custo padrão vigente: **R$ {self._format_currency(standard_cost)}**."
            )

        revision = str(product.get("last_revision_date") or "").strip()
        ncm = str(product.get("ncm_ipi_position") or "").strip()

        if revision:
            lines.append(f"Última revisão técnica: **{self._format_revision_date(revision)}**.")

        if ncm:
            lines.append(f"NCM: **{ncm}**.")

        blocked = str(product.get("blocked") or "").strip()
        if blocked and blocked not in {"N", "0", ""}:
            lines.append(f"Atenção: indicador de bloqueio **{blocked}** no cadastro.")

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
            "titulo": f"Visão do produto {product_summary['code']}",
            "linhas": [line for line in linhas if "None" not in line],
            "campos": self._alias_dict(product_summary),
            "dados": {
                "product": product_summary,
                "guideTotal": self._total(root.get("guide")),
                "inspectionTotal": self._total(root.get("inspection")),
                "structureTotal": self._total(root.get("structure")),
            },
        }

    def _present_product_analyser(self, root: dict, product: dict, path: str) -> dict:
        code = str(product.get("code") or "").strip()
        title = f"Informações completas do produto {code}" if code else "Informações completas do produto"

        linhas = self._build_product_analyser_body_lines(root, product)

        structure = root.get("structure")
        structure_table = self._build_analyser_structure_components_table(structure)
        structure_tree = self.build_tree_presentation(root, path=path)

        return {
            "titulo": title,
            "linhas": linhas,
            "campos": self._alias_dict(self._product_analyser_summary(product)),
            "dados": {
                "product": self._product_analyser_summary(product),
                "guideTotal": self._total(root.get("guide")),
                "inspectionTotal": self._total(root.get("inspection")),
                "structureTotal": self._total(structure if isinstance(structure, dict) else None),
            },
            "apresentacao": structure_tree or structure_table,
        }

    def _product_analyser_summary(self, product: dict) -> dict:
        return {
            "code": product.get("code"),
            "description": product.get("description"),
            "type": product.get("type"),
            "unit": product.get("unit"),
            "groupCode": product.get("group_code"),
            "active": product.get("active"),
            "blocked": product.get("blocked"),
            "defaultWarehouse": product.get("default_warehouse"),
            "customerReference": product.get("customer_reference"),
            "lastPurchasePrice": product.get("last_purchase_price"),
            "standardCost": product.get("standard_cost"),
            "lastRevisionDate": product.get("last_revision_date"),
            "ncm": product.get("ncm_ipi_position"),
        }

    def _build_product_analyser_profile_lines(self, product: dict) -> list[str]:
        code = product.get("code")
        desc = product.get("description")

        lines = [
            f"Produto **{code}**: {desc}.",
            (
                f"Tipo {product.get('type')}, unidade {product.get('unit')}, "
                f"grupo {product.get('group_code')}."
            ),
            (
                f"Status ativo: {product.get('active')}. "
                f"Armazém padrão: {product.get('default_warehouse')}."
            ),
        ]

        blocked = str(product.get("blocked") or "").strip()

        if blocked:
            lines.append(f"Indicador de bloqueio: {blocked}.")

        customer_reference = str(product.get("customer_reference") or "").strip()

        if customer_reference:
            lines.append(f"Referência de cliente: {customer_reference}.")

        lines.append(
            "Último preço de compra: "
            f"{self._format_currency(product.get('last_purchase_price')) if product.get('last_purchase_price') not in (None, '') else '0'}. "
            f"Custo padrão: R$ {self._format_currency(product.get('standard_cost'))}."
        )
        lines.append(
            f"Última revisão: {product.get('last_revision_date')}. "
            f"NCM: {product.get('ncm_ipi_position')}."
        )

        drawing_code = str(product.get("drawing_code") or "").strip()

        if drawing_code:
            lines.append(f"Código desenho: {drawing_code}.")

        barcode = str(product.get("barcode") or "").strip()

        if barcode:
            lines.append(f"Código de barras: {barcode}.")

        return lines

    def _escape_markdown_table_cell(self, value) -> str:
        text = str(value if value is not None else "").strip()
        return text.replace("|", "\\|").replace("\n", " ")

    def _markdown_table(self, columns: list[tuple[str, str]], rows: list[dict]) -> list[str]:
        if not rows:
            return []

        header = "| " + " | ".join(label for _, label in columns) + " |"
        separator = "| " + " | ".join("---" for _ in columns) + " |"
        body = [
            "| "
            + " | ".join(
                self._escape_markdown_table_cell(row.get(key))
                for key, _ in columns
            )
            + " |"
            for row in rows
        ]

        return [header, separator, *body]

    def _build_product_analyser_profile_markdown(self, product: dict) -> list[str]:
        purchase = product.get("last_purchase_price")

        if purchase in (None, ""):
            purchase_display = "0,00"
        elif isinstance(purchase, (int, float)):
            purchase_display = self._format_currency(purchase)
        else:
            purchase_display = str(purchase)

        rows = [
            ("code", "Código", product.get("code")),
            ("description", "Descrição", product.get("description")),
            ("type", "Tipo", product.get("type")),
            ("unit", "Unidade", product.get("unit")),
            ("group_code", "Grupo", product.get("group_code")),
            ("active", "Ativo", product.get("active")),
            ("blocked", "Bloqueio", product.get("blocked")),
            ("default_warehouse", "Armazém padrão", product.get("default_warehouse")),
            ("customer_reference", "Ref. cliente", product.get("customer_reference")),
            ("drawing_code", "Código desenho", product.get("drawing_code")),
            ("last_purchase_price", "Últ. preço compra", purchase_display),
            (
                "standard_cost",
                "Custo padrão",
                f"R$ {self._format_currency(product.get('standard_cost'))}"
                if product.get("standard_cost") not in (None, "")
                else "",
            ),
            ("last_revision_date", "Última revisão", product.get("last_revision_date")),
            ("ncm_ipi_position", "NCM", product.get("ncm_ipi_position")),
        ]

        table_rows = [
            {"campo": label, "valor": value}
            for _, label, value in rows
            if value not in (None, "")
        ]

        if not table_rows:
            return []

        return [
            "",
            *self._markdown_table(
                [("campo", "Campo"), ("valor", "Valor")],
                table_rows,
            ),
        ]

    def _flatten_analyser_guide_rows(self, guide_items: list) -> list[dict]:
        rows: list[dict] = []

        for item in guide_items:
            if not isinstance(item, dict):
                continue

            product_code = str(item.get("product_code") or "?").strip()
            bom_level = item.get("bom_level", 0)
            operations = item.get("operations")

            if not isinstance(operations, list) or not operations:
                op_desc = str(item.get("operation_description") or "").strip()

                if not op_desc:
                    continue

                rows.append(
                    {
                        "product_code": product_code,
                        "bom_level": bom_level,
                        "operation_code": item.get("operation_code") or "",
                        "operation_description": op_desc,
                        "work_center": item.get("work_center") or "",
                    }
                )
                continue

            for operation in operations:
                if not isinstance(operation, dict):
                    continue

                op_desc = str(operation.get("operation_description") or "").strip()

                if not op_desc:
                    continue

                rows.append(
                    {
                        "product_code": product_code,
                        "bom_level": bom_level,
                        "operation_code": operation.get("operation_code") or "",
                        "operation_description": op_desc,
                        "work_center": operation.get("work_center") or "",
                    }
                )

        return rows

    def _build_product_analyser_guide_markdown(self, guide_items: list) -> list[str]:
        rows = self._flatten_analyser_guide_rows(guide_items)

        if not rows:
            return []

        return [
            "",
            "**Roteiro de produção**",
            "",
            *self._markdown_table(
                [
                    ("product_code", "Produto"),
                    ("bom_level", "BOM"),
                    ("operation_code", "Op."),
                    ("operation_description", "Operação"),
                    ("work_center", "Centro"),
                ],
                rows,
            ),
        ]

    def _build_product_analyser_guide_table(self, root: dict) -> dict | None:
        guide = root.get("guide")

        if not isinstance(guide, dict):
            return None

        guide_items = guide.get("items") or []
        rows = self._flatten_analyser_guide_rows(guide_items)

        if not rows:
            return None

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        product_code = str(product.get("code") or rows[0].get("product_code") or "").strip()
        title = (
            f"Roteiro de produção — {product_code}"
            if product_code
            else "Roteiro de produção"
        )

        return {
            "type": "table",
            "title": title,
            "columns": [
                {"key": "product_code", "label": "Produto"},
                {"key": "bom_level", "label": "BOM", "dataType": "number"},
                {"key": "operation_code", "label": "Op."},
                {"key": "operation_description", "label": "Operação"},
                {"key": "work_center", "label": "Centro"},
            ],
            "rows": rows,
        }

    def _flatten_analyser_inspection_rows(self, inspection_items: list) -> list[dict]:
        rows: list[dict] = []

        for item in inspection_items:
            if not isinstance(item, dict):
                continue

            product_code = str(
                item.get("product")
                or item.get("product_code")
                or "?"
            ).strip()
            level = item.get("level", item.get("bom_level", ""))

            if self._has_protheus_inspection_blocks(item):
                qp7 = self._inspection_list(item, "QP7", "qp7")

                for test in qp7:
                    if not isinstance(test, dict):
                        continue

                    rows.append(
                        {
                            "product_code": product_code,
                            "level": level,
                            "section": "Dimensional",
                            "operation": test.get("QP7_OPERAC") or "",
                            "test": test.get("QP7_ENSAIO") or "",
                            "lab": test.get("QP7_LABOR") or "",
                            "nominal": test.get("QP7_NOMINA") or "",
                            "lower": test.get("QP7_LIE") or test.get("QP7_LIC") or "",
                            "upper": test.get("QP7_LSE") or test.get("QP7_LSC") or "",
                            "unit": test.get("QP7_UNIMED") or "",
                            "detail": "",
                        }
                    )

                qp8 = self._inspection_list(item, "QP8", "qp8")

                for test in qp8:
                    if not isinstance(test, dict):
                        continue

                    rows.append(
                        {
                            "product_code": product_code,
                            "level": level,
                            "section": "Textual",
                            "operation": test.get("QP8_OPERAC") or "",
                            "test": test.get("QP8_ENSAIO") or "",
                            "lab": "",
                            "nominal": "",
                            "lower": "",
                            "upper": "",
                            "unit": "",
                            "detail": test.get("QP8_TEXTO") or "",
                        }
                    )
                continue

            parent_code = str(
                item.get("parentCode")
                or item.get("parentcode")
                or item.get("Parentcode")
                or ""
            ).strip()

            rows.append(
                {
                    "product_code": product_code,
                    "level": level,
                    "section": "Referência",
                    "operation": "",
                    "test": "",
                    "lab": "",
                    "nominal": "",
                    "lower": "",
                    "upper": "",
                    "unit": "",
                    "detail": parent_code
                    or self._presenter_text("generic", "emptyDetail"),
                }
            )

        return rows

    def _build_product_analyser_inspection_table(self, root: dict) -> dict | None:
        inspection = root.get("inspection")

        if not isinstance(inspection, dict):
            return None

        inspection_items = inspection.get("items") or []
        rows = self._flatten_analyser_inspection_rows(inspection_items)

        if not rows:
            return None

        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        product_code = str(product.get("code") or "").strip()
        title = (
            f"Plano de inspeção — {product_code}"
            if product_code
            else "Plano de inspeção"
        )

        return {
            "type": "table",
            "title": title,
            "columns": [
                {"key": "product_code", "label": "Produto"},
                {"key": "level", "label": "Nível"},
                {"key": "section", "label": "Seção"},
                {"key": "operation", "label": "Op."},
                {"key": "test", "label": "Ensaio"},
                {"key": "lab", "label": "Labor."},
                {"key": "nominal", "label": "Nominal"},
                {"key": "lower", "label": "Lim. inf."},
                {"key": "upper", "label": "Lim. sup."},
                {"key": "unit", "label": "Unid."},
                {"key": "detail", "label": "Detalhe"},
            ],
            "rows": rows,
        }

    def _build_inspection_items_table(
        self,
        items: list,
        *,
        path: str = "",
    ) -> dict | None:
        rows = self._flatten_analyser_inspection_rows(items)

        if not rows:
            return None

        product_code = self._extract_product_code_from_path(path)
        title = (
            f"Plano de inspeção — {product_code}"
            if product_code
            else self._infer_items_title(items, path) or "Plano de inspeção"
        )

        return {
            "type": "table",
            "title": title,
            "columns": [
                {"key": "product_code", "label": "Produto"},
                {"key": "level", "label": "Nível"},
                {"key": "section", "label": "Seção"},
                {"key": "operation", "label": "Op."},
                {"key": "test", "label": "Ensaio"},
                {"key": "lab", "label": "Labor."},
                {"key": "nominal", "label": "Nominal"},
                {"key": "lower", "label": "Lim. inf."},
                {"key": "upper", "label": "Lim. sup."},
                {"key": "unit", "label": "Unid."},
                {"key": "detail", "label": "Detalhe"},
            ],
            "rows": rows,
        }

    def build_analyser_auxiliary_table_presentations(self, root: dict) -> list[dict]:
        """Tabelas nativas do analyser: ficha, roteiro, inspeção (ordem de leitura no chat)."""
        tables: list[dict] = []
        product = root.get("product")

        if isinstance(product, dict):
            profile_table = self._build_product_analyser_profile_table(product, root)

            if profile_table:
                tables.append(profile_table)

        guide_table = self._build_product_analyser_guide_table(root)

        if guide_table:
            tables.append(guide_table)

        inspection_table = self._build_product_analyser_inspection_table(root)

        if inspection_table:
            tables.append(inspection_table)

        return tables

    def _has_protheus_inspection_blocks(self, item: dict) -> bool:
        return any(
            key in item
            for key in ("QP6", "QP7", "QP8", "qp6", "qp7", "qp8")
        )

    def _inspection_list(self, item: dict, *keys: str) -> list:
        for key in keys:
            value = item.get(key)

            if isinstance(value, list):
                return value

        return []

    def _build_product_analyser_inspection_markdown(self, inspection_items: list) -> list[str]:
        if not inspection_items:
            return []

        detailed = [
            item
            for item in inspection_items
            if isinstance(item, dict) and self._has_protheus_inspection_blocks(item)
        ]
        shallow = [
            item
            for item in inspection_items
            if isinstance(item, dict) and not self._has_protheus_inspection_blocks(item)
        ]

        sections: list[str] = ["", "**Plano de inspeção**", ""]

        for item in detailed[:6]:
            product_code = str(
                item.get("product")
                or item.get("product_code")
                or "?"
            ).strip()
            level = item.get("level", item.get("bom_level", 0))
            qp6 = self._inspection_list(item, "QP6", "qp6")
            header_desc = ""

            if qp6 and isinstance(qp6[0], dict):
                header_desc = str(qp6[0].get("QP6_DESCPO") or "").strip()

            sections.append("")
            sections.append(f"**Produto {product_code}** (nível {level})")

            if header_desc:
                sections.append(f"*{header_desc}*")

            qp7 = self._inspection_list(item, "QP7", "qp7")

            if qp7:
                dim_rows = []

                for test in qp7:
                    if not isinstance(test, dict):
                        continue

                    dim_rows.append(
                        {
                            "operation": test.get("QP7_OPERAC") or "",
                            "test": test.get("QP7_ENSAIO") or "",
                            "lab": test.get("QP7_LABOR") or "",
                            "nominal": test.get("QP7_NOMINA") or "",
                            "lower": test.get("QP7_LIE") or test.get("QP7_LIC") or "",
                            "upper": test.get("QP7_LSE") or test.get("QP7_LSC") or "",
                            "unit": test.get("QP7_UNIMED") or "",
                        }
                    )

                if dim_rows:
                    sections.append("")
                    sections.append("*Ensaios dimensionais*")
                    sections.extend(
                        self._markdown_table(
                            [
                                ("operation", "Op."),
                                ("test", "Ensaio"),
                                ("lab", "Labor."),
                                ("nominal", "Nominal"),
                                ("lower", "Lim. inf."),
                                ("upper", "Lim. sup."),
                                ("unit", "Unid."),
                            ],
                            dim_rows,
                        )
                    )

            qp8 = self._inspection_list(item, "QP8", "qp8")

            if qp8:
                text_rows = []

                for test in qp8:
                    if not isinstance(test, dict):
                        continue

                    text_rows.append(
                        {
                            "operation": test.get("QP8_OPERAC") or "",
                            "test": test.get("QP8_ENSAIO") or "",
                            "text": test.get("QP8_TEXTO") or "",
                        }
                    )

                if text_rows:
                    sections.append("")
                    sections.append("*Ensaios textuais / referências*")
                    sections.extend(
                        self._markdown_table(
                            [
                                ("operation", "Op."),
                                ("test", "Ensaio"),
                                ("text", "Texto / referência"),
                            ],
                            text_rows,
                        )
                    )

        if shallow:
            shallow_rows = []

            for item in shallow[:20]:
                product_code = str(
                    item.get("product")
                    or item.get("product_code")
                    or item.get("Product")
                    or "?"
                ).strip()
                parent_code = str(
                    item.get("parentCode")
                    or item.get("parentcode")
                    or item.get("Parentcode")
                    or ""
                ).strip()
                level = item.get("level", item.get("Nível", item.get("bom_level", "")))

                shallow_rows.append(
                    {
                        "product_code": product_code,
                        "parent_code": parent_code or "—",
                        "level": level,
                        "plan": self._presenter_text("generic", "emptyPlan"),
                    }
                )

            if shallow_rows:
                sections.append("")
                sections.append("*Componentes referenciados (sem plano expandido)*")
                sections.extend(
                    self._markdown_table(
                        [
                            ("product_code", "Componente"),
                            ("parent_code", "Produto pai"),
                            ("level", "Nível"),
                            ("plan", "Plano"),
                        ],
                        shallow_rows,
                    )
                )

            if len(shallow) > 20:
                sections.append(
                    self._presenter_text(
                        "pagination",
                        "moreComponents",
                        count=str(len(shallow) - 20),
                    )
                )

        if len(detailed) > 6:
            sections.append(
                self._presenter_text(
                    "pagination",
                    "moreDetailedProducts",
                    count=str(len(detailed) - 6),
                )
            )

        return sections

    def _build_product_analyser_collection_sections(self, root: dict) -> list[str]:
        sections: list[str] = []

        guide = root.get("guide")

        if isinstance(guide, dict):
            guide_items = guide.get("items") or []

            if guide_items:
                if not self._build_product_analyser_guide_table(root):
                    sections.extend(self._build_product_analyser_guide_markdown(guide_items))
            else:
                sections.append(
                    self._presenter_text("analyserCollections", "guideEmpty")
                )

        inspection = root.get("inspection")

        if isinstance(inspection, dict):
            inspection_items = inspection.get("items") or []

            if inspection_items:
                if not self._build_product_analyser_inspection_table(root):
                    sections.extend(
                        self._build_product_analyser_inspection_markdown(inspection_items)
                    )
            else:
                sections.append(
                    self._presenter_text("analyserCollections", "inspectionEmpty")
                )

        return sections

    def _build_product_analyser_body_lines(
        self,
        root: dict,
        product: dict,
        *,
        compact_for_rich_ui: bool = False,
    ) -> list[str]:
        from app.domain.services.chat_product_analyser_divergence_service import (
            ChatProductAnalyserDivergenceService,
        )

        lines: list[str] = []

        if not compact_for_rich_ui:
            opening = ChatProductAnalyserDivergenceService.build_opening_narrative(
                root,
                product,
            )

            if opening:
                lines.extend(["", opening, ""])

            lines.extend(self._build_product_analyser_profile_lines(product))
            lines.extend(self._build_product_analyser_collection_sections(root))

        insights = self._build_product_analyser_insights(root, product)

        if compact_for_rich_ui:
            from app.domain.services.chat_presentation_section_availability_service import (
                ChatPresentationSectionAvailabilityService,
            )

            insights = ChatPresentationSectionAvailabilityService.filter_analyser_highlights(
                insights,
            )

        if insights:
            lines.extend(["", self._analyser_markdown("highlightsHeader"), ""])
            lines.extend(f"- {line}" for line in insights)

        attention = ChatProductAnalyserDivergenceService.build_attention_points(
            root,
            product,
        )

        if attention:
            lines.extend(["", self._analyser_markdown("attentionHeader"), ""])
            lines.extend(
                f"{index}. {point}"
                for index, point in enumerate(attention, start=1)
            )

        structure = root.get("structure")

        if (
            not compact_for_rich_ui
            and isinstance(structure, dict)
            and (structure.get("items") or structure.get("total"))
        ):
            lines.extend(
                [
                    "",
                    self._presenter_text(
                        "analyserCollections", "structureVisualizationHint"
                    ),
                ]
            )

        return [line for line in lines if line is not None]

    def _format_collection_item_lines(self, items: list) -> list[str]:
        lines: list[str] = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            if self._has_protheus_inspection_blocks(item):
                lines.extend(self._build_product_analyser_inspection_markdown([item]))
                continue

            formatted = self._format_guide_like_item(item)

            if formatted:
                lines.append(formatted)
                continue

            preview = ", ".join(
                f"{self._humanize_key(key)}={value}"
                for key, value in list(item.items())[:6]
                if value not in (None, "", [], {})
            )
            lines.append(f"- {preview}")

        if len(items) > 12:
            lines.append(
                self._presenter_text(
                    "pagination",
                    "moreRecords",
                    count=str(len(items) - 12),
                )
            )

        return lines

    def _format_guide_like_item(self, item: dict) -> str | None:
        operations = item.get("operations")

        if not isinstance(operations, list) or not operations:
            op_desc = str(item.get("operation_description") or "").strip()

            if op_desc:
                product_code = str(item.get("product_code") or "?").strip()
                level = item.get("bom_level", 0)
                op_code = str(item.get("operation_code") or "").strip()
                center = str(item.get("work_center") or "").strip()
                label = f"Op. **{op_code}**" if op_code else "Operação"
                center_part = f" ({center})" if center else ""

                return (
                    f"- Produto **{product_code}** (BOM {level}): "
                    f"{label} — {op_desc}{center_part}."
                )

            return None

        product_code = str(item.get("product_code") or "?").strip()
        level = item.get("bom_level", 0)
        op_parts: list[str] = []

        for operation in operations[:6]:
            if not isinstance(operation, dict):
                continue

            op_desc = str(operation.get("operation_description") or "").strip()

            if not op_desc:
                continue

            op_code = str(operation.get("operation_code") or "").strip()
            center = str(operation.get("work_center") or "").strip()
            label = f"**{op_code}** {op_desc}" if op_code else f"**{op_desc}**"

            if center:
                label = f"{label} ({center})"

            op_parts.append(label)

        if not op_parts:
            return None

        joined = "; ".join(op_parts)

        return f"- Produto **{product_code}** (BOM {level}): {joined}."


    def _build_product_analyser_insights(self, root: dict, product: dict) -> list[str]:
        insights: list[str] = []
        code = str(product.get("code") or "").strip()
        product_type = str(product.get("type") or "").strip()
        structure = root.get("structure") if isinstance(root.get("structure"), dict) else {}
        items = structure.get("items") if isinstance(structure.get("items"), list) else []

        mp_codes: set[str] = set()
        mp_usage: dict[str, set[str]] = {}

        for item in items:
            if not isinstance(item, dict):
                continue

            parent_code = str(item.get("code") or "").strip()

            for component in item.get("components") or []:
                if not isinstance(component, dict):
                    continue

                component_code = str(component.get("code") or "").strip()

                if not component_code:
                    continue

                if str(component.get("type") or "").upper() == "MP":
                    mp_codes.add(component_code)

                mp_usage.setdefault(component_code, set()).add(parent_code)

        if items:
            insights.append(
                f"Estrutura com {len(items)} item(ns) de nível 1 "
                f"e {len(mp_codes)} matéria(s)-prima(s) distinta(s)."
            )

        shared_components = sorted(
            code
            for code, parents in mp_usage.items()
            if len({parent for parent in parents if parent}) > 1
        )

        if shared_components:
            insights.append(
                self._analyser_markdown(
                    "sharedComponents",
                    sample=", ".join(shared_components),
                )
            )

        last_purchase_price = product.get("last_purchase_price")
        last_purchase_date = str(product.get("last_purchase_date") or "").strip()

        if last_purchase_price in (0, 0.0, None) and not last_purchase_date:
            insights.append(self._analyser_markdown("noRecentPurchaseProduct"))

        standard_cost = product.get("standard_cost")

        if standard_cost not in (None, ""):
            insights.append(
                self._analyser_markdown(
                    "standardCost",
                    cost=self._format_currency(standard_cost),
                )
            )

        if self._collection_is_empty(root.get("guide")):
            insights.append("Roteiro de produção ainda não cadastrado.")

        if self._collection_is_empty(root.get("inspection")):
            insights.append("Plano de inspeção ainda não cadastrado.")

        blocked = str(product.get("blocked") or "").strip()

        if blocked and blocked not in {"N", "0"}:
            insights.append(f"Produto com indicador de bloqueio «{blocked}».")

        return insights

    def _flatten_analyser_structure_rows(self, structure: dict | None) -> list[dict]:
        if not isinstance(structure, dict):
            return []

        rows: list[dict] = []
        level1_items = structure.get("items") or []

        for item in level1_items:
            if not isinstance(item, dict):
                continue

            parent_code = item.get("code")
            parent_description = item.get("description")
            components = item.get("components") or []

            if components:
                for component in components:
                    if not isinstance(component, dict):
                        continue

                    rows.append(
                        {
                            "parent_code": parent_code,
                            "parent_description": parent_description,
                            "component_code": component.get("code"),
                            "description": component.get("description"),
                            "type": component.get("type"),
                            "unit": component.get("unit"),
                            "quantity": component.get("quantity"),
                        }
                    )
            else:
                rows.append(
                    {
                        "parent_code": "",
                        "parent_description": "",
                        "component_code": item.get("code"),
                        "description": item.get("description"),
                        "type": item.get("type"),
                        "unit": item.get("unit"),
                        "quantity": item.get("quantity"),
                    }
                )

        return rows

    def _build_analyser_structure_components_table(
        self,
        structure: dict | None,
    ) -> dict | None:
        rows = self._flatten_analyser_structure_rows(structure)

        if not rows:
            return None

        product_code = ""

        if isinstance(structure, dict) and isinstance(structure.get("root"), dict):
            product_code = str(structure["root"].get("code") or "").strip()

        title = (
            f"Componentes da estrutura {product_code}"
            if product_code
            else "Componentes da estrutura"
        )

        return {
            "type": "table",
            "title": title,
            "columns": self._column_labels.fixed_table_columns(
                "analyserStructureComponents",
                schema_labels=self._active_schema_labels,
            ),
            "rows": rows,
        }

    def _build_product_analyser_profile_table(self, product: dict, root: dict) -> dict:
        columns = self._column_labels.kv_table_column_defs()
        rows = self._column_labels.build_kv_profile_rows(
            product,
            extended=True,
            schema_labels=self._active_schema_labels,
        )

        for key in ("guide", "inspection", "structure"):
            value = root.get(key)

            if isinstance(value, dict) and value.get("total") is not None:
                rows.append(
                    {
                        "campo": self._label_collection(key),
                        "valor": self._column_labels.format_collection_total(value["total"]),
                    }
                )

        return {
            "type": "table",
            "title": f"Produto {product.get('code', '')}",
            "columns": columns,
            "rows": rows,
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

        linhas = [f"Produto {code}: {desc}."]

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

        title = f"Dados do produto {code}"
        if "prices" in root:
            title = f"Preços do produto {code}"
        elif "stock" in root:
            title = f"Estoque do produto {code}"
        elif "purchases" in root:
            title = f"Compras do produto {code}"
        elif "sales" in root or "billing" in root:
            title = f"Vendas do produto {code}"
        elif "open_orders" in root:
            title = f"Pedidos em aberto do produto {code}"

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

    def _present_lmp_page(self, root: dict) -> dict | None:
        items = root.get("items")

        if not isinstance(items, list):
            return None

        if items and isinstance(items[0], dict) and "sale_number" not in items[0] and "saleNumber" not in items[0]:
            return None

        if not items:
            return None

        total = root.get("total")
        linhas = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            ov = item.get("sale_number") or item.get("saleNumber")
            desc = item.get("sale_description") or item.get("saleDescription") or ""
            status = item.get("status") or item.get("engineering_status") or ""
            kind = item.get("listing_kind") or item.get("listingKind") or ""
            branch = item.get("branch") or ""

            parts = [str(part) for part in [ov, kind, status, branch] if part]
            header = " · ".join(parts) if parts else "LMP"
            line = f"OV {header}: {desc}".strip(": ")

            if line:
                linhas.append(line.rstrip(": "))

        if total is not None:
            linhas.append(
                self._presenter_text(
                    "pagination",
                    "lmpPageTotal",
                    total=str(total),
                    page=str(root.get("page", 1)),
                )
            )

        return {
            "titulo": self._presenter_text("pagination", "lmpTitle"),
            "linhas": linhas
            or [self._presenter_text("pagination", "lmpEmptyPage")],
            "dados": {"total": total, "items": items[:12]},
        }

    def _present_lmp_detail(self, root: dict) -> dict | None:
        sale_number = root.get("sale_number") or root.get("saleNumber")

        if not sale_number:
            return None

        desc = root.get("sale_description") or root.get("saleDescription") or ""
        status = root.get("engineering_status") or root.get("status") or ""
        kind = root.get("listing_kind") or root.get("listingKind") or ""
        branch = root.get("branch") or ""
        customer = root.get("costumer_name") or root.get("customer_name") or ""
        seller = root.get("seller_name") or ""
        qtd_pi = root.get("qtd_pi")

        linhas = [
            self._route_presentation(
                "lmp",
                "ovHeader",
                sale_number=str(sale_number),
                desc=str(desc).strip(": "),
            ).strip(": "),
        ]

        if kind:
            linhas.append(self._route_presentation("lmp", "kind", kind=str(kind)))

        if branch:
            linhas.append(self._route_presentation("lmp", "branch", branch=str(branch)))

        if status:
            linhas.append(self._route_presentation("lmp", "status", status=str(status)))

        if customer:
            linhas.append(
                self._route_presentation("lmp", "customer", customer=str(customer))
            )

        if seller:
            linhas.append(self._route_presentation("lmp", "seller", seller=str(seller)))

        if qtd_pi is not None:
            linhas.append(self._route_presentation("lmp", "piQuantity", qtd=str(qtd_pi)))

        products = root.get("list_products") or root.get("listProducts") or []

        if isinstance(products, list):
            linhas.append(
                self._route_presentation(
                    "lmp", "productsCount", count=str(len(products))
                )
            )

        return {
            "titulo": self._route_presentation(
                "lmp", "detailTitle", sale_number=str(sale_number)
            ),
            "linhas": [line for line in linhas if line],
            "dados": root,
        }

    def _present_sql_rows(self, rows: list) -> dict | None:
        default_title = ExternalActionResponseContentService.get("sql", "defaultTitle")

        if not rows:
            return {
                "titulo": default_title,
                "linhas": [
                    ExternalActionResponseContentService.get("sql", "emptyNoRows")
                ],
                "dados": {"rows": []},
            }

        if not isinstance(rows[0], dict):
            return {
                "titulo": default_title,
                "linhas": [
                    ExternalActionResponseContentService.format(
                        "sql",
                        "rowsCount",
                        count=len(rows),
                    )
                ],
                "dados": {"rows": rows},
            }

        return self._present_sql_dict_rows(rows)

    def _present_sql_resultsets(self, root: dict, path: str) -> dict | None:
        resultsets = root.get("resultsets")

        if not isinstance(resultsets, list):
            return None

        rows = self._collect_sql_resultset_rows(resultsets)
        record_total = self._sql_resultset_record_total(resultsets)
        title = self._sql_result_title(root, path)

        if not rows:
            return {
                "titulo": title,
                "linhas": [self._sql_empty_message(root, path)],
                "dados": root,
                "sqlRows": [],
            }

        presented = self._present_sql_dict_rows(
            rows,
            title=title,
            record_total=record_total,
        )
        presented["dados"] = root
        presented["sqlRows"] = rows
        return presented

    def _collect_sql_resultset_rows(self, resultsets: list) -> list[dict]:
        rows: list[dict] = []

        for resultset in resultsets:
            if not isinstance(resultset, dict):
                continue

            data = resultset.get("data")

            if not isinstance(data, list):
                continue

            for row in data:
                if isinstance(row, dict):
                    rows.append(row)

        return rows

    @staticmethod
    def _sql_resultset_record_total(resultsets: list) -> int | None:
        best: int | None = None

        for resultset in resultsets:
            if not isinstance(resultset, dict):
                continue

            try:
                total = int(resultset.get("total"))
            except (TypeError, ValueError):
                continue

            if total < 0:
                continue

            best = max(best or 0, total)

        return best

    def _sql_result_title(self, root: dict, path: str) -> str:
        if self._looks_like_inventory_below_minimum_sql_context(root, path):
            return ExternalActionResponseContentService.get(
                "inventoryBelowMinimum",
                "title",
            )

        if self._looks_like_production_sql_context(root, path):
            schedule = self._resolve_production_schedule_from_root(root)
            if schedule:
                return schedule.title
            return ExternalActionResponseContentService.get(
                "productionSchedule",
                "titleTodayFallback",
            )

        if ExternalActionSqlCapabilityService.is_sql_execution_context(path=path) or (
            ExternalActionSqlCapabilityService.is_sql_result_payload(root)
        ):
            return ExternalActionResponseContentService.get("sql", "defaultTitle")

        return ExternalActionResponseContentService.get("sql", "defaultTitle")

    def _sql_empty_message(self, root: dict, path: str) -> str:
        if self._looks_like_inventory_below_minimum_sql_context(root, path):
            return ExternalActionResponseContentService.get(
                "inventoryBelowMinimum",
                "emptyMessage",
            )

        if self._looks_like_production_sql_context(root, path):
            schedule = self._resolve_production_schedule_from_root(root)
            if schedule:
                return schedule.empty_message
            return ExternalActionResponseContentService.get(
                "productionSchedule",
                "emptyTodayFallback",
            )

        if ExternalActionSqlCapabilityService.is_sql_execution_context(path=path) or (
            ExternalActionSqlCapabilityService.is_sql_result_payload(root)
        ):
            total = root.get("total_resultsets")

            if total is not None:
                return ExternalActionResponseContentService.format(
                    "sql",
                    "emptyWithResultsets",
                    total=total,
                )

            return ExternalActionResponseContentService.get("sql", "emptyNoRows")

        total = root.get("total_resultsets")

        if total is not None:
            return ExternalActionResponseContentService.format(
                "sql",
                "emptyWithResultsets",
                total=total,
            )

        return ExternalActionResponseContentService.get("sql", "emptyNoRows")

    def _resolve_production_schedule_from_root(self, root: dict):
        from app.domain.services.chat_sql_production_schedule_date_service import (
            ChatSqlProductionScheduleDateService,
        )

        if not isinstance(root, dict):
            return None

        for key in ("sql", "query", "statement", "executedSql"):
            value = root.get(key)
            if isinstance(value, str) and value.strip():
                return ChatSqlProductionScheduleDateService.infer_from_sql(value)

        dados = root.get("dados")

        if isinstance(dados, dict):
            for key in ("sql", "query", "statement", "executedSql"):
                value = dados.get(key)

                if isinstance(value, str) and value.strip():
                    return ChatSqlProductionScheduleDateService.infer_from_sql(value)

        return None

    def _looks_like_production_sql_context(self, root: dict, path: str) -> bool:
        rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])

        if rows and self._looks_like_production_schedule_row(rows[0]):
            return True

        resultsets = root.get("resultsets") if isinstance(root, dict) else None
        if isinstance(resultsets, list):
            for resultset in resultsets:
                if not isinstance(resultset, dict):
                    continue
                columns = resultset.get("columns") or []
                if any(
                    column in columns
                    for column in (
                        "COD_PRODUTO",
                        "DESCRICAO_PRODUTO",
                        "QTD_PLANEJADA",
                    )
                ):
                    return True

        if not isinstance(root, dict):
            return False

        for key in ("sql", "query", "statement"):
            value = root.get(key)
            if isinstance(value, str) and ExternalActionSqlCapabilityService.looks_like_production_schedule_sql(
                value
            ):
                return True

        return False

    def _looks_like_inventory_below_minimum_sql_context(self, root: dict, path: str) -> bool:
        rows = self._collect_sql_resultset_rows(root.get("resultsets") or [])

        if rows and self._looks_like_inventory_below_minimum_row(rows[0]):
            return True

        resultsets = root.get("resultsets") if isinstance(root, dict) else None

        if isinstance(resultsets, list):
            for resultset in resultsets:
                if not isinstance(resultset, dict):
                    continue

                columns = {
                    str(column).lower()
                    for column in (resultset.get("columns") or [])
                }

                if {"product_code", "minimum_stock"}.issubset(columns):
                    return True

        if not isinstance(root, dict):
            return False

        for key in ("sql", "query", "statement"):
            value = root.get(key)

            if isinstance(value, str) and ExternalActionSqlCapabilityService.looks_like_inventory_below_minimum_sql(
                value
            ):
                return True

        return False

    def _looks_like_inventory_below_minimum_row(self, row: dict) -> bool:
        if not isinstance(row, dict):
            return False

        keys = {str(key).lower() for key in row.keys()}

        return "product_code" in keys and (
            "minimum_stock" in keys or "available_quantity" in keys
        )

    def _present_sql_dict_rows(
        self,
        rows: list[dict],
        *,
        title: str | None = None,
        record_total: int | None = None,
    ) -> dict:
        resolved_title = title or ExternalActionResponseContentService.get(
            "sql",
            "defaultTitle",
        )
        shown = len(rows)
        total_count = record_total if record_total is not None and record_total >= shown else shown

        linhas = [
            ExternalActionResponseContentService.format(
                "sql",
                "rowsCount",
                count=total_count,
            )
        ]

        if total_count > shown:
            linhas.append(
                ExternalActionResponseContentService.format(
                    "sql",
                    "moreProducts",
                    count=total_count - shown,
                )
            )

        return {
            "titulo": resolved_title,
            "linhas": linhas,
            "dados": {"rows": rows, "total": total_count, "shown": shown},
            "sqlRows": rows,
        }

    def _looks_like_production_schedule_row(self, row: dict) -> bool:
        if not isinstance(row, dict):
            return False

        keys = {str(key).upper() for key in row.keys()}

        return "COD_PRODUTO" in keys and (
            "DESCRICAO_PRODUTO" in keys or "QTD_PLANEJADA" in keys
        )

    def _format_production_schedule_row(self, row: dict) -> str:
        code = str(
            row.get("COD_PRODUTO")
            or row.get("cod_produto")
            or "?"
        ).strip()
        description = str(
            row.get("DESCRICAO_PRODUTO")
            or row.get("descricao_produto")
            or ""
        ).strip()
        quantity = row.get("QTD_PLANEJADA")
        unit = str(row.get("UNIDADE") or row.get("unidade") or "").strip()
        start_at = row.get("DATA_INICIO_OPERACAO") or row.get("data_inicio_operacao")

        parts = [f"**`{code}`**"]

        if description:
            parts.append(description)

        line = " — ".join(parts)

        if quantity is not None:
            qty_text = self._format_num(quantity)
            suffix = f" {unit}".rstrip()
            line += f" · **{qty_text}{suffix}**"

        if start_at:
            line += (
                f"{ExternalActionResponseContentService.get('sql', 'operationStartPrefix')}"
                f"{start_at}"
            )

        return line

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

            parts = [f"**{item_code}**"]

            if item_desc:
                parts.append(item_desc)

            if item_type:
                parts.append(f"({item_type})")

            line = " — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "")

            if quantity is not None:
                line += f" — qtd **{self._format_num(quantity)}**"

            linhas.append(f"- {line}")

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

    def _present_product_search(self, root: dict, items: list, *, title: str | None = None) -> dict:
        titulo = title or self._route_presentation("productSearch", "defaultTitle")
        total = root.get("total")
        is_hierarchy = titulo and ("pai" in titulo.lower() or "estrutura" in titulo.lower())

        if not items:
            return {
                "titulo": titulo,
                "linhas": [self._route_presentation("productSearch", "emptySearch")],
                "dados": root,
            }

        linhas = []

        for item in items:
            if not isinstance(item, dict):
                continue

            code = item.get("code") or "?"
            desc = item.get("description") or ""
            tipo = item.get("type") or ""
            unit = item.get("unit") or ""
            qty = item.get("quantity")
            level = item.get("level")

            parts = [f"**{code}**"]
            if desc:
                parts.append(desc)
            if tipo:
                parts.append(f"({tipo})")
            if unit:
                parts.append(f"[{unit}]")

            line = " — ".join(parts[:2]) + (f" {parts[2]}" if len(parts) > 2 else "") + (f" {parts[3]}" if len(parts) > 3 else "")

            if is_hierarchy:
                extras = []
                if qty is not None:
                    extras.append(f"Qtd: {qty}")
                if level is not None:
                    extras.append(f"Nível: {level}")
                if extras:
                    line += f" | {', '.join(extras)}"

            linhas.append(line)

        if total is not None and total > len(items):
            linhas.append(
                self._route_presentation(
                    "productSearch", "totalFound", total=str(total)
                )
            )

        return {
            "titulo": titulo,
            "linhas": linhas or [self._route_presentation("productSearch", "empty")],
            "dados": {"total": total, "items": [{"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")} for i in items]},
        }

    def _present_sale_orders(self, root: dict, items: list) -> dict:
        total = root.get("total")

        if not items:
            return {
                "titulo": self._route_presentation("saleOrders", "title"),
                "linhas": [self._route_presentation("saleOrders", "emptyPeriod")],
                "dados": root,
            }

        linhas = []

        for item in items[:12]:
            if not isinstance(item, dict):
                continue

            order = item.get("order_number") or "?"
            desc = item.get("description") or ""
            branch = item.get("branch") or ""
            date = item.get("date") or ""
            stage = item.get("stage") or ""

            parts = [f"OV {order}"]
            if branch:
                parts.append(f"Fil. {branch}")
            if date:
                parts.append(date)
            if stage:
                parts.append(stage)

            header = " · ".join(parts)
            line = f"{header}: {desc}".rstrip(": ") if desc else header
            linhas.append(line)

        if total is not None:
            linhas.append(
                self._presenter_text(
                    "pagination",
                    "saleOrdersPageTotal",
                    total=str(total),
                    page=str(root.get("page", 1)),
                )
            )

        return {
            "titulo": self._route_presentation("saleOrders", "title"),
            "linhas": linhas or [self._route_presentation("saleOrders", "empty")],
            "dados": {"total": total, "items": items[:12]},
        }

    def _present_product_guide(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        titulo = (
            title
            or self._infer_items_title(items, path)
            or self._route_presentation("guide", "defaultTitle")
        )
        product_code = self._extract_product_code_from_path(path)

        main_ops: list[tuple[str, str, str | None]] = []
        component_products: set[str] = set()

        for item in items:
            if not isinstance(item, dict):
                continue

            level = item.get("bom_level", 0)
            op_desc = str(item.get("operation_description") or "").strip()
            op_code = str(item.get("operation_code") or "").strip()
            prod = str(item.get("product_code") or "").strip()
            work_center = str(item.get("work_center") or "").strip() or None

            if not product_code and level == 0 and prod:
                product_code = prod

            if level == 0 and op_desc:
                main_ops.append((op_code, op_desc, work_center))
            elif level and prod:
                component_products.add(prod)

        linhas: list[str] = []

        if product_code and main_ops:
            ops_preview = ", ".join(
                f"**{code}** {desc}" if code else f"**{desc}**"
                for code, desc, _ in main_ops
            )
            linhas.append(
                self._route_presentation(
                    "guide",
                    "mainOps",
                    code=product_code,
                    count=str(len(main_ops)),
                    preview=ops_preview,
                )
            )
        elif product_code:
            linhas.append(
                self._route_presentation(
                    "guide",
                    "queryOnly",
                    code=product_code,
                    count=str(len(items)),
                )
            )

        if component_products:
            preview_codes = ", ".join(sorted(component_products)[:5])
            suffix = "…" if len(component_products) > 5 else ""
            linhas.append(
                self._route_presentation(
                    "guide",
                    "bomComponents",
                    count=str(len(component_products)),
                    preview=preview_codes,
                    suffix=suffix,
                )
            )

        for op_code, op_desc, work_center in main_ops:
            center_part = (
                self._route_presentation(
                    "guide", "workCenterSuffix", center=str(work_center)
                )
                if work_center
                else ""
            )
            label = (
                self._route_presentation("guide", "operationWithCode", code=op_code)
                if op_code
                else self._route_presentation("guide", "operationGeneric")
            )
            linhas.append(
                self._route_presentation(
                    "guide",
                    "operationLine",
                    label=label,
                    desc=op_desc,
                    center=center_part,
                )
            )

        if not linhas:
            linhas = [
                self._route_presentation(
                    "guide", "apiFallback", count=str(len(items))
                )
            ]

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items,
                "product_code": product_code,
                "total": len(items),
            },
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

    def _present_product_inspection(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        titulo = (
            title
            or self._infer_items_title(items, path)
            or self._route_presentation("inspection", "defaultTitle")
        )
        product_code = self._extract_product_code_from_path(path)
        linhas: list[str] = []

        if items and isinstance(items[0], dict) and "has_inspection" in items[0]:
            with_plan = [item for item in items if item.get("has_inspection")]
            without_plan = len(items) - len(with_plan)

            if product_code:
                linhas.append(
                    self._route_presentation(
                        "inspection",
                        "planWithProduct",
                        code=product_code,
                        count=str(len(items)),
                    )
                )
            else:
                linhas.append(
                    self._route_presentation(
                        "inspection",
                        "planGeneric",
                        count=str(len(items)),
                    )
                )

            linhas.append(
                self._route_presentation(
                    "inspection", "withPlanCount", count=str(len(with_plan))
                )
            )

            if without_plan:
                linhas.append(
                    self._route_presentation(
                        "inspection", "withoutPlanCount", count=str(without_plan)
                    )
                )

            for item in with_plan:
                if not isinstance(item, dict):
                    continue

                item_code = str(item.get("product_code") or "?").strip()
                header = item.get("header") if isinstance(item.get("header"), dict) else {}
                header_desc = str(header.get("description") or "").strip()
                measurable = item.get("measurable_tests") or []
                textual = item.get("textual_tests") or []
                measurable_count = len(measurable) if isinstance(measurable, list) else 0
                textual_count = len(textual) if isinstance(textual, list) else 0

                from app.domain.services.chat_product_operational_content_service import (
                    ChatProductOperationalContentService,
                )

                summary = header_desc or ChatProductOperationalContentService.get(
                    "presenter",
                    "inspection",
                    "summaryFallback",
                )
                linhas.append(
                    self._route_presentation(
                        "inspection",
                        "itemLine",
                        code=item_code,
                        summary=summary,
                        measurable=str(measurable_count),
                        textual=str(textual_count),
                    )
                )

                if isinstance(measurable, list):
                    for test in measurable[:3]:
                        if not isinstance(test, dict):
                            continue

                        label = test.get("test_code") or test.get("sequence") or "Teste"
                        unit = test.get("unit") or ""
                        nominal = test.get("nominal_value")
                        lower = test.get("lower_spec_limit")
                        upper = test.get("upper_spec_limit")
                        spec_parts = []

                        if nominal is not None:
                            spec_parts.append(f"nominal {nominal}{unit}")

                        if lower is not None or upper is not None:
                            spec_parts.append(f"limites {lower or '—'} a {upper or '—'}{unit}")

                        if spec_parts:
                            linhas.append(
                                self._route_presentation(
                                    "inspection",
                                    "testLimits",
                                    label=str(label),
                                    specs=", ".join(spec_parts),
                                )
                            )

            if len(with_plan) > 8:
                linhas.append(
                    self._presenter_text(
                        "pagination",
                        "moreInspectionItems",
                        count=str(len(with_plan) - 8),
                    )
                )

            return {
                "titulo": titulo,
                "linhas": linhas,
                "dados": {
                    "items": items,
                    "product_code": product_code,
                    "total": len(items),
                },
            }

        linhas.append(
            self._route_presentation(
                "inspection", "characteristicsPlan", count=str(len(items))
            )
        )

        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            characteristic = (
                item.get("characteristic")
                or item.get("specification")
                or item.get("step_description")
                or item.get("description")
                or "?"
            )
            inspection_type = item.get("inspection_type") or item.get("method") or ""
            sequence = item.get("sequence") or item.get("step") or ""
            parts = [f"**{characteristic}**"]

            if inspection_type:
                parts.append(f"tipo {inspection_type}")

            if sequence not in (None, ""):
                parts.append(f"seq. {sequence}")

            linhas.append(f"- {' — '.join(str(part) for part in parts)}")

        if len(items) > 10:
            linhas.append(
                self._presenter_text(
                    "pagination",
                    "moreCharacteristics",
                    count=str(len(items) - 10),
                )
            )

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items,
                "product_code": product_code,
                "total": len(items),
            },
        }

    def _present_product_stock(
        self,
        items: list,
        *,
        path: str = "",
        title: str | None = None,
    ) -> dict:
        titulo = title or self._infer_items_title(items, path) or "Estoque do produto"
        product_code = self._extract_product_code_from_path(path)
        branches: set[str] = set()
        warehouses: set[str] = set()
        total_available = 0.0
        total_current = 0.0
        has_available = False
        has_current = False
        detail_lines: list[str] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            branch = str(item.get("branch") or "").strip()
            warehouse = str(item.get("warehouse") or "").strip()

            if branch:
                branches.add(branch)

            if warehouse:
                warehouses.add(warehouse)

            available = item.get("available_quantity")
            current = item.get("current_quantity")

            if available is not None:
                has_available = True
                total_available += float(available or 0)

            if current is not None:
                has_current = True
                total_current += float(current or 0)

            from app.domain.services.chat_product_operational_content_service import (
                ChatProductOperationalContentService,
            )

            detail_lines.append(
                ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "detailLine",
                    branch=item.get("branch") or "—",
                    warehouse=item.get("warehouse") or "—",
                    current=self._format_num(item.get("current_quantity")),
                    available=self._format_num(item.get("available_quantity")),
                    committed=self._format_num(item.get("committed_quantity")),
                    location=item.get("physical_location")
                    or ChatProductOperationalContentService.get(
                        "presenter",
                        "stock",
                        "locationFallback",
                    ),
                )
            )

        linhas: list[str] = []
        branch_count = len(branches)
        warehouse_count = len(warehouses)

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        if product_code:
            summary = ChatProductOperationalContentService.format(
                "presenter",
                "stock",
                "summaryWithCode",
                code=product_code,
                positions=len(items),
            )

            if branch_count:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryBranches",
                    count=branch_count,
                    branches=", ".join(sorted(branches)),
                )

            if warehouse_count:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryWarehouses",
                    count=warehouse_count,
                    warehouses=", ".join(sorted(warehouses)),
                )

            summary += "."

            if has_available:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryAvailableTotal",
                    total=self._format_num(total_available),
                )
            elif has_current:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryCurrentTotal",
                    total=self._format_num(total_current),
                )
            else:
                summary += ChatProductOperationalContentService.get(
                    "presenter",
                    "stock",
                    "summaryNoAvailable",
                )

            linhas.append(summary)
        else:
            summary = ChatProductOperationalContentService.format(
                "presenter",
                "stock",
                "summaryWithoutCode",
                positions=len(items),
            )

            if branch_count:
                summary += ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "summaryWithoutCodeBranches",
                    count=branch_count,
                )
            else:
                summary += "."

            linhas.append(summary)

        if len(detail_lines) > 8:
            linhas.append(
                ChatProductOperationalContentService.format(
                    "presenter",
                    "stock",
                    "textModeDetailHint",
                    lines=len(detail_lines),
                )
            )

        return {
            "titulo": titulo,
            "linhas": linhas,
            "linhas_detalhe": detail_lines,
            "dados": {
                "items": items,
                "product_code": product_code,
                "total": len(items),
            },
        }

    def _present_items(self, items: list, *, title: str | None = None) -> dict:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        titulo = title or ChatProductOperationalContentService.get(
            "presenter",
            "items",
            "defaultTitle",
        )
        linhas = [
            ChatProductOperationalContentService.format(
                "presenter",
                "items",
                "apiReturned",
                count=len(items),
            )
        ]

        detail_lines = []
        for item in items[:10]:
            if not isinstance(item, dict):
                continue

            if "warehouse" in item and "available_quantity" in item:
                if not title:
                    titulo = "Estoque do produto"
                detail_lines.append(
                    "Filial {branch}, armazém {warehouse}: atual {current}, disponível {available}, empenhada {committed}. Local: {location}.".format(
                        branch=item.get("branch"),
                        warehouse=item.get("warehouse"),
                        current=item.get("current_quantity"),
                        available=item.get("available_quantity"),
                        committed=item.get("committed_quantity"),
                        location=item.get("physical_location") or "não informado",
                    )
                )
            elif "supplier_name" in item or "supplier_code" in item:
                name = item.get("supplier_name") or item.get("supplier_code") or "?"
                lead = item.get("registered_lead_time_days") or item.get("real_avg_lead_time_days")
                price = item.get("last_price")
                parts = [f"**{name}**"]
                if lead is not None:
                    parts.append(f"Lead time: {lead}d")
                if price is not None:
                    parts.append(f"Últ. preço: R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                detail_lines.append(" | ".join(parts))
            elif "customer_name" in item or "customer_code" in item:
                name = item.get("customer_name") or item.get("customer_code") or "?"
                detail_lines.append(f"**{name}**")
            else:
                label_keys = ["name", "description", "supplier_name", "customer_name", "code", "number"]
                label = next((str(item[k]) for k in label_keys if item.get(k)), None)
                if label:
                    detail_lines.append(label)

        if detail_lines:
            linhas = detail_lines

        return {
            "titulo": titulo,
            "linhas": linhas,
            "dados": {
                "items": items[:15],
            },
        }

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

    def _build_product_analyser_text_presentation(
        self,
        root: dict,
        product: dict,
        path: str,
    ) -> dict | None:
        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        code = str(product.get("code") or "").strip()
        title = (
            ChatProductOperationalContentService.format(
                "presenter",
                "analyser",
                "titleWithCode",
                code=code,
            )
            if code
            else ChatProductOperationalContentService.get(
                "presenter",
                "analyser",
                "titleGeneric",
            )
        )
        from app.domain.services.chat_rich_presentation_text_service import (
            ChatRichPresentationTextService,
        )

        auxiliary_tables = self.build_analyser_auxiliary_table_presentations(root)
        compact_for_rich_ui = ChatRichPresentationTextService.should_compact_narrative(
            table_presentations=auxiliary_tables,
            tree_presentation=self.build_tree_presentation(root, path=path),
        )

        body_parts = self._build_product_analyser_body_lines(
            root,
            product,
            compact_for_rich_ui=compact_for_rich_ui,
        )
        markdown_parts = [f"### {title}", ""]

        if not compact_for_rich_ui:
            scope_line = ChatProductOperationalContentService.get(
                "presenter",
                "analyser",
                "scopeIntro",
            )
            markdown_parts.extend([scope_line, ""])

        markdown_parts.extend(body_parts)

        return {
            "type": "markdown",
            "title": title,
            "markdown": "\n".join(markdown_parts).strip(),
        }

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
            "title": title or self._fallback_title(path) or "Resultado",
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
        self._active_schema_labels = self._column_labels.resolve_schema_labels(
            response_schema
        )

        try:
            return self._build_presentation(data, path=path)
        finally:
            self._active_schema_labels = None

    def _build_presentation(self, data, *, path: str = "") -> dict | None:
        root = self._unwrap_data(data)

        if isinstance(root, list) and root and isinstance(root[0], dict):
            return self._build_items_table(root, title="Consulta SQL")

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
            return self._build_items_table(
                stock.get("items") or [],
                title="Estoque do produto",
            )

        parents = root.get("parents")
        if isinstance(parents, list) and parents:
            return self._build_items_table(parents, title="Produtos pai (onde é usado)")

        structure = root.get("structure")
        if isinstance(structure, dict) and isinstance(structure.get("items"), list):
            return self._build_items_table(
                structure["items"],
                title="Estrutura do produto",
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

        return {
            "type": "table",
            "title": f"Produto {product.get('code', '')}",
            "columns": columns,
            "rows": rows,
        }

    def _build_product_detail_table(self, product: dict, detail_list: list, root: dict) -> dict:
        code = product.get("code", "")

        title = f"Dados do produto {code}"
        if "prices" in root:
            title = f"Preços do produto {code}"
        elif "stock" in root:
            title = f"Estoque do produto {code}"
        elif "purchases" in root:
            title = f"Compras do produto {code}"
        elif "sales" in root or "billing" in root:
            title = f"Vendas do produto {code}"
        elif "open_orders" in root:
            title = f"Pedidos em aberto do produto {code}"

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

    def _build_lmp_table(self, items: list, root: dict) -> dict:
        columns = [
            {"key": "sale_number", "label": "OV"},
            {"key": "branch", "label": "Filial"},
            {"key": "listing_kind", "label": "Tipo"},
            {"key": "status", "label": "Status"},
            {"key": "sale_description", "label": "Descrição"},
        ]

        rows = []
        for item in items:
            if not isinstance(item, dict):
                continue
            rows.append({
                "sale_number": item.get("sale_number") or item.get("saleNumber"),
                "branch": item.get("branch"),
                "listing_kind": item.get("listing_kind") or item.get("listingKind"),
                "status": item.get("status") or item.get("engineering_status"),
                "sale_description": item.get("sale_description") or item.get("saleDescription"),
            })

        return {
            "type": "table",
            "title": self._route_presentation(
                "tableTitles",
                "lmps",
                total=str(root.get("total", len(rows))),
            ),
            "columns": columns,
            "rows": rows,
        }

    def _build_sale_orders_table(self, items: list, root: dict) -> dict:
        columns = [
            {"key": "order_number", "label": "OV"},
            {"key": "branch", "label": "Filial"},
            {"key": "description", "label": "Descrição"},
            {"key": "date", "label": "Data", "dataType": "date"},
            {"key": "stage", "label": "Etapa"},
        ]

        rows = [item for item in items if isinstance(item, dict)]

        return {
            "type": "table",
            "title": self._route_presentation(
                "tableTitles",
                "saleOrders",
                total=str(root.get("total", len(rows))),
            ),
            "columns": columns,
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
            columns = [
                {"key": "code", "label": "Código"},
                {"key": "description", "label": "Descrição"},
                {"key": "type", "label": "Tipo"},
                {"key": "unit", "label": "Unidade"},
            ]
            rows = [
                {"code": i.get("code"), "description": i.get("description"), "type": i.get("type"), "unit": i.get("unit")}
                for i in items
                if isinstance(i, dict)
            ]

        table_title = title or f"Busca de produtos ({root.get('total', len(rows))} resultado(s))"

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

    def _build_sql_resultset_empty_table(
        self,
        root: dict,
        *,
        title: str,
        path: str = "",
    ) -> dict | None:
        resultsets = root.get("resultsets")

        if not isinstance(resultsets, list) or not resultsets:
            return None

        first = resultsets[0]

        if not isinstance(first, dict):
            return None

        columns_raw = first.get("columns")

        if not isinstance(columns_raw, list) or not columns_raw:
            return None

        sample = {str(column): None for column in columns_raw}
        profile_name = self._column_labels.detect_table_profile(sample, path=path)
        preferred = None

        if profile_name:
            preferred = self._column_labels.preferred_columns(
                profile_name,
                sample,
                schema_labels=self._active_schema_labels,
            )

        if preferred:
            columns = [
                self._enrich_column(key, label)
                for key, label in preferred
            ]
        else:
            columns = [
                self._enrich_column(str(column), self._humanize_key(str(column)))
                for column in columns_raw[:15]
            ]

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": [],
        }

    def _build_items_table(
        self,
        items: list,
        title: str = "Dados retornados",
        *,
        path: str = "",
    ) -> dict | None:
        if not items:
            return None

        first = next((item for item in items if isinstance(item, dict)), None)

        if not first:
            return None

        profile_name = self._column_labels.detect_table_profile(first, path=path)
        preferred = None

        if profile_name:
            preferred = self._column_labels.preferred_columns(
                profile_name,
                first,
                schema_labels=self._active_schema_labels,
            )

        if preferred:
            columns = [
                self._enrich_column(key, label)
                for key, label in preferred
            ]
        else:
            columns = []

        if not columns:
            flat_items = self._flatten_nested_field(items)
            first_flat = flat_items[0] if flat_items else first
            columns = [
                self._enrich_column(key, self._humanize_key(key))
                for key in list(first_flat.keys())[:15]
                if not isinstance(first_flat.get(key), (list, dict))
            ]
            col_keys = {c["key"] for c in columns}
            rows = [
                {k: item.get(k) for k in col_keys}
                for item in flat_items
                if isinstance(item, dict)
            ]
        else:
            col_keys = {c["key"] for c in columns}
            rows = [
                {k: item.get(k) for k in col_keys}
                for item in items
                if isinstance(item, dict)
            ]

        return {
            "type": "table",
            "title": title,
            "columns": columns,
            "rows": rows,
        }

    def _humanize_key(self, key: str) -> str:
        return self._column_labels.label_for(
            key,
            schema_labels=self._active_schema_labels,
        )

    _NO_CHART_PATHS = (
        "/suppliers", "/customers", "/structure", "/parents",
        "/guide", "/inspection", "/search",
        "/purchases", "/sales", "/internal-movements",
        "/inbound-invoice", "/outbound-invoice", "/prices",
    )

    def build_dashboard_presentation(self, data, *, path: str = "") -> dict | None:
        from app.domain.services.chat_dashboard_presentation_service import (
            ChatDashboardPresentationService,
        )

        root = self._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        return ChatDashboardPresentationService.build(
            root,
            path=path,
            build_kpi=lambda summary, route: (
                (
                    {
                        "type": "kpi",
                        "title": self._kpi_title(route) or "Resumo",
                        "cards": cards,
                    }
                    if (cards := self._build_generic_kpi_cards(summary, route))
                    else None
                )
                or self._build_kpi_chart(summary, route)
            ),
            build_lmp_table=self._build_lmp_table,
            build_items_table=lambda items, title: self._build_items_table(
                items,
                title=self._infer_items_title(items, path) or title,
                path=path,
            ),
            build_items_chart=lambda items, root, route: self.build_chart_presentation(
                {**root, "items": items},
                path=route,
                force=True,
            ),
        )

    def _build_analyser_structure_type_chart(self, root: dict) -> dict | None:
        structure = root.get("structure")

        if not isinstance(structure, dict):
            return None

        counts: dict[str, int] = {}

        for item in structure.get("items") or []:
            if not isinstance(item, dict):
                continue

            components = [
                component
                for component in (item.get("components") or [])
                if isinstance(component, dict)
            ]

            if components:
                for component in components:
                    comp_type = (
                        str(component.get("type") or "Outros").strip().upper()
                        or "OUTROS"
                    )
                    counts[comp_type] = counts.get(comp_type, 0) + 1
                continue

            comp_type = str(item.get("type") or "Outros").strip().upper() or "OUTROS"
            counts[comp_type] = counts.get(comp_type, 0) + 1

        if len(counts) < 2:
            return None

        labels = [f"{key} ({value})" for key, value in sorted(counts.items(), key=lambda pair: -pair[1])]
        values = [value for _, value in sorted(counts.items(), key=lambda pair: -pair[1])]

        return {
            "type": "chart",
            "chartType": "donut",
            "title": "Composição por tipo de componente",
            "labels": labels,
            "datasets": [{"label": "Itens", "data": values}],
        }

    def build_chart_presentation(self, data, *, path: str = "", force: bool = False) -> dict | None:
        """Gera presentation tipo chart APENAS quando dados são naturalmente visuais."""
        if not force:
            lowered_path = (path or "").lower()
            if any(token in lowered_path for token in self._NO_CHART_PATHS):
                return None

        root = self._unwrap_data(data)

        if isinstance(root, dict) and "/analyser" in str(path or "").lower():
            normalized = self._normalize_analyser_root(root)
            analyser_chart = self._build_analyser_structure_type_chart(normalized)

            if analyser_chart:
                return analyser_chart

        if not isinstance(root, dict):
            if isinstance(root, list) and root and isinstance(root[0], dict):
                return self._try_chart_from_rows(root, force=force, path=path)
            return None

        stock_items = self._collect_stock_items(root)
        if stock_items:
            return self._build_stock_chart(stock_items)

        items = root.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            if self._is_stock_data(items[0]):
                return self._build_stock_chart(items)

            return self._try_chart_from_rows(items, force=force, path=path)

        if self._looks_like_kpi_response(root, path):
            stock_value_kpi = self._build_stock_value_kpi(root, path)

            if stock_value_kpi:
                return stock_value_kpi

            return self._build_kpi_chart(root, path)

        return None

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
        return "warehouse" in row and (
            "available_quantity" in row or "current_quantity" in row
        )

    def _collect_stock_items(self, root: dict) -> list | None:
        """Linhas de estoque em `items` na raiz ou em `stock.items`."""
        if not isinstance(root, dict):
            return None

        items = root.get("items")

        if (
            isinstance(items, list)
            and items
            and isinstance(items[0], dict)
            and self._is_stock_data(items[0])
        ):
            return items

        stock = root.get("stock")

        if isinstance(stock, dict):
            stock_items = stock.get("items")

            if (
                isinstance(stock_items, list)
                and stock_items
                and isinstance(stock_items[0], dict)
                and self._is_stock_data(stock_items[0])
            ):
                return stock_items

        return None

    def _build_stock_chart(self, items: list) -> dict | None:
        if not items:
            return None

        chart_data = []
        for item in items[:20]:
            if not isinstance(item, dict):
                continue
            label = f"Fil.{item.get('branch', '?')}/{item.get('warehouse', '?')}"
            chart_data.append({
                "name": label,
                "Qtd. atual": item.get("current_quantity") or 0,
                "Disponível": item.get("available_quantity") or 0,
                "Empenhada": item.get("committed_quantity") or 0,
            })

        if not chart_data:
            return None

        return {
            "type": "chart",
            "title": "Estoque por filial/armazém",
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": ["Qtd. atual", "Disponível", "Empenhada"],
                "colors": ["#0ea5e9", "#10b981", "#f59e0b"],
                "legend": True,
            },
        }

    def _looks_like_kpi_response(self, root: dict, path: str) -> bool:
        lowered = str(path or "").lower()

        if "/sales/billing" in lowered:
            return False

        kpi_paths = (
            "cpv", "otd", "inventory-turnover", "stock-value", "giro",
            "turnover", "kpi", "indicator", "snapshot",
            "ebitda", "pmr", "pdi", "completion",
            "closing-rate", "new-clients", "new-business",
            "depreciation", "labor_cost", "production_cost",
            "effectiveness", "delivery",
        )
        if any(token in path for token in kpi_paths):
            return True

        kpi_keys = ("value", "percentage", "current", "previous", "target", "meta")
        has_series = any(k in root for k in ("periods", "series", "history"))
        kpi_count = sum(1 for k in kpi_keys if k in root)
        if kpi_count >= 2 or (kpi_count >= 1 and has_series):
            return True

        has_nested = any(isinstance(v, (dict, list)) for v in root.values())
        if not root.get("items") and not has_nested and len(root) <= 8:
            numeric_count = sum(1 for v in root.values() if isinstance(v, (int, float)))
            if numeric_count >= 2:
                return True

        return False

    def _build_kpi_chart(self, root: dict, path: str) -> dict | None:
        periods = root.get("periods") or root.get("series") or root.get("history")
        if isinstance(periods, list) and len(periods) >= 2:
            return {
                "type": "chart",
                "title": self._kpi_title(path),
                "chartType": "line",
                "data": periods[:24],
                "config": {
                    "xAxis": "period",
                    "legend": True,
                },
            }

        value = root.get("value") or root.get("percentage") or root.get("current")
        target = root.get("target") or root.get("meta")
        previous = root.get("previous") or root.get("anterior")
        unit = root.get("unit") or root.get("unidade") or ""

        if value is not None:
            cards = []
            trend = None
            delta = None

            if previous is not None:
                try:
                    diff = float(value) - float(previous)
                    if diff > 0:
                        trend = "up"
                        delta = f"+{self._format_num(diff)}{unit}"
                    elif diff < 0:
                        trend = "down"
                        delta = f"{self._format_num(diff)}{unit}"
                    else:
                        trend = "stable"
                except (ValueError, TypeError):
                    pass

            cards.append({
                "label": "Atual",
                "value": value,
                "unit": unit,
                "trend": trend,
                "delta": delta,
                "color": "#0ea5e9",
            })

            if target is not None:
                cards.append({
                    "label": "Meta",
                    "value": target,
                    "unit": unit,
                    "color": "#10b981",
                })

            if previous is not None:
                cards.append({
                    "label": "Anterior",
                    "value": previous,
                    "unit": unit,
                    "color": "#94a3b8",
                })

            if cards:
                return {
                    "type": "kpi",
                    "title": self._kpi_title(path),
                    "cards": cards,
                }

        cards = self._build_generic_kpi_cards(root, path)
        if cards:
            return {
                "type": "kpi",
                "title": self._kpi_title(path),
                "cards": cards,
            }

        return None

    def _build_generic_kpi_cards(self, root: dict, path: str) -> list | None:
        colors = ["#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
        cards = []
        idx = 0
        for key, val in root.items():
            if not isinstance(val, (int, float)):
                continue
            cards.append({
                "label": self._humanize_key(key),
                "value": val,
                "unit": "%" if "pct" in key or "percent" in key or "rate" in key else "",
                "color": colors[idx % len(colors)],
            })
            idx += 1
            if idx >= 6:
                break
        return cards if len(cards) >= 2 else None

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

    def _presenter_text(self, section: str, key: str, *extra_path: str, **values: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        path = (section, key, *extra_path)

        if values:
            return ChatAssistantContentService.format(
                "presenter_content",
                *path,
                **values,
            )

        return ChatAssistantContentService.get("presenter_content", *path)

    def _kpi_title(self, path: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        lowered = str(path or "").lower()
        matchers = ChatAssistantContentService.get_node(
            "presenter_content",
            "kpiPathMatchers",
        )

        if isinstance(matchers, list):
            for entry in matchers:
                if not isinstance(entry, dict):
                    continue

                fragment = str(entry.get("fragment") or "").strip()
                title_key = str(entry.get("titleKey") or "").strip()

                if fragment and fragment in lowered and title_key:
                    title = ChatAssistantContentService.get(
                        "presenter_content",
                        "kpiTitles",
                        title_key,
                    )

                    if title:
                        return title

        return ChatAssistantContentService.get(
            "presenter_content",
            "kpiTitles",
            "default",
            default="Indicador",
        )

    _CHART_WORTHY_NUMERIC_KEYS = {
        "quantity", "value", "total", "amount", "price", "cost",
        "revenue", "count", "percentage", "rate", "margin",
        "qtd", "valor", "preco", "custo", "receita", "faturamento",
        "saldo", "volume", "peso", "weight",
    }

    def _try_chart_from_rows(
        self,
        rows: list,
        *,
        force: bool = False,
        path: str = "",
        user_message: str | None = None,
    ) -> dict | None:
        """Gera gráfico APENAS quando os dados são naturalmente visuais (ou force=True)."""
        if len(rows) < 2 or not isinstance(rows[0], dict):
            return None

        heatmap = self._try_heatmap_from_rows(
            rows,
            force=force,
            user_message=user_message,
        )

        if heatmap:
            return heatmap

        if not force and len(rows) > 12:
            return None

        first = rows[0]
        numeric_keys = [k for k, v in first.items() if isinstance(v, (int, float))]
        string_keys = [k for k, v in first.items() if isinstance(v, str)]

        if not numeric_keys or not string_keys:
            return None

        if force:
            chart_numeric = numeric_keys[:3]
        else:
            chart_numeric = [
                k for k in numeric_keys
                if any(token in k.lower() for token in self._CHART_WORTHY_NUMERIC_KEYS)
            ]
            if not chart_numeric:
                return None

        label_key = string_keys[0]
        labels = [str(r.get(label_key, "")) for r in rows[:12]]
        if len(set(labels)) < 2:
            return None

        from app.domain.services.chat_chart_type_selection_service import (
            ChatChartTypeSelectionService,
        )

        chart_numeric_slice = chart_numeric[:3]
        chart_type = ChatChartTypeSelectionService.resolve(
            rows=rows[:12],
            label_key=label_key,
            numeric_keys=chart_numeric_slice,
            user_message=user_message,
        )

        lowered_path = str(path or "").lower()

        if chart_type == "scatter" and (
            "eficiencia-fabril" in lowered_path or "eficiencia_fabril" in lowered_path
        ):
            if "filial" in string_keys:
                chart_type = "bar"
                label_key = "filial"

        config: dict = {
            "xAxis": label_key,
            "yAxis": chart_numeric_slice,
            "legend": len(chart_numeric_slice) > 1,
        }

        from app.domain.services.chat_presentation_axis_preference_service import (
            ChatPresentationAxisPreferenceService,
        )

        axis = ChatPresentationAxisPreferenceService.resolve(
            rows=rows[:12],
            chart_type=chart_type,
            label_key=label_key,
            numeric_keys=chart_numeric_slice,
            user_message=user_message,
        )

        config["xAxis"] = axis["xAxis"]
        config["yAxis"] = axis["yAxis"]
        config["numericColumns"] = axis["numericColumns"]
        config["categoryColumns"] = axis["categoryColumns"]

        if chart_type == "scatter":
            config["legend"] = False

        if chart_type == "combo" and len(chart_numeric_slice) >= 2:
            config["comboBarKey"] = chart_numeric_slice[0]
            config["comboLineKey"] = chart_numeric_slice[1]

        if chart_type == "gauge" and chart_numeric_slice:
            config["gaugeValueKey"] = chart_numeric_slice[0]
            config["gaugeTargetKey"] = chart_numeric_slice[1] if len(chart_numeric_slice) > 1 else None

        chart_title = self._infer_items_title(rows, path) or "Visualização dos dados"

        presentation = {
            "type": "chart",
            "title": chart_title,
            "chartType": chart_type,
            "data": rows,
            "config": config,
        }

        from app.domain.services.chat_chart_data_aggregation_service import (
            ChatChartDataAggregationService,
        )

        ChatChartDataAggregationService.apply_to_chart_presentation(presentation)

        capped = presentation.get("data") or []

        if isinstance(capped, list):
            presentation["data"] = capped[:24]

        return presentation

    def _try_heatmap_from_rows(
        self,
        rows: list,
        *,
        force: bool = False,
        user_message: str | None = None,
    ) -> dict | None:
        if len(rows) < 4 or not isinstance(rows[0], dict):
            return None

        first = rows[0]
        string_keys = [key for key, value in first.items() if isinstance(value, str)]
        numeric_keys = [key for key, value in first.items() if isinstance(value, (int, float))]

        if len(string_keys) < 2 or len(numeric_keys) != 1:
            return None

        from app.domain.services.chat_chart_type_selection_service import (
            ChatChartTypeSelectionService,
        )

        message = re.sub(r"\s+", " ", str(user_message or "").strip().lower())
        wants_heatmap = any(
            token in message
            for token in ("heatmap", "mapa de calor", "mapa calor", "matriz de intensidade")
        )

        if not force and not wants_heatmap:
            if not ChatChartTypeSelectionService._looks_heatmap_matrix(
                rows,
                string_keys,
                numeric_keys,
            ):
                return None

        x_axis, y_axis = ChatChartTypeSelectionService._pick_heatmap_axes(string_keys, rows)
        value_key = numeric_keys[0]
        capped_rows = rows[:144]

        return {
            "type": "chart",
            "title": "Mapa de calor",
            "chartType": "heatmap",
            "data": capped_rows,
            "config": {
                "xAxis": x_axis,
                "yAxis": y_axis,
                "valueKey": value_key,
                "legend": False,
            },
        }

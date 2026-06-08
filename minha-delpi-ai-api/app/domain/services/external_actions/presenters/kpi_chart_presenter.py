"""KPI e gráficos do ExternalActionResultPresenter — Fase 3A."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.domain.services.chat_api_delpi_response_profile_service import (
    ChatApiDelpiResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionKpiChartPresenter:
    _NO_CHART_PATHS = (
        "/suppliers",
        "/customers",
        "/structure",
        "/parents",
        "/guide",
        "/inspection",
        "/search",
        "/purchases",
        "/sales",
        "/internal-movements",
        "/inbound-invoice",
        "/outbound-invoice",
        "/prices",
    )

    _CHART_WORTHY_NUMERIC_KEYS = {
        "quantity",
        "value",
        "total",
        "amount",
        "price",
        "cost",
        "revenue",
        "count",
        "percentage",
        "rate",
        "margin",
        "qtd",
        "valor",
        "preco",
        "custo",
        "receita",
        "faturamento",
        "saldo",
        "volume",
        "peso",
        "weight",
    }

    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def present_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> dict | None:
        if not isinstance(root, dict):
            return None

        if not self.looks_like_kpi_response(root, path, entity=entity):
            return self._host._present_dict_fallback(root, path)

        kpi = self.build_kpi_chart(root, path)

        if kpi:
            linhas = self.kpi_cards_to_linhas(kpi)
            kpi_title = kpi.get("title") or self.kpi_title(path)

            return {
                "titulo": kpi_title,
                "linhas": linhas
                or [
                    self._host._presenter_text(
                        "generic",
                        "kpiSeeData",
                        title=kpi_title,
                    )
                ],
                "dados": root,
                "apresentacao": kpi,
            }

        fallback = self._host._present_dict_fallback(root, path)

        if fallback:
            return fallback

        kpi_title = self.kpi_title(path)

        return {
            "titulo": kpi_title,
            "linhas": [
                self._host._presenter_text(
                    "generic",
                    "kpiSeeData",
                    title=kpi_title,
                )
            ],
            "dados": root,
        }

    def kpi_cards_to_linhas(self, kpi: dict) -> list[str]:
        cards = kpi.get("cards")

        if not isinstance(cards, list):
            return []

        linhas: list[str] = []

        for card in cards:
            if not isinstance(card, dict):
                continue

            label = str(card.get("label") or self.kpi_title("")).strip()
            unit = str(card.get("unit") or "").strip()
            value = card.get("value")
            field_key = str(card.get("key") or "").strip()

            if value is None:
                continue

            formatted_value = (
                self._host._format_field_value(field_key, value)
                if field_key
                else self._host._format_field_value(label, value)
            )
            suffix = (
                ""
                if formatted_value.endswith("%") or formatted_value.startswith("R$")
                else f" {unit}".rstrip()
            )
            linhas.append(f"**{label}:** {formatted_value}{suffix}")

        return linhas

    def kpi_cards_from_presenter_section(self, section: str, data: dict) -> list[dict]:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        cards_cfg = ChatAssistantContentService.get_node(
            "presenter_content",
            section,
            "kpiCards",
        )

        if not isinstance(cards_cfg, list):
            return []

        cards: list[dict] = []

        for item in cards_cfg:
            if not isinstance(item, dict):
                continue

            field = str(item.get("field") or "").strip()
            label = str(item.get("label") or "").strip()

            if not field or not label:
                continue

            cards.append(
                {
                    "label": label,
                    "value": data.get(field),
                    "unit": str(item.get("unit") or ""),
                    "color": str(item.get("color") or "#0ea5e9"),
                }
            )

        return cards

    def build_dashboard_presentation(self, data: Any, *, path: str = "") -> dict | None:
        from app.domain.services.chat_dashboard_presentation_service import (
            ChatDashboardPresentationService,
        )

        root = self._host._unwrap_data(data)

        if not isinstance(root, dict):
            return None

        return ChatDashboardPresentationService.build(
            root,
            path=path,
            build_kpi=lambda summary, route: (
                (
                    {
                        "type": "kpi",
                        "title": self.kpi_title(route)
                        or self._host._presenter_text("charts", "dashboardKpiFallbackTitle"),
                        "cards": cards,
                    }
                    if (cards := self.build_generic_kpi_cards(summary, route))
                    else None
                )
                or self.build_kpi_chart(summary, route)
            ),
            build_lmp_table=self._host._build_lmp_table,
            build_items_table=lambda items, title: self._host._build_items_table(
                items,
                title=self._host._infer_items_title(items, path) or title,
                path=path,
            ),
            build_items_chart=lambda items, root_payload, route: self.build_chart_presentation(
                {**root_payload, "items": items},
                path=route,
                force=True,
            ),
        )

    def build_chart_presentation(
        self,
        data: Any,
        *,
        path: str = "",
        force: bool = False,
    ) -> dict | None:
        """Gera presentation tipo chart APENAS quando dados são naturalmente visuais."""
        if not force:
            lowered_path = (path or "").lower()

            if any(token in lowered_path for token in self._NO_CHART_PATHS):
                return None

        root = self._host._unwrap_data(data)

        if isinstance(root, dict) and "/analyser" in str(path or "").lower():
            normalized = self._host._normalize_analyser_root(root)
            analyser_chart = self._build_analyser_structure_type_chart(normalized)

            if analyser_chart:
                return analyser_chart

        if not isinstance(root, dict):
            if isinstance(root, list) and root and isinstance(root[0], dict):
                return self.try_chart_from_rows(root, force=force, path=path)

            return None

        stock_items = self._collect_stock_items(root)

        if stock_items:
            return self._build_stock_chart(stock_items)

        items = root.get("items")

        if isinstance(items, list) and items and isinstance(items[0], dict):
            if self._is_stock_data(items[0]):
                return self._build_stock_chart(items)

            chart = self.try_chart_from_rows(items, force=force, path=path)

            if chart:
                return chart

            if force:
                return self._build_categorical_count_chart(items, path=path)

            return None

        if self.looks_like_kpi_response(root, path):
            stock_value_kpi = self._host._build_stock_value_kpi(root, path)

            if stock_value_kpi:
                return stock_value_kpi

            return self.build_kpi_chart(root, path)

        return None

    def looks_like_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> bool:
        if entity == "product_billing":
            return False

        if entity and ChatApiDelpiResponseProfileService.is_kpi_entity(entity):
            return True

        lowered = str(path or "").lower()

        if "/sales/billing" in lowered:
            return False

        kpi_paths = (
            "cpv",
            "otd",
            "inventory-turnover",
            "stock-value",
            "giro",
            "turnover",
            "kpi",
            "indicator",
            "snapshot",
            "ebitda",
            "pmr",
            "pdi",
            "completion",
            "closing-rate",
            "new-clients",
            "new-business",
            "depreciation",
            "labor_cost",
            "production_cost",
            "effectiveness",
            "delivery",
        )

        if any(token in path for token in kpi_paths):
            return True

        kpi_keys = ("value", "percentage", "current", "previous", "target", "meta")
        has_series = any(k in root for k in ("periods", "series", "history"))
        kpi_count = sum(1 for k in kpi_keys if k in root)

        if kpi_count >= 2 or (kpi_count >= 1 and has_series):
            return True

        has_nested = any(isinstance(value, (dict, list)) for value in root.values())

        if not root.get("items") and not has_nested and len(root) <= 8:
            numeric_count = sum(1 for value in root.values() if isinstance(value, (int, float)))

            if numeric_count >= 2:
                return True

        return False

    def build_kpi_chart(self, root: dict, path: str) -> dict | None:
        periods = root.get("periods") or root.get("series") or root.get("history")

        if isinstance(periods, list) and len(periods) >= 2:
            return {
                "type": "chart",
                "title": self.kpi_title(path),
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
                        delta = f"+{self._host._format_num(diff)}{unit}"
                    elif diff < 0:
                        trend = "down"
                        delta = f"{self._host._format_num(diff)}{unit}"
                    else:
                        trend = "stable"
                except (ValueError, TypeError):
                    pass

            cards.append(
                {
                    "label": self._host._presenter_text("kpiCards", "current"),
                    "value": value,
                    "unit": unit,
                    "trend": trend,
                    "delta": delta,
                    "color": "#0ea5e9",
                }
            )

            if target is not None:
                cards.append(
                    {
                        "label": self._host._presenter_text("kpiCards", "target"),
                        "value": target,
                        "unit": unit,
                        "color": "#10b981",
                    }
                )

            if previous is not None:
                cards.append(
                    {
                        "label": self._host._presenter_text("kpiCards", "previous"),
                        "value": previous,
                        "unit": unit,
                        "color": "#94a3b8",
                    }
                )

            if cards:
                return {
                    "type": "kpi",
                    "title": self.kpi_title(path),
                    "cards": cards,
                }

        cards = self.build_generic_kpi_cards(root, path)

        if not cards:
            summary = root.get("summary")

            if isinstance(summary, dict):
                cards = self.build_generic_kpi_cards(summary, path)

        if cards:
            return {
                "type": "kpi",
                "title": self.kpi_title(path),
                "cards": cards,
            }

        return None

    def build_generic_kpi_cards(self, root: dict, path: str) -> list | None:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        cfg = ChatAssistantContentService.get_node("presenter_content", "genericKpi") or {}
        palette = cfg.get("palette") or [
            "#0ea5e9",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
        ]
        max_cards = int(cfg.get("maxCards") or 6)
        min_cards = int(cfg.get("minCards") or 2)
        percent_keys = [
            str(token).lower()
            for token in (cfg.get("percentUnitKeys") or ["pct", "percent", "rate"])
            if str(token).strip()
        ]
        cards = []
        idx = 0

        for key, val in root.items():
            if not isinstance(val, (int, float)):
                continue

            field_format = self._host._column_labels.resolve_field_format(
                str(key),
                schema_formats=self._host._active_schema_formats,
            )
            lowered_key = str(key).lower()
            cards.append(
                {
                    "key": str(key),
                    "label": self._host._humanize_key(key),
                    "value": val,
                    "dataType": field_format,
                    "unit": (
                        "%"
                        if field_format == "percent"
                        or any(token in lowered_key for token in percent_keys)
                        else ""
                    ),
                    "color": str(palette[idx % len(palette)]),
                }
            )
            idx += 1

            if idx >= max_cards:
                break

        return cards if len(cards) >= min_cards else None

    def kpi_title(self, path: str) -> str:
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

    def _build_categorical_count_chart(
        self,
        rows: list,
        *,
        path: str = "",
    ) -> dict | None:
        if not rows or not isinstance(rows[0], dict):
            return None

        preferred_keys = (
            "status",
            "listing_kind",
            "filial",
            "branch",
            "sale_number",
            "op",
            "produto",
            "product_code",
        )
        first = rows[0]
        label_key = next(
            (key for key in preferred_keys if key in first and isinstance(first.get(key), str)),
            None,
        )

        if not label_key:
            label_key = next(
                (key for key, value in first.items() if isinstance(value, str) and str(value).strip()),
                None,
            )

        if not label_key:
            return None

        counts: dict[str, int] = {}

        for row in rows[:24]:
            if not isinstance(row, dict):
                continue

            label = str(row.get(label_key) or "").strip() or "—"
            counts[label] = counts.get(label, 0) + 1

        if not counts:
            return None

        data = [{"name": name, "value": value} for name, value in counts.items()]
        chart_title = self._host._infer_items_title(rows, path) or self._host._presenter_text(
            "charts",
            "defaultVisualizationTitle",
        )

        return {
            "type": "chart",
            "title": chart_title,
            "chartType": "donut",
            "data": data,
            "config": {
                "xAxis": "name",
                "yAxis": ["value"],
                "legend": len(data) > 1,
            },
        }

    def try_chart_from_rows(
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

        heatmap = self.try_heatmap_from_rows(
            rows,
            force=force,
            user_message=user_message,
        )

        if heatmap:
            return heatmap

        if not force and len(rows) > 12:
            return None

        first = rows[0]
        numeric_keys = [key for key, value in first.items() if isinstance(value, (int, float))]
        string_keys = [key for key, value in first.items() if isinstance(value, str)]

        if not numeric_keys or not string_keys:
            return None

        if force:
            chart_numeric = numeric_keys[:3]
        else:
            chart_numeric = [
                key
                for key in numeric_keys
                if any(token in key.lower() for token in self._CHART_WORTHY_NUMERIC_KEYS)
            ]

            if not chart_numeric:
                return None

        label_key = string_keys[0]
        labels = [str(row.get(label_key, "")) for row in rows[:12]]

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
            config["gaugeTargetKey"] = (
                chart_numeric_slice[1] if len(chart_numeric_slice) > 1 else None
            )

        chart_title = self._host._infer_items_title(rows, path) or self._host._presenter_text(
            "charts",
            "defaultVisualizationTitle",
        )

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

    def try_heatmap_from_rows(
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
            "title": self._host._presenter_text("charts", "heatmapTitle"),
            "chartType": "heatmap",
            "data": capped_rows,
            "config": {
                "xAxis": x_axis,
                "yAxis": y_axis,
                "valueKey": value_key,
                "legend": False,
            },
        }

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
                    fallback = self._host._presenter_text("charts", "componentTypeFallback")
                    comp_type = (
                        str(component.get("type") or fallback).strip().upper()
                        or fallback.upper()
                    )
                    counts[comp_type] = counts.get(comp_type, 0) + 1

                continue

            fallback = self._host._presenter_text("charts", "componentTypeFallback")
            comp_type = (
                str(item.get("type") or fallback).strip().upper() or fallback.upper()
            )
            counts[comp_type] = counts.get(comp_type, 0) + 1

        if len(counts) < 2:
            return None

        sorted_counts = sorted(counts.items(), key=lambda pair: -pair[1])
        labels = [
            self._host._presenter_text(
                "charts",
                "typeLabelWithCount",
                type=key,
                count=str(value),
            )
            for key, value in sorted_counts
        ]
        values = [value for _, value in sorted_counts]
        label_key = "label"
        value_key = "value"
        chart_rows = [
            {label_key: label, value_key: value}
            for label, value in zip(labels, values)
        ]

        return {
            "type": "chart",
            "chartType": "donut",
            "title": self._host._presenter_text("charts", "structureTypeCompositionTitle"),
            "data": chart_rows,
            "config": {
                "xAxis": label_key,
                "yAxis": value_key,
                "legend": False,
            },
        }

    def _is_stock_data(self, row: dict) -> bool:
        return "warehouse" in row and (
            "available_quantity" in row or "current_quantity" in row
        )

    def _collect_stock_items(self, root: dict) -> list | None:
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

            label = self._host._presenter_text(
                "charts",
                "stockLocationLabel",
                branch=str(item.get("branch") or "?"),
                warehouse=str(item.get("warehouse") or "?"),
            )
            chart_data.append(
                {
                    "name": label,
                    self._host._humanize_key("current_quantity"): item.get("current_quantity") or 0,
                    self._host._humanize_key("available_quantity"): item.get("available_quantity") or 0,
                    self._host._humanize_key("committed_quantity"): item.get("committed_quantity") or 0,
                }
            )

        if not chart_data:
            return None

        quantity_series = [
            self._host._humanize_key("current_quantity"),
            self._host._humanize_key("available_quantity"),
            self._host._humanize_key("committed_quantity"),
        ]

        return {
            "type": "chart",
            "title": self._host._presenter_text("charts", "stockByLocationTitle"),
            "chartType": "horizontal_bar",
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": quantity_series,
                "colors": ["#0ea5e9", "#10b981", "#f59e0b"],
                "legend": True,
            },
        }

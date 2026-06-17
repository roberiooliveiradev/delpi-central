"""Quartet KPI/árvore/gráfico/dashboard declarativo — Playbook 12 R6."""

from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationCompositeVisualBuilder:
    @classmethod
    def spec(cls, spec_key: str) -> dict[str, Any]:
        resolved = ChatAssistantContentService.get_node(
            "presenter_content",
            "compositeVisualSpecs",
            spec_key,
        )

        return dict(resolved) if isinstance(resolved, dict) else {}

    @classmethod
    def build_kpi(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        spec: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        kpi_spec = spec.get("kpi")

        if not isinstance(kpi_spec, dict):
            return None

        default_source = str(kpi_spec.get("source") or "summary")
        require_sections = kpi_spec.get("requireAnySectionSummary")

        if isinstance(require_sections, list) and require_sections:
            if not any(
                isinstance(cls._section_summary(root, str(section)), dict)
                for section in require_sections
            ):
                return None

        require_any = kpi_spec.get("requireAny")

        if isinstance(require_any, list) and require_any:
            if not any(cls._has_resolved_data(root, str(token)) for token in require_any):
                return None

        code, _description = cls._product_context(host, root, path)
        namespace = str(spec.get("routeNamespace") or "").strip()
        title = cls._title(
            host,
            namespace,
            kpi_spec,
            code=code,
            default_generic="kpiTitleGeneric",
            default_with_code="kpiTitle",
        )
        cards: list[dict[str, Any]] = []
        default_dict = cls._resolve_dict(root, default_source)

        for card_spec in kpi_spec.get("cards") or []:
            if not isinstance(card_spec, dict):
                continue

            card_source = cls._resolve_dict(
                root,
                str(card_spec.get("source") or default_source),
            )
            card = cls._metric_card_from_field(host, namespace, card_spec, card_source)

            if card:
                cards.append(card)

        for card_spec in kpi_spec.get("sectionCards") or []:
            if not isinstance(card_spec, dict):
                continue

            section = str(card_spec.get("section") or "").strip()
            section_summary = cls._section_summary(root, section)

            if not isinstance(section_summary, dict):
                continue

            card = cls._metric_card_from_field(host, namespace, card_spec, section_summary)

            if card:
                cards.append(card)

        for card_spec in kpi_spec.get("computedCards") or []:
            if not isinstance(card_spec, dict):
                continue

            card = cls._metric_card_from_computed(host, namespace, root, card_spec)

            if card:
                cards.append(card)

        if not cards and not default_dict:
            return None

        min_cards = int(kpi_spec.get("minCards") or 2)

        return ChatPresentationKpiAssemblyService.build(title=title, cards=cards, min_cards=min_cards)

    @classmethod
    def build_chart(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        spec: dict[str, Any],
    ) -> dict[str, Any] | None:
        chart_spec = spec.get("chart")

        if not isinstance(chart_spec, dict):
            return None

        kind = str(chart_spec.get("kind") or "series").strip().lower()
        namespace = str(spec.get("routeNamespace") or "").strip()
        code, _description = cls._product_context(host, root, path)

        if kind == "composition":
            return cls._build_composition_chart(host, root, path, namespace, chart_spec, code=code)

        items = cls._filtered_items(host, root, path, chart_spec)
        min_items = int(chart_spec.get("minItems") or 1)

        if len(items) < min_items:
            return None

        limit = int(chart_spec.get("limit") or 20)
        series_specs = [
            item for item in (chart_spec.get("series") or []) if isinstance(item, dict)
        ]

        if not series_specs:
            return None

        y_labels: list[str] = []
        chart_data: list[dict[str, Any]] = []

        for index, item in enumerate(items[:limit]):
            row: dict[str, Any] = {
                "name": cls._chart_name(item, chart_spec, index=index + 1),
            }

            for index, series in enumerate(series_specs):
                field = str(series.get("field") or "").strip()
                label_key = str(series.get("labelKey") or "").strip()

                if label_key:
                    label = cls._route(host, namespace, label_key)
                else:
                    humanize_field = str(series.get("humanizeField") or field).strip()
                    label = host._humanize_key(humanize_field)

                if index >= len(y_labels):
                    y_labels.append(label)

                row[label] = float(item.get(field) or 0)

            chart_data.append(row)

        if not chart_data:
            return None

        colors = list(chart_spec.get("colors") or ["#0ea5e9", "#10b981"])

        return {
            "type": "chart",
            "title": cls._title(
                host,
                namespace,
                chart_spec,
                code=code,
                default_generic=str(chart_spec.get("titleGenericKey") or "chartTitleGeneric"),
                default_with_code=str(chart_spec.get("titleWithCodeKey") or "chartTitle"),
            ),
            "chartType": str(chart_spec.get("chartType") or "horizontal_bar"),
            "data": chart_data,
            "config": {
                "xAxis": "name",
                "yAxis": y_labels,
                "colors": colors,
                "legend": bool(chart_spec.get("legend", True)),
            },
        }

    @classmethod
    def build_tree(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        spec: dict[str, Any],
    ) -> dict[str, Any] | None:
        tree_spec = spec.get("tree")

        if not isinstance(tree_spec, dict):
            return None

        if isinstance(tree_spec.get("primary"), dict):
            for variant_key in ("primary", "fallback"):
                variant = tree_spec.get(variant_key)

                if not isinstance(variant, dict):
                    continue

                built = cls._build_tree_from_spec(host, root, path, spec, variant)

                if built:
                    return built

            return None

        return cls._build_tree_from_spec(host, root, path, spec, tree_spec)

    @classmethod
    def build_dashboard(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        spec: dict[str, Any],
        *,
        kpi: dict[str, Any] | None = None,
        tree: dict[str, Any] | None = None,
        chart: dict[str, Any] | None = None,
        table: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_presentation_dashboard_assembly_service import (
            ChatPresentationDashboardAssemblyService,
        )

        dashboard_spec = spec.get("dashboard")

        if not isinstance(dashboard_spec, dict):
            return None

        namespace = str(spec.get("routeNamespace") or "").strip()
        code, _description = cls._product_context(host, root, path)
        title = cls._title(
            host,
            namespace,
            dashboard_spec,
            code=code,
            default_generic="dashboardTitleGeneric",
            default_with_code="dashboardTitle",
        )
        panel_titles_raw = dashboard_spec.get("panelTitles") if isinstance(dashboard_spec.get("panelTitles"), dict) else {}
        panel_titles = {
            str(key): cls._route(host, namespace, str(value))
            for key, value in panel_titles_raw.items()
        }
        kind = str(dashboard_spec.get("kind") or "stacked").strip().lower()

        if kind == "rich_panels":
            view_order = list(dashboard_spec.get("viewOrder") or ["kpi", "tree", "chart"])

            if not isinstance(tree, dict):
                view_order = list(
                    dashboard_spec.get("viewOrderWithoutTree") or ["kpi", "chart", "table"]
                )

            panels = ChatPresentationDashboardAssemblyService.build_rich_panels(
                view_order=view_order,
                kpi=kpi,
                tree=tree,
                chart=chart,
                table=table,
                panel_titles={
                    key: str((slot or {}).get("title") or panel_titles.get(key) or "")
                    for key, slot in {
                        "kpi": kpi,
                        "tree": tree,
                        "chart": chart,
                        "table": table,
                    }.items()
                },
            )

            min_panels = int(dashboard_spec.get("minPanels") or 2)

            return ChatPresentationDashboardAssemblyService.build(
                title=title,
                panels=panels,
                min_panels=min_panels,
            )

        panels: list[dict[str, Any]] = []

        for panel_spec in dashboard_spec.get("panels") or []:
            if not isinstance(panel_spec, dict):
                continue

            source = str(panel_spec.get("source") or "").strip()
            presentation = {
                "kpi": kpi,
                "chart": chart,
                "table": table,
                "tree": tree,
            }.get(source)

            if not isinstance(presentation, dict):
                continue

            fallback_key = str(panel_spec.get("titleFallbackKey") or "").strip()
            panel_title = str(presentation.get("title") or "")

            if not panel_title and fallback_key:
                panel_title = cls._route(host, namespace, fallback_key)

            panel_kwargs: dict[str, Any] = {
                "panel_id": str(panel_spec.get("id") or source),
                "title": panel_title,
                "presentation": presentation,
            }

            if source == "chart":
                panel_kwargs["chart_presentation"] = presentation

            panels.append(ChatPresentationDashboardAssemblyService.panel(**panel_kwargs))

        min_panels = int(dashboard_spec.get("minPanels") or 2)

        return ChatPresentationDashboardAssemblyService.build(
            title=title,
            panels=panels,
            min_panels=min_panels,
        )

    @classmethod
    def _build_tree_from_spec(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        spec: dict[str, Any],
        tree_spec: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        namespace = str(spec.get("routeNamespace") or "").strip()
        code, description = cls._product_context(host, root, path)
        items = cls._resolve_tree_items(host, root, path, tree_spec)

        if tree_spec.get("wrapSingleRecord"):
            record_source = str(tree_spec.get("wrapSingleRecordSource") or tree_spec.get("source") or "").strip()
            record = cls._resolve_dict(root, record_source)
            group_field = str(tree_spec.get("wrapGroupField") or "supplier_group").strip()
            group_from = str(tree_spec.get("wrapGroupFromField") or "supplier_code").strip()

            if isinstance(record, dict) and record:
                group_value = str(record.get(group_from) or "—")
                items = [{**record, group_field: group_value}]
            else:
                items = []

        if not items:
            return None

        title = cls._title(
            host,
            namespace,
            tree_spec,
            code=code,
            default_generic="treeTitleGeneric",
            default_with_code="treeTitle",
        )
        root_label = (
            cls._route(host, namespace, str(tree_spec.get("rootLabelKey") or "treeRootLabel"), code=code)
            if code
            else title
        )
        kind = str(tree_spec.get("kind") or "multi_level").strip().lower()

        if tree_spec.get("promoteToFlatBomWhenNested"):
            from app.domain.services.chat_presentation_operational_table_service import (
                ChatPresentationOperationalTableService as OpsTable,
            )

            if OpsTable.has_nested_bom_items(items):
                kind = "flat_bom"

        if kind == "flat_bom":
            return ChatPresentationHierarchyTreeService.build_flat_bom_tree(
                title=title,
                root_id=code or str(tree_spec.get("rootIdFallback") or "structure"),
                root_label=root_label,
                root_subtitle=description,
                items=items,
            )

        leaf_spec = tree_spec.get("leaf") if isinstance(tree_spec.get("leaf"), dict) else {}
        group_keys = list(tree_spec.get("groupKeys") or [])
        leaf_builder = cls._tree_leaf_builder(host, namespace, leaf_spec)

        return ChatPresentationHierarchyTreeService.build_multi_level(
            title=title,
            root_id=code or str(tree_spec.get("rootIdFallback") or "playbook"),
            root_label=root_label,
            items=items,
            group_keys=group_keys,
            leaf_builder=leaf_builder,
        )

    @classmethod
    def _tree_leaf_builder(
        cls,
        host: ExternalActionResultPresenter,
        namespace: str,
        leaf_spec: dict[str, Any],
    ) -> Callable[[dict[str, Any]], dict[str, Any]]:
        from app.domain.services.chat_presentation_hierarchy_tree_service import (
            ChatPresentationHierarchyTreeService,
        )

        label_namespace = str(leaf_spec.get("labelNamespace") or namespace).strip()
        meta_fields = [
            str(field)
            for field in (leaf_spec.get("metaFields") or [])
            if str(field).strip()
        ]

        def _leaf(item: dict[str, Any]) -> dict[str, Any]:
            label_fields = leaf_spec.get("labelFields") if isinstance(leaf_spec.get("labelFields"), dict) else {}
            label_values: dict[str, str] = {}

            for key, source_field in label_fields.items():
                if isinstance(source_field, dict):
                    if source_field.get("formatSupplier"):
                        from app.domain.services.chat_presentation_supplier_display_service import (
                            ChatPresentationSupplierDisplayService,
                        )

                        label_values[str(key)] = ChatPresentationSupplierDisplayService.format_supplier_label(
                            supplier_code=ChatPresentationSupplierDisplayService.supplier_code(item),
                            supplier_name=ChatPresentationSupplierDisplayService.supplier_name(item),
                            supplier_store=ChatPresentationSupplierDisplayService.supplier_store(item),
                        )
                        continue

                    field_name = str(source_field.get("field") or "").strip()
                    raw_value = cls._field_value(item, field_name, source_field.get("alternateFields"))

                    if source_field.get("format"):
                        label_values[str(key)] = str(
                            host._format_field_value(field_name, raw_value)
                        )
                    else:
                        label_values[str(key)] = str(raw_value or "—")
                else:
                    label_values[str(key)] = str(item.get(str(source_field)) or "—")

            node_id = cls._leaf_node_id(item, leaf_spec)
            subtitle = str(item.get(str(leaf_spec.get("subtitleField") or "")) or "").strip()
            fallback_field = str(leaf_spec.get("subtitleFallbackField") or "").strip()

            if not subtitle and fallback_field:
                subtitle = str(item.get(fallback_field) or "").strip()

            meta = {
                field: item.get(field)
                for field in meta_fields
                if item.get(field) is not None
            }
            detail_meta = item.get("_detailMeta")

            if isinstance(detail_meta, dict):
                meta.update(detail_meta)

            if not subtitle and leaf_spec.get("subtitleFormat") == "supplier_store":
                from app.domain.services.chat_presentation_supplier_display_service import (
                    ChatPresentationSupplierDisplayService,
                )

                subtitle = ChatPresentationSupplierDisplayService.format_store_label(
                    ChatPresentationSupplierDisplayService.supplier_store(item)
                )

            kwargs: dict[str, Any] = {
                "node_id": node_id,
                "label": cls._route(
                    host,
                    label_namespace,
                    str(leaf_spec.get("labelKey") or ""),
                    **label_values,
                ),
                "subtitle": subtitle,
            }

            if meta:
                kwargs["meta"] = meta

            return ChatPresentationHierarchyTreeService._serialize_node(**kwargs)

        return _leaf

    @classmethod
    def _build_composition_chart(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        namespace: str,
        chart_spec: dict[str, Any],
        *,
        code: str,
    ) -> dict[str, Any] | None:
        source_key = str(chart_spec.get("source") or "last_purchase")
        record = cls._resolve_dict(root, source_key)
        base_field = str(chart_spec.get("baseField") or "unit_price").strip()
        rate_field = str(chart_spec.get("rateField") or "icms_rate").strip()

        if record.get(base_field) is None:
            return None

        price_value = float(record.get(base_field) or 0)
        rate_value = record.get(rate_field)
        icms_value = price_value * float(rate_value or 0) / 100 if rate_value is not None else 0
        net_label = cls._route(host, namespace, str(chart_spec.get("netLabelKey") or "chartNetPriceLabel"))
        icms_label = cls._route(host, namespace, str(chart_spec.get("icmsLabelKey") or "chartIcmsLabel"))
        composition_label = cls._route(
            host,
            namespace,
            str(chart_spec.get("compositionLabelKey") or "chartCompositionLabel"),
        )

        return {
            "type": "chart",
            "title": cls._title(
                host,
                namespace,
                chart_spec,
                code=code,
                default_generic=str(chart_spec.get("titleGenericKey") or "chartTitleGeneric"),
                default_with_code=str(chart_spec.get("titleWithCodeKey") or "chartTitle"),
            ),
            "chartType": str(chart_spec.get("chartType") or "horizontal_bar"),
            "data": [
                {
                    "name": composition_label,
                    net_label: price_value,
                    icms_label: icms_value,
                }
            ],
            "config": {
                "xAxis": "name",
                "yAxis": [net_label, icms_label],
                "colors": list(chart_spec.get("colors") or ["#10b981", "#6366f1"]),
                "legend": bool(chart_spec.get("legend", True)),
            },
        }

    @classmethod
    def _metric_card_from_field(
        cls,
        host: ExternalActionResultPresenter,
        namespace: str,
        card_spec: dict[str, Any],
        source: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        if not isinstance(source, dict):
            return None

        field = str(card_spec.get("field") or "").strip()
        raw_value = cls._field_value(source, field, card_spec.get("alternateFields"))

        if raw_value is None:
            return None

        if card_spec.get("skipZero") and raw_value in (None, "", 0, 0.0):
            return None

        cast = str(card_spec.get("cast") or "").strip().lower()

        if cast == "int":
            value: int | float = int(raw_value or 0)
        else:
            value = float(raw_value or 0)

        return ChatPresentationKpiAssemblyService.metric_card(
            label=cls._route(host, namespace, str(card_spec.get("labelKey") or "")),
            value=value,
            unit=str(card_spec.get("unit") or ""),
            color=str(card_spec.get("color") or "#0ea5e9"),
            key=str(card_spec.get("key") or field),
        )

    @classmethod
    def _metric_card_from_computed(
        cls,
        host: ExternalActionResultPresenter,
        namespace: str,
        root: dict[str, Any],
        card_spec: dict[str, Any],
    ) -> dict[str, Any] | None:
        from app.domain.services.chat_presentation_kpi_assembly_service import (
            ChatPresentationKpiAssemblyService,
        )

        computed_type = str(card_spec.get("type") or "").strip().lower()
        cast = str(card_spec.get("cast") or "").strip().lower()
        value: int | float | None = None
        label_key = str(card_spec.get("labelKey") or "")

        if computed_type == "sum":
            section = str(card_spec.get("section") or "").strip()
            summary = cls._section_summary(root, section) if section else cls._resolve_dict(
                root,
                str(card_spec.get("source") or "summary"),
            )
            fields = [str(field) for field in (card_spec.get("fields") or []) if str(field).strip()]

            if not isinstance(summary, dict) or not fields:
                return None

            total = sum(float(summary.get(field) or 0) for field in fields)
            value = int(total) if cast == "int" else total
        elif computed_type == "items_count":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            value = len(items)
        elif computed_type == "items_average":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            field = str(card_spec.get("field") or "").strip()
            numbers = [
                float(item.get(field) or 0)
                for item in items
                if isinstance(item, dict) and item.get(field) is not None
            ]

            if not numbers:
                return None

            value = sum(numbers) / len(numbers)
        elif computed_type == "first_item_field":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            field = str(card_spec.get("field") or "").strip()

            if not items or not field:
                return None

            first = items[0]

            if not isinstance(first, dict) or first.get(field) is None:
                return None

            raw_value = first.get(field)
            value = int(raw_value or 0) if cast == "int" else float(raw_value or 0)
        elif computed_type == "array_min":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            field = str(card_spec.get("field") or "").strip()
            numbers = [
                float(item.get(field) or 0)
                for item in items
                if isinstance(item, dict)
            ]

            if not numbers:
                return None

            value = min(numbers)
        elif computed_type == "array_max":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            field = str(card_spec.get("field") or "").strip()
            numbers = [
                float(item.get(field) or 0)
                for item in items
                if isinstance(item, dict)
            ]
            min_count = int(card_spec.get("minCount") or 1)

            if len(numbers) < min_count:
                return None

            value = max(numbers)
        elif computed_type == "array_max_positive":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            field = str(card_spec.get("field") or "").strip()
            numbers = [
                float(item.get(field) or 0)
                for item in items
                if isinstance(item, dict) and float(item.get(field) or 0) > 0
            ]

            if numbers:
                value = max(numbers)
                label_key = str(card_spec.get("labelKey") or "")
            else:
                fallback_field = str(card_spec.get("fallbackField") or "sale_price").strip()
                fallback_numbers = [
                    float(item.get(fallback_field) or 0)
                    for item in items
                    if isinstance(item, dict)
                ]
                min_count = int(card_spec.get("fallbackMinCount") or 2)

                if len(fallback_numbers) < min_count:
                    return None

                value = max(fallback_numbers)
                label_key = str(
                    card_spec.get("fallbackLabelKey") or card_spec.get("labelKey") or ""
                )
        elif computed_type == "array_max_skip_empty":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))
            field = str(card_spec.get("field") or "").strip()
            numbers = [
                float(item.get(field) or 0)
                for item in items
                if isinstance(item, dict) and item.get(field) not in (None, "", 0, 0.0)
            ]

            if not numbers:
                return None

            value = max(numbers)
        elif computed_type == "array_count":
            items = cls._resolve_list(root, str(card_spec.get("source") or "items"))

            if not items:
                return None

            value = len(items)
        else:
            return None

        if value is None:
            return None

        return ChatPresentationKpiAssemblyService.metric_card(
            label=cls._route(host, namespace, label_key),
            value=value,
            unit=str(card_spec.get("unit") or ""),
            color=str(card_spec.get("color") or "#0ea5e9"),
            key=str(card_spec.get("key") or computed_type),
        )

    @classmethod
    def _resolve_tree_items(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        tree_spec: dict[str, Any],
    ) -> list[dict[str, Any]]:
        combine_sections = tree_spec.get("combineSections")

        if isinstance(combine_sections, list) and combine_sections:
            code, _description = cls._product_context(host, root, path)
            combined: list[dict[str, Any]] = []

            for section_spec in combine_sections:
                if not isinstance(section_spec, dict):
                    continue

                section = str(section_spec.get("section") or "").strip()
                items = cls._resolve_list(root, f"section.{section}.items")
                preprocess = str(section_spec.get("preprocess") or "").strip()

                if preprocess == "enrich_history_items":
                    items = cls._enrich_history_items(host, items, product_code=code)

                record_kind = str(section_spec.get("recordKind") or "").strip()

                for item in items:
                    enriched = dict(item)

                    if record_kind:
                        enriched["record_kind"] = record_kind

                    combined.append(enriched)

            items = combined
        else:
            source_key = str(tree_spec.get("source") or "items")
            items = cls._resolve_list(root, source_key)

        inject_fields = tree_spec.get("injectFields")

        if isinstance(inject_fields, dict) and inject_fields:
            items = [{**item, **inject_fields} for item in items]

        preprocess = str(tree_spec.get("preprocess") or "").strip()

        if preprocess == "enrich_structure_rows":
            from app.domain.services.external_actions.presenters.product_operational_table_row_enrichment import (
                enrich_structure_rows,
            )

            items = enrich_structure_rows(items)
        elif preprocess == "enrich_history_items":
            code, _description = cls._product_context(host, root, path)
            items = cls._enrich_history_items(host, items, product_code=code)

        return [item for item in items if isinstance(item, dict)]

    @classmethod
    def _enrich_history_items(
        cls,
        host: ExternalActionResultPresenter,
        items: list[dict[str, Any]],
        *,
        product_code: str,
    ) -> list[dict[str, Any]]:
        from app.domain.services.chat_presentation_detail_action_service import (
            ChatPresentationDetailActionService,
        )
        from app.domain.services.chat_presentation_supplier_display_service import (
            ChatPresentationSupplierDisplayService,
        )

        enriched: list[dict[str, Any]] = []

        for raw in items:
            item = ChatPresentationSupplierDisplayService.enrich_item(raw)

            if product_code:
                item["product_code"] = product_code

            document = str(item.get("document_number") or item.get("purchase_order") or "").strip()
            source = str(item.get("source") or "").strip()

            if product_code and document and source:
                item["_detailMeta"] = ChatPresentationDetailActionService.purchase_record_detail_meta(
                    product_code=product_code,
                    document_number=document,
                    source=source,
                    supplier_code=ChatPresentationSupplierDisplayService.supplier_code(item),
                    supplier_store=ChatPresentationSupplierDisplayService.supplier_store(item),
                )

            enriched.append(item)

        return enriched

    @classmethod
    def _aggregate_mp_stock_rows(cls, stock_items: list[Any]) -> list[dict[str, Any]]:
        from app.domain.services.chat_presentation_operational_table_service import (
            ChatPresentationOperationalTableService as OpsTable,
        )

        grouped: dict[str, dict[str, Any]] = {}

        for item in stock_items:
            if not isinstance(item, dict):
                continue

            code = str(item.get("raw_material_code") or "").strip()

            if not code:
                continue

            bucket = grouped.setdefault(
                code,
                {
                    "raw_material_code": code,
                    "available_quantity_total": 0.0,
                },
            )
            bucket["available_quantity_total"] += OpsTable.parse_quantity(item.get("available_quantity"))

        rows: list[dict[str, Any]] = []

        for code in sorted(grouped):
            row = grouped[code]
            row["available_quantity_total"] = float(row.get("available_quantity_total") or 0)
            rows.append(row)

        return rows

    @classmethod
    def _product_context(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
    ) -> tuple[str, str]:
        product = root.get("product") if isinstance(root.get("product"), dict) else {}
        code = str(
            product.get("product_code")
            or product.get("code")
            or host._extract_product_code_from_path(path)
            or ""
        ).strip()
        description = str(product.get("description") or "").strip()

        return code, description

    @classmethod
    def _section_block(cls, root: dict[str, Any], key: str) -> dict[str, Any]:
        block = root.get(key)

        return dict(block) if isinstance(block, dict) else {}

    @classmethod
    def _section_summary(cls, root: dict[str, Any], section: str) -> dict[str, Any]:
        summary = cls._section_block(root, section).get("summary")

        from app.domain.services.chat_presentation_operational_metadata_field_service import (
            ChatPresentationOperationalMetadataFieldService,
        )

        return ChatPresentationOperationalMetadataFieldService.filter_summary(
            dict(summary) if isinstance(summary, dict) else None,
        )

    @classmethod
    def _resolve_dict(cls, root: dict[str, Any], source_key: str) -> dict[str, Any]:
        if source_key in ("root", ""):
            return root

        if source_key.startswith("section."):
            parts = source_key.split(".")

            if len(parts) >= 3 and parts[2] == "summary":
                return cls._section_summary(root, parts[1])

            if len(parts) >= 2:
                block = cls._section_block(root, parts[1])

                return block

        if source_key == "summary":
            summary = root.get("summary")

            from app.domain.services.chat_presentation_operational_metadata_field_service import (
                ChatPresentationOperationalMetadataFieldService,
            )

            return ChatPresentationOperationalMetadataFieldService.filter_summary(
                dict(summary) if isinstance(summary, dict) else None,
            )

        block = root.get(source_key)

        return dict(block) if isinstance(block, dict) else {}

    @classmethod
    def _resolve_list(cls, root: dict[str, Any], source_key: str) -> list[dict[str, Any]]:
        if source_key.startswith("section."):
            parts = source_key.split(".")

            if len(parts) >= 3 and parts[2] == "items":
                items = cls._section_block(root, parts[1]).get("items")

                return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []

        if source_key == "items":
            items = root.get("items")

            return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []

        if source_key == "prices":
            prices = root.get("prices")

            return [item for item in prices if isinstance(item, dict)] if isinstance(prices, list) else []

        block = root.get(source_key)

        return [item for item in block if isinstance(item, dict)] if isinstance(block, list) else []

    @classmethod
    def _has_resolved_data(cls, root: dict[str, Any], token: str) -> bool:
        if token.startswith("section."):
            parts = token.split(".")

            if len(parts) >= 3 and parts[2] == "items":
                return bool(cls._resolve_list(root, token))

            if len(parts) >= 3 and parts[2] == "summary":
                return bool(cls._resolve_dict(root, token))

        if token in ("items", "prices"):
            return bool(cls._resolve_list(root, token))

        return bool(cls._resolve_dict(root, token))

    @classmethod
    def _field_value(
        cls,
        source: dict[str, Any],
        field: str,
        alternate_fields: Any,
    ) -> Any:
        if field and source.get(field) is not None:
            return source.get(field)

        for alternate in alternate_fields or []:
            alt = str(alternate).strip()

            if alt and source.get(alt) is not None:
                return source.get(alt)

        return None

    @classmethod
    def _filtered_items(
        cls,
        host: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
        chart_spec: dict[str, Any],
    ) -> list[dict[str, Any]]:
        source_key = str(chart_spec.get("source") or "items")
        items = cls._resolve_list(root, source_key)

        if chart_spec.get("preprocess") == "aggregate_mp_stock":
            items = cls._aggregate_mp_stock_rows(items)

        item_filter = chart_spec.get("itemFilter")

        if not isinstance(item_filter, dict):
            return items

        field = str(item_filter.get("field") or "").strip()

        if not field:
            return items

        if item_filter.get("truthy") is True:
            truthy = ChatPresentationVocabularyService.exclusive_raw_material_truthy()

            return [
                item
                for item in items
                if str(item.get(field) or "").strip().upper() in truthy
            ]

        expected = str(item_filter.get("equals") or "").strip()

        if expected:
            return [item for item in items if str(item.get(field) or "").strip() == expected]

        return items

    @classmethod
    def _chart_name(cls, item: dict[str, Any], chart_spec: dict[str, Any], *, index: int = 0) -> str:
        name_fields = chart_spec.get("nameFields")

        if isinstance(name_fields, list):
            for field in name_fields:
                value = str(item.get(str(field)) or "").strip()

                if value:
                    return value

            if chart_spec.get("nameIndexFallback") and index:
                return f"#{index}"

        name_field = str(chart_spec.get("nameField") or "").strip()
        fallback_field = str(chart_spec.get("nameFallbackField") or "").strip()

        if name_field:
            prefix = str(chart_spec.get("namePrefix") or "")
            value = str(item.get(name_field) or (item.get(fallback_field) if fallback_field else None) or "—")

            return f"{prefix}{value}" if prefix else value

        if chart_spec.get("nameFromIndex"):
            return str(item.get("name") or "—")

        return str(item.get("product_code") or "—")

    @classmethod
    def _leaf_node_id(cls, item: dict[str, Any], leaf_spec: dict[str, Any]) -> str:
        fixed_id = str(leaf_spec.get("fixedId") or "").strip()

        if fixed_id:
            return fixed_id

        prefix = str(leaf_spec.get("idPrefix") or "")
        id_fields = leaf_spec.get("idFields") if isinstance(leaf_spec.get("idFields"), list) else []
        parts = [str(item.get(str(field)) or "—") for field in id_fields]
        joined = ":".join(parts)

        if prefix.endswith(":"):
            return f"{prefix}{joined}"

        if prefix:
            return f"{prefix}:{joined}" if joined else prefix

        return joined or "leaf"

    @classmethod
    def _title(
        cls,
        host: ExternalActionResultPresenter,
        namespace: str,
        spec: dict[str, Any],
        *,
        code: str,
        default_generic: str,
        default_with_code: str,
    ) -> str:
        if code:
            key = str(spec.get("titleWithCodeKey") or default_with_code)

            return cls._route(host, namespace, key, code=code)

        key = str(spec.get("titleGenericKey") or default_generic)

        return cls._route(host, namespace, key)

    @classmethod
    def _route(
        cls,
        host: ExternalActionResultPresenter,
        namespace: str,
        key: str,
        **values: str,
    ) -> str:
        if not namespace or not key:
            return ""

        return host._route_presentation(namespace, key, **values)

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

from app.domain.services.external_actions.presenters.legacy_route_presenter import (
    ExternalActionLegacyRoutePresenter,
)
from app.domain.services.external_actions.presenters.playbook_report_presenter import (
    ExternalActionPlaybookReportPresenter,
)

from app.domain.services.external_actions.presenters.entity_route_presenter import (
    ExternalActionEntityRoutePresenter,
)

from app.domain.services.external_actions.presenters.presentation_builder_presenter import (
    ExternalActionPresentationBuilderPresenter,
)
from app.domain.services.external_actions.presenters.text_presentation_presenter import (
    ExternalActionTextPresentationPresenter,
)
from app.domain.services.external_actions.presenters.route_line_presenter import (
    ExternalActionRouteLinePresenter,
)
from app.domain.services.external_actions.presenters.operational_response_presenter import (
    ExternalActionOperationalResponsePresenter,
)
from app.domain.services.external_actions.presenters.product_overview_presenter import (
    ExternalActionProductOverviewPresenter,
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
        self._playbook_report_presenter: ExternalActionPlaybookReportPresenter | None = None
        self._legacy_route_presenter: ExternalActionLegacyRoutePresenter | None = None
        self._entity_route_presenter: ExternalActionEntityRoutePresenter | None = None
        self._presentation_builder_presenter: ExternalActionPresentationBuilderPresenter | None = None
        self._text_presentation_presenter: ExternalActionTextPresentationPresenter | None = None
        self._route_line_presenter: ExternalActionRouteLinePresenter | None = None
        self._operational_response_presenter: ExternalActionOperationalResponsePresenter | None = None
        self._product_overview_presenter: ExternalActionProductOverviewPresenter | None = None

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


    def _playbook_report(self) -> ExternalActionPlaybookReportPresenter:
        if self._playbook_report_presenter is None:
            self._playbook_report_presenter = ExternalActionPlaybookReportPresenter(self)

        return self._playbook_report_presenter

    def _legacy_route(self) -> ExternalActionLegacyRoutePresenter:
        if self._legacy_route_presenter is None:
            self._legacy_route_presenter = ExternalActionLegacyRoutePresenter(self)

        return self._legacy_route_presenter


    def _entity_route(self) -> ExternalActionEntityRoutePresenter:
        if self._entity_route_presenter is None:
            self._entity_route_presenter = ExternalActionEntityRoutePresenter(self)

        return self._entity_route_presenter


    def _presentation_builder(self) -> ExternalActionPresentationBuilderPresenter:
        if self._presentation_builder_presenter is None:
            self._presentation_builder_presenter = ExternalActionPresentationBuilderPresenter(self)

        return self._presentation_builder_presenter

    def _text(self) -> ExternalActionTextPresentationPresenter:
        if self._text_presentation_presenter is None:
            self._text_presentation_presenter = ExternalActionTextPresentationPresenter(self)

        return self._text_presentation_presenter

    def _route_lines(self) -> ExternalActionRouteLinePresenter:
        if self._route_line_presenter is None:
            self._route_line_presenter = ExternalActionRouteLinePresenter(self)

        return self._route_line_presenter

    def _operational_response(self) -> ExternalActionOperationalResponsePresenter:
        if self._operational_response_presenter is None:
            self._operational_response_presenter = ExternalActionOperationalResponsePresenter(self)

        return self._operational_response_presenter

    def _product_overview(self) -> ExternalActionProductOverviewPresenter:
        if self._product_overview_presenter is None:
            self._product_overview_presenter = ExternalActionProductOverviewPresenter(self)

        return self._product_overview_presenter

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
            routed = self._entity_route()._present_entity_first(data, path=path, profile=profile)

            if routed is not None:
                return routed

            return self._legacy_route()._present_legacy(data, path=path)
        finally:
            self._active_schema_labels = previous_labels
            self._active_schema_formats = previous_formats



    def _present_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> dict | None:
        return self._kpi_chart().present_kpi_response(root, path, entity=entity)


    def _fallback_title(self, path: str) -> str | None:
        return self._operational_response()._fallback_title(path)

    def _present_dict_fallback(self, root: dict, path: str) -> dict | None:
        return self._operational_response()._present_dict_fallback(root, path)

    def _extract_product_code_from_path(self, path: str) -> str:
        return self._operational_response()._extract_product_code_from_path(path)

    def _present_empty_operational_result(self, *, path: str, root) -> dict | None:
        return self._operational_response()._present_empty_operational_result(path=path, root=root)

    @staticmethod
    def _is_empty_operational_payload(root) -> bool:
        return ExternalActionOperationalResponsePresenter._is_empty_operational_payload(root)

    def _format_protheus_date(self, value) -> str | None:
        return self._operational_response()._format_protheus_date(value)

    def _format_currency(self, value) -> str:
        return self._operational_response()._format_currency(value)

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


    def _is_product_operational_path(self, path: str) -> bool:
        return self._operational_response()._is_product_operational_path(path)

    def _detect_api_error(self, data, *, path: str = "") -> dict | None:
        return self._operational_response()._detect_api_error(data, path=path)

    def _unwrap_data(self, data):
        return self._operational_response()._unwrap_data(data)

    def _normalize_api_section(self, block, *, _depth: int = 0):
        return self._operational_response()._normalize_api_section(block, _depth=_depth)

    def _overview_missing(self) -> str:
        return self._product_overview()._overview_missing()

    def _build_product_overview_narrative_lines(self, product: dict, root: dict) -> list[str]:
        return self._product_overview()._build_product_overview_narrative_lines(product, root)

    def _format_revision_date(self, token: str) -> str:
        return self._product_overview()._format_revision_date(token)

    def _present_product(self, root: dict, product: dict) -> dict:
        return self._product_overview()._present_product(root, product)


























    def _extract_product_detail_list(self, root: dict) -> list | None:
        return self._product_overview()._extract_product_detail_list(root)

    def _format_detail_preview_line(self, item: dict) -> str:
        return self._product_overview()._format_detail_preview_line(item)

    def _present_product_with_details(
        self, product_summary: dict, detail_list: list, root: dict
    ) -> dict:
        return self._product_overview()._present_product_with_details(
            product_summary,
            detail_list,
            root,
        )
















    def _present_product_structure(self, root: dict, path: str) -> dict | None:
        return self._product_list()._present_product_structure(root, path)

    def _present_product_factory_status(self, root: dict, path: str) -> dict:
        return self._product_list()._present_product_factory_status(root, path)





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
        return self._route_lines()._alias_dict(payload)

    def _label_collection(self, key: str) -> str:
        return self._route_lines()._label_collection(key)

    def _total(self, value):
        return self._route_lines()._total(value)

    def _collection_is_empty(self, value) -> bool:
        return self._route_lines()._collection_is_empty(value)


    def _build_parents_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._text()._build_parents_text_presentation(root, path)

    def _build_structure_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._text()._build_structure_text_presentation(root, path)

    def build_text_presentation(self, data, *, path: str = "") -> dict | None:
        return self._text().build_text_presentation(data, path=path)

    def build_tree_presentation(self, data, *, path: str = "") -> dict | None:
        return self._text().build_tree_presentation(data, path=path)

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
            entity_first = self._presentation_builder()._build_presentation_by_entity(
                data,
                path=path,
                profile=profile,
            )

            if entity_first is not None:
                return entity_first

            return self._presentation_builder()._build_presentation(data, path=path)
        finally:
            self._active_schema_labels = None
            self._active_schema_formats = None












    def _infer_column_type(self, key: str) -> str | None:
        return self._column_labels.infer_column_type(key)

    def _enrich_column(self, key: str, label: str) -> dict:
        return self._column_labels.enrich_column(key, label)

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
        return self._route_lines()._format_structure_component_line(
            code,
            description,
            item_type,
            quantity,
        )

    def _format_measurable_test_specs(self, test: dict) -> str | None:
        return self._route_lines()._format_measurable_test_specs(test)

    def _format_inspection_characteristic_line(self, item: dict) -> str | None:
        return self._route_lines()._format_inspection_characteristic_line(item)

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
        return self._route_lines()._format_product_search_line(
            code=code,
            description=description,
            item_type=item_type,
            unit=unit,
            quantity=quantity,
            level=level,
            is_hierarchy=is_hierarchy,
        )

    def _product_detail_scope(self, root: dict) -> str:
        return self._route_lines()._product_detail_scope(root)

    def _product_detail_title(self, code: object, root: dict) -> str:
        return self._route_lines()._product_detail_title(code, root)







    # --- Presentation builder (delegação Fase 3A lote 11) ---

    def _build_presentation_by_entity(self, data, *, path: str, profile: ApiDelpiResponseProfile) -> dict | None:
        return self._presentation_builder()._build_presentation_by_entity(data, path=path, profile=profile)

    def _build_presentation_entity_extensions(self, root: dict, *, path: str, profile: ApiDelpiResponseProfile) -> dict | None:
        return self._presentation_builder()._build_presentation_entity_extensions(root, path=path, profile=profile)

    def _build_factory_status_table(self, root: dict, path: str) -> dict:
        return self._presentation_builder()._build_factory_status_table(root, path)

    def _build_presentation(self, data, *, path: str = "") -> dict | None:
        return self._presentation_builder()._build_presentation(data, path=path)

    def _build_product_table(self, product: dict, root: dict) -> dict:
        return self._presentation_builder()._build_product_table(product, root)

    def _build_product_detail_table(self, product: dict, detail_list: list, root: dict) -> dict:
        return self._presentation_builder()._build_product_detail_table(product, detail_list, root)

    def _build_sale_orders_table(self, items: list, root: dict) -> dict:
        return self._presentation_builder()._build_sale_orders_table(items, root)

    def _flatten_nested_field(self, items: list) -> list:
        return self._presentation_builder()._flatten_nested_field(items)

    def _build_product_search_table(self, items: list, root: dict, *, title: str | None = None) -> dict:
        return self._presentation_builder()._build_product_search_table(items, root, title=title)

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
        return self._column_labels.format_num(value)

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

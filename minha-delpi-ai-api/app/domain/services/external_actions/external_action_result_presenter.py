from app.domain.services.chat_presentation_column_label_context import (
    ExternalActionColumnLabelContext,
)
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
from app.domain.services.external_actions.presenters.product_composite_analysis_presenter import (
    ExternalActionProductCompositeAnalysisPresenter,
)
from app.domain.services.external_actions.presenters.product_production_status_presenter import (
    ExternalActionProductProductionStatusPresenter,
)
from app.domain.services.external_actions.presenters.product_shipping_status_presenter import (
    ExternalActionProductShippingStatusPresenter,
)
from app.domain.services.external_actions.presenters.product_structure_exclusivity_presenter import (
    ExternalActionProductStructureExclusivityPresenter,
)
from app.domain.services.external_actions.presenters.product_pricing_presenter import (
    ExternalActionProductPricingPresenter,
)
from app.domain.services.external_actions.presenters.product_purchase_history_presenter import (
    ExternalActionProductPurchaseHistoryPresenter,
)
from app.domain.services.external_actions.presenters.product_purchases_presenter import (
    ExternalActionProductPurchasesPresenter,
)
from app.domain.services.external_actions.presenters.product_raw_material_price_presenter import (
    ExternalActionProductRawMaterialPricePresenter,
)
from app.domain.services.external_actions.presenters.product_list_presenter import (
    ExternalActionProductListPresenter,
)
from app.domain.services.external_actions.presenters.product_stock_presenter import (
    ExternalActionProductStockPresenter,
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
from app.domain.services.external_actions.presenters.presenter_content_presenter import (
    ExternalActionPresenterContentPresenter,
)
from app.domain.services.external_actions.presenters.presentation_shape_presenter import (
    ExternalActionPresentationShapePresenter,
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
        self._product_composite_presenter: ExternalActionProductCompositeAnalysisPresenter | None = None
        self._product_production_status_presenter: ExternalActionProductProductionStatusPresenter | None = None
        self._product_shipping_status_presenter: ExternalActionProductShippingStatusPresenter | None = None
        self._product_structure_exclusivity_presenter: ExternalActionProductStructureExclusivityPresenter | None = None
        self._product_pricing_presenter: ExternalActionProductPricingPresenter | None = None
        self._product_purchase_history_presenter: ExternalActionProductPurchaseHistoryPresenter | None = None
        self._product_purchases_presenter: ExternalActionProductPurchasesPresenter | None = None
        self._product_raw_material_price_presenter: ExternalActionProductRawMaterialPricePresenter | None = None
        self._product_list_presenter: ExternalActionProductListPresenter | None = None
        self._product_stock_presenter: ExternalActionProductStockPresenter | None = None
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
        self._presenter_content_presenter: ExternalActionPresenterContentPresenter | None = None
        self._presentation_shape_presenter: ExternalActionPresentationShapePresenter | None = None

    @property
    def column_label_context(self) -> ExternalActionColumnLabelContext:
        return ExternalActionColumnLabelContext(
            column_labels=self._column_labels,
            schema_labels=self._active_schema_labels,
            schema_formats=self._active_schema_formats,
        )

    def _kpi_chart(self) -> ExternalActionKpiChartPresenter:
        if self._kpi_chart_presenter is None:
            self._kpi_chart_presenter = ExternalActionKpiChartPresenter(self)

        return self._kpi_chart_presenter

    def _analyser(self) -> ExternalActionProductAnalyserPresenter:
        if self._product_analyser_presenter is None:
            self._product_analyser_presenter = ExternalActionProductAnalyserPresenter(self)

        return self._product_analyser_presenter

    def _composite_analysis(self) -> ExternalActionProductCompositeAnalysisPresenter:
        if self._product_composite_presenter is None:
            self._product_composite_presenter = ExternalActionProductCompositeAnalysisPresenter(self)

        return self._product_composite_presenter

    def _production_status(self) -> ExternalActionProductProductionStatusPresenter:
        if self._product_production_status_presenter is None:
            self._product_production_status_presenter = ExternalActionProductProductionStatusPresenter(
                self
            )

        return self._product_production_status_presenter

    def _shipping_status(self) -> ExternalActionProductShippingStatusPresenter:
        if self._product_shipping_status_presenter is None:
            self._product_shipping_status_presenter = ExternalActionProductShippingStatusPresenter(
                self
            )

        return self._product_shipping_status_presenter

    def _structure_exclusivity(self) -> ExternalActionProductStructureExclusivityPresenter:
        if self._product_structure_exclusivity_presenter is None:
            self._product_structure_exclusivity_presenter = (
                ExternalActionProductStructureExclusivityPresenter(self)
            )

        return self._product_structure_exclusivity_presenter

    def _product_pricing(self) -> ExternalActionProductPricingPresenter:
        if self._product_pricing_presenter is None:
            self._product_pricing_presenter = ExternalActionProductPricingPresenter(self)

        return self._product_pricing_presenter

    def _purchase_history(self) -> ExternalActionProductPurchaseHistoryPresenter:
        if self._product_purchase_history_presenter is None:
            self._product_purchase_history_presenter = ExternalActionProductPurchaseHistoryPresenter(
                self,
            )

        return self._product_purchase_history_presenter

    def _purchases(self) -> ExternalActionProductPurchasesPresenter:
        if self._product_purchases_presenter is None:
            self._product_purchases_presenter = ExternalActionProductPurchasesPresenter(self)

        return self._product_purchases_presenter

    def _raw_material_price(self) -> ExternalActionProductRawMaterialPricePresenter:
        if self._product_raw_material_price_presenter is None:
            self._product_raw_material_price_presenter = (
                ExternalActionProductRawMaterialPricePresenter(self)
            )

        return self._product_raw_material_price_presenter

    def _product_list(self) -> ExternalActionProductListPresenter:
        if self._product_list_presenter is None:
            self._product_list_presenter = ExternalActionProductListPresenter(self)

        return self._product_list_presenter

    def _stock(self) -> ExternalActionProductStockPresenter:
        if self._product_stock_presenter is None:
            self._product_stock_presenter = ExternalActionProductStockPresenter(self)

        return self._product_stock_presenter

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

    def _presenter_content(self) -> ExternalActionPresenterContentPresenter:
        if self._presenter_content_presenter is None:
            self._presenter_content_presenter = ExternalActionPresenterContentPresenter(self)

        return self._presenter_content_presenter

    def _presentation_shape(self) -> ExternalActionPresentationShapePresenter:
        if self._presentation_shape_presenter is None:
            self._presentation_shape_presenter = ExternalActionPresentationShapePresenter(self)

        return self._presentation_shape_presenter

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
        return self._presenter_content()._path_fragment_title(fragment)


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
        return self._composite_analysis()._present_factory_status(root, path)

    def _present_product_production_status(self, root: dict, path: str) -> dict:
        return self._production_status()._present_production_status(root, path)

    def _present_product_shipping_status(self, root: dict, path: str) -> dict:
        return self._shipping_status()._present_shipping_status(root, path)

    def _present_product_structure_exclusivity(self, root: dict, path: str) -> dict:
        return self._structure_exclusivity()._present_structure_exclusivity(root, path)

    def _present_product_raw_material_price_intelligence(self, root: dict, path: str) -> dict:
        return self._raw_material_price()._present_raw_material_price_intelligence(root, path)

    def _present_product_cost_impact_simulation(self, root: dict, path: str) -> dict:
        return self._raw_material_price()._present_cost_impact_simulation(root, path)

    def _present_product_pricing(self, root: dict, path: str) -> dict:
        return self._product_pricing()._present_product_pricing(root, path)

    def _present_product_last_purchase(self, root: dict, path: str) -> dict:
        return self._raw_material_price()._present_last_purchase(root, path)

    def _present_product_purchase_price_history(self, root: dict, path: str) -> dict:
        return self._purchase_history()._present_purchase_history(root, path)

    def _present_product_purchase_budget_history(self, root: dict, path: str) -> dict:
        return self._purchase_history()._present_purchase_history(root, path)

    def _present_product_purchases(self, root: dict, path: str) -> dict:
        return self._purchases()._present_product_purchases(root, path)

    def _present_playbook_report(self, root: dict, path: str, *, entity: str) -> dict | None:
        return self._playbook_report()._present_playbook_report(root, path, entity=entity)

    def _build_playbook_report_table(self, root: dict, path: str, *, entity: str) -> dict | None:
        return self._playbook_report()._build_playbook_report_table(root, path, entity=entity)





    def _looks_like_inspection_item(self, item: dict) -> bool:
        return self._presentation_shape()._looks_like_inspection_item(item)




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

    def prepare_presentation_data(self, data, *, path: str = ""):
        return self._entity_route().prepare_presentation_root(data, path=path)

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

            legacy = self._presentation_builder()._build_presentation(data, path=path)

            if legacy is not None:
                return legacy

            from app.domain.services.chat_schema_driven_presentation_service import (
                ChatSchemaDrivenPresentationService,
            )

            return ChatSchemaDrivenPresentationService.build_primary(
                self,
                data,
                path=path,
                entity=profile.entity,
                response_schema=response_schema,
            )
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

    def _columns_for_items(
        self,
        items: list,
        *,
        profile_name: str | None = None,
        path: str = "",
    ) -> list[dict]:
        dict_items = [item for item in items if isinstance(item, dict)]

        if not dict_items:
            return []

        return self._column_labels.resolve_columns_for_items(
            dict_items,
            path=path,
            profile_name=profile_name,
            schema_labels=self._active_schema_labels,
        )

    def _markdown_column_pairs_for_items(
        self,
        items: list,
        *,
        profile_name: str | None = None,
        path: str = "",
    ) -> list[tuple[str, str]]:
        return [
            (column["key"], column["label"])
            for column in self._columns_for_items(
                items,
                profile_name=profile_name,
                path=path,
            )
        ]

    def _build_profile_items_table(
        self,
        items: list,
        *,
        profile_name: str | None = None,
        title: str,
        role: str,
        path: str = "",
    ) -> dict | None:
        from app.domain.services.chat_presentation_operational_table_service import (
            ChatPresentationOperationalTableService as OpsTable,
        )

        return OpsTable.build_items_table(
            self.column_label_context,
            [item for item in items if isinstance(item, dict)],
            title=title,
            role=role,
            path=path,
            profile_name=profile_name,
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
        tables = self.build_factory_status_table_presentations(root, path)

        if tables:
            return tables[0]

        return self._presentation_builder()._build_factory_status_table(root, path)

    def build_factory_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._composite_analysis().build_factory_status_table_presentations(root, path)

    def build_factory_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._composite_analysis().build_factory_kpi_presentation(root, path)

    def build_factory_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._composite_analysis().build_factory_tree_presentation(root, path)

    def build_factory_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._composite_analysis().build_factory_chart_presentation(root, path)

    def build_factory_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        tree: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._composite_analysis().build_factory_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table,
        )

    def build_production_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._production_status().build_production_status_table_presentations(root, path)

    def build_shipping_status_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._shipping_status().build_shipping_status_table_presentations(root, path)

    def build_structure_exclusivity_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._structure_exclusivity().build_structure_exclusivity_table_presentations(
            root,
            path,
        )

    def build_production_status_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._production_status().build_production_status_kpi_presentation(root, path)

    def build_production_status_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._production_status().build_production_status_chart_presentation(root, path)

    def build_production_status_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._production_status().build_production_status_tree_presentation(root, path)

    def build_production_status_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._production_status().build_production_status_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_shipping_status_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._shipping_status().build_shipping_status_kpi_presentation(root, path)

    def build_shipping_status_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._shipping_status().build_shipping_status_chart_presentation(root, path)

    def build_shipping_status_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._shipping_status().build_shipping_status_tree_presentation(root, path)

    def build_shipping_status_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._shipping_status().build_shipping_status_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_structure_exclusivity_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._structure_exclusivity().build_structure_exclusivity_kpi_presentation(root, path)

    def build_structure_exclusivity_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._structure_exclusivity().build_structure_exclusivity_chart_presentation(root, path)

    def build_structure_exclusivity_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._structure_exclusivity().build_structure_exclusivity_tree_presentation(root, path)

    def build_structure_exclusivity_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        tree: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._structure_exclusivity().build_structure_exclusivity_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table,
        )

    def build_raw_material_price_intelligence_table_presentations(
        self,
        root: dict,
        path: str,
    ) -> list[dict]:
        return self._raw_material_price().build_raw_material_price_intelligence_table_presentations(
            root,
            path,
        )

    def build_raw_material_price_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_raw_material_price_kpi_presentation(root, path)

    def build_raw_material_price_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_raw_material_price_chart_presentation(root, path)

    def build_raw_material_price_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_raw_material_price_tree_presentation(root, path)

    def build_raw_material_price_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        tree: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._raw_material_price().build_raw_material_price_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            tree=tree,
            chart=chart,
            table=table,
        )

    def build_cost_impact_simulation_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._raw_material_price().build_cost_impact_simulation_table_presentations(
            root,
            path,
        )

    def build_cost_impact_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_cost_impact_kpi_presentation(root, path)

    def build_cost_impact_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_cost_impact_chart_presentation(root, path)

    def build_cost_impact_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_cost_impact_tree_presentation(root, path)

    def build_cost_impact_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._raw_material_price().build_cost_impact_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_product_pricing_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._product_pricing().build_product_pricing_table_presentations(root, path)

    def build_product_pricing_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._product_pricing().build_product_pricing_kpi_presentation(root, path)

    def build_product_pricing_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._product_pricing().build_product_pricing_chart_presentation(root, path)

    def build_product_pricing_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._product_pricing().build_product_pricing_tree_presentation(root, path)

    def build_product_pricing_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._product_pricing().build_product_pricing_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_last_purchase_table_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_last_purchase_table_presentation(root, path)

    def build_last_purchase_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._raw_material_price().build_last_purchase_table_presentations(root, path)

    def build_last_purchase_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_last_purchase_kpi_presentation(root, path)

    def build_last_purchase_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_last_purchase_chart_presentation(root, path)

    def build_last_purchase_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price().build_last_purchase_tree_presentation(root, path)

    def build_last_purchase_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._raw_material_price().build_last_purchase_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_purchase_history_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._purchase_history().build_purchase_history_table_presentations(root, path)

    def build_purchase_history_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchase_history().build_purchase_history_kpi_presentation(root, path)

    def build_purchase_history_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchase_history().build_purchase_history_chart_presentation(root, path)

    def build_purchase_history_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchase_history().build_purchase_history_tree_presentation(root, path)

    def build_purchase_history_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._purchase_history().build_purchase_history_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_purchases_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._purchases().build_purchases_table_presentations(root, path)

    def build_purchases_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchases().build_purchases_kpi_presentation(root, path)

    def build_purchases_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchases().build_purchases_chart_presentation(root, path)

    def build_purchases_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchases().build_purchases_tree_presentation(root, path)

    def build_purchases_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._purchases().build_purchases_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def build_stock_table_presentations(self, root: dict, path: str) -> list[dict]:
        return self._stock().build_stock_table_presentations(root, path)

    def build_stock_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._stock().build_stock_kpi_presentation(root, path)

    def build_stock_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._stock().build_stock_tree_presentation(root, path)

    def build_stock_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._stock().build_stock_chart_presentation(root, path)

    def build_stock_dashboard_presentation(
        self,
        root: dict,
        path: str,
        *,
        kpi: dict | None = None,
        chart: dict | None = None,
        table: dict | None = None,
    ) -> dict | None:
        return self._stock().build_stock_dashboard_presentation(
            root,
            path,
            kpi=kpi,
            chart=chart,
            table=table,
        )

    def _build_stock_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._stock()._build_stock_text_presentation(root, path)

    def _build_factory_status_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._composite_analysis()._build_factory_status_text_presentation(root, path)

    def _build_production_status_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._production_status()._build_production_status_text_presentation(root, path)

    def _build_shipping_status_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._shipping_status()._build_shipping_status_text_presentation(root, path)

    def _build_structure_exclusivity_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._structure_exclusivity()._build_structure_exclusivity_text_presentation(
            root,
            path,
        )

    def _build_raw_material_price_intelligence_text_presentation(
        self,
        root: dict,
        path: str,
    ) -> dict | None:
        return self._raw_material_price()._build_intelligence_text_presentation(root, path)

    def _build_cost_impact_simulation_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price()._build_cost_impact_text_presentation(root, path)

    def _build_product_pricing_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._product_pricing()._build_pricing_text_presentation(root, path)

    def _build_last_purchase_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._raw_material_price()._build_last_purchase_text_presentation(root, path)

    def _build_purchase_history_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchase_history()._build_purchase_history_text_presentation(root, path)

    def _build_purchases_text_presentation(self, root: dict, path: str) -> dict | None:
        return self._purchases()._build_purchases_text_presentation(root, path)

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
        root: dict | None = None,
    ) -> dict:
        return self._stock()._present_product_stock(
            items,
            path=path,
            title=title,
            root=root,
        )

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

    def build_analyser_tree_presentation(self, root: dict, path: str) -> dict | None:
        return self._analyser().build_analyser_tree_presentation(root, path)

    def build_analyser_chart_presentation(self, root: dict, path: str) -> dict | None:
        return self._analyser().build_analyser_chart_presentation(root, path)

    def build_analyser_kpi_presentation(self, root: dict, path: str) -> dict | None:
        return self._analyser().build_analyser_kpi_presentation(root, path)

    def build_analyser_dashboard_presentation(self, root: dict, path: str, **kwargs: object) -> dict | None:
        return self._analyser().build_analyser_dashboard_presentation(root, path, **kwargs)

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

    def apply_schema_driven_auxiliaries(
        self,
        data,
        *,
        path: str = "",
        text_presentation: dict | None = None,
        tree_presentation: dict | None = None,
        table_presentation: dict | None = None,
        chart_presentation: dict | None = None,
        kpi_presentation: dict | None = None,
    ) -> dict[str, dict | None]:
        from app.domain.services.chat_schema_driven_presentation_service import (
            ChatSchemaDrivenPresentationService,
        )

        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)

        if not ChatSchemaDrivenPresentationService.should_apply(
            path=path,
            entity=profile.entity,
        ):
            return {
                "text_presentation": text_presentation,
                "tree_presentation": tree_presentation,
                "table_presentation": table_presentation,
                "chart_presentation": chart_presentation,
                "kpi_presentation": kpi_presentation,
            }

        bundle = ChatSchemaDrivenPresentationService.build_bundle(
            self,
            data,
            path=path,
            entity=profile.entity,
        )

        return {
            "text_presentation": self._merge_schema_text_presentation(
                text_presentation,
                bundle.text,
            ),
            "tree_presentation": tree_presentation or bundle.tree,
            "table_presentation": table_presentation or bundle.table,
            "chart_presentation": chart_presentation or bundle.chart,
            "kpi_presentation": kpi_presentation or bundle.kpi,
        }

    @staticmethod
    def _merge_schema_text_presentation(
        existing: dict | None,
        schema_text: dict | None,
    ) -> dict | None:
        if not isinstance(schema_text, dict):
            return existing

        if not isinstance(existing, dict):
            return schema_text

        existing_md = str(existing.get("markdown") or "").strip()
        schema_md = str(schema_text.get("markdown") or "").strip()

        if not schema_md:
            return existing

        if "<!-- section:scope -->" in schema_md and (
            not existing_md or existing_md.count("\n") < 2
        ):
            return schema_text

        if len(schema_md) > len(existing_md) + 24:
            return schema_text

        return existing

    def build_chart_presentation(self, data, *, path: str = "", force: bool = False) -> dict | None:
        return self._kpi_chart().build_chart_presentation(data, path=path, force=force)

    def _is_tabular_data(self, row: dict) -> bool:
        return self._presentation_shape()._is_tabular_data(row)

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
        return self._presenter_content()._analyser_markdown(key, **values)

    def _route_narrative(self, route: str, key: str, **values: str) -> str:
        return self._presenter_content()._route_narrative(route, key, **values)

    def _route_presentation(self, route: str, key: str, **values: str) -> str:
        return self._presenter_content()._route_presentation(route, key, **values)

    def _presenter_text(
        self,
        section: str,
        text_key: str,
        *extra_path: str,
        **values: str,
    ) -> str:
        return self._presenter_content()._presenter_text(
            section,
            text_key,
            *extra_path,
            **values,
        )

    def _presenter_root_format(self, key: str, **values: str) -> str:
        return self._presenter_content()._presenter_root_format(key, **values)

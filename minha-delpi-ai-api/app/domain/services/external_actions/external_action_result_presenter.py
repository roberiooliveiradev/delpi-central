"""Humanização e apresentação schema-first de resultados de actions externas."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_column_label_context import (
    ExternalActionColumnLabelContext,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.domain.services.external_actions.presenters.kpi_chart_presenter import (
    ExternalActionKpiChartPresenter,
)
from app.domain.services.external_actions.presenters.operational_response_presenter import (
    ExternalActionOperationalResponsePresenter,
)
from app.domain.services.external_actions.presenters.presentation_table_host_service import (
    build_items_table,
    escape_markdown_table_cell,
    infer_items_title,
    markdown_table,
)
from app.domain.services.external_actions.presenters.presenter_content_presenter import (
    ExternalActionPresenterContentPresenter,
)
from app.domain.services.external_actions.presenters.sql_presenter import (
    ExternalActionSqlPresenter,
)
from app.domain.services.external_actions.external_action_result_orchestration.external_action_result_build_service import (
    ExternalActionResultBuildService,
)
from app.domain.services.external_actions.external_action_result_orchestration.external_action_result_present_service import (
    ExternalActionResultPresentService,
)
from app.domain.services.external_actions.external_action_result_orchestration.external_action_result_schema_auxiliary_service import (
    ExternalActionResultSchemaAuxiliaryService,
)


class ExternalActionResultPresenter:
    def __init__(
        self,
        column_label_service: ExternalActionColumnLabelService | None = None,
    ):
        self._column_labels = column_label_service or ExternalActionColumnLabelService()
        self._active_schema_labels: dict[str, str] | None = None
        self._active_schema_formats: dict[str, str] | None = None
        self._active_presentation_path: str = ""
        self._kpi_chart_presenter: ExternalActionKpiChartPresenter | None = None
        self._operational_response_presenter: ExternalActionOperationalResponsePresenter | None = None
        self._presenter_content_presenter: ExternalActionPresenterContentPresenter | None = None
        self._sql_presenter: ExternalActionSqlPresenter | None = None

    @property
    def column_label_context(self) -> ExternalActionColumnLabelContext:
        return ExternalActionColumnLabelContext(
            column_labels=self._column_labels,
            schema_labels=self._active_schema_labels,
            schema_formats=self._active_schema_formats,
            path=self._active_presentation_path,
        )

    def _effective_presentation_path(self, path: str = "") -> str:
        return path or self._active_presentation_path or ""

    def _kpi_chart(self) -> ExternalActionKpiChartPresenter:
        if self._kpi_chart_presenter is None:
            self._kpi_chart_presenter = ExternalActionKpiChartPresenter(self)

        return self._kpi_chart_presenter

    def _operational_response(self) -> ExternalActionOperationalResponsePresenter:
        if self._operational_response_presenter is None:
            self._operational_response_presenter = ExternalActionOperationalResponsePresenter(self)

        return self._operational_response_presenter

    def _presenter_content(self) -> ExternalActionPresenterContentPresenter:
        if self._presenter_content_presenter is None:
            self._presenter_content_presenter = ExternalActionPresenterContentPresenter(self)

        return self._presenter_content_presenter

    def _sql(self) -> ExternalActionSqlPresenter:
        if self._sql_presenter is None:
            self._sql_presenter = ExternalActionSqlPresenter(self)

        return self._sql_presenter

    def present(self, data, *, path: str = "") -> dict:
        return ExternalActionResultPresentService.present(self, data, path=path)

    def prepare_presentation_data(self, data, *, path: str = ""):
        return data

    def build_presentation(
        self,
        data,
        *,
        path: str = "",
        response_schema: dict | None = None,
    ) -> dict | None:
        return ExternalActionResultBuildService.build_presentation(
            self,
            data,
            path=path,
            response_schema=response_schema,
        )

    def build_text_presentation(self, data, *, path: str = "") -> dict | None:
        return None

    def build_tree_presentation(self, data, *, path: str = "") -> dict | None:
        return None

    def build_dashboard_presentation(self, data, *, path: str = "") -> dict | None:
        return None

    def build_chart_presentation(self, data, *, path: str = "", force: bool = False) -> dict | None:
        return self._kpi_chart().build_chart_presentation(data, path=path, force=force)

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
        return ExternalActionResultSchemaAuxiliaryService.apply_schema_driven_auxiliaries(
            self,
            data,
            path=path,
            text_presentation=text_presentation,
            tree_presentation=tree_presentation,
            table_presentation=table_presentation,
            chart_presentation=chart_presentation,
            kpi_presentation=kpi_presentation,
        )

    @staticmethod
    def _merge_schema_text_presentation(
        existing: dict | None,
        schema_text: dict | None,
    ) -> dict | None:
        return ExternalActionResultSchemaAuxiliaryService.merge_schema_text_presentation(
            existing,
            schema_text,
        )

    def _fallback_title(self, path: str) -> str | None:
        return self._operational_response()._fallback_title(path)

    def _present_dict_fallback(self, root: dict, path: str) -> dict | None:
        return self._operational_response()._present_dict_fallback(root, path)

    def _present_empty_operational_result(self, *, path: str, root) -> dict | None:
        return self._operational_response()._present_empty_operational_result(path=path, root=root)

    @staticmethod
    def _is_empty_operational_payload(root) -> bool:
        return ExternalActionOperationalResponsePresenter._is_empty_operational_payload(root)

    def _detect_api_error(self, data, *, path: str = "") -> dict | None:
        return self._operational_response()._detect_api_error(data, path=path)

    def _unwrap_data(self, data):
        return self._operational_response()._unwrap_data(data)

    def _normalize_api_section(self, block, *, _depth: int = 0):
        return self._operational_response()._normalize_api_section(block, _depth=_depth)

    def _extract_product_code_from_path(self, path: str) -> str:
        return self._operational_response()._extract_product_code_from_path(path)

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

    def _infer_items_title(self, items: list, path: str) -> str | None:
        return infer_items_title(items, path)

    def _build_items_table(
        self,
        items: list,
        title: str | None = None,
        *,
        path: str = "",
        profile_name: str | None = None,
        entity: str | None = None,
        role: str = "generic",
    ) -> dict | None:
        return build_items_table(
            self,
            items,
            title,
            path=path,
            profile_name=profile_name,
            entity=entity,
            role=role,
        )

    def _humanize_key(self, key: str) -> str:
        return self._column_labels.label_for(
            key,
            schema_labels=self._active_schema_labels,
            path=self._effective_presentation_path(),
        )

    def _enrich_column(self, key: str, label: str) -> dict:
        return self._column_labels.enrich_column(key, label)

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

    def _escape_markdown_table_cell(self, value) -> str:
        return escape_markdown_table_cell(value)

    def _markdown_table(self, columns: list[tuple[str, str]], rows: list[dict]) -> list[str]:
        return markdown_table(columns, rows)

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

    def _kpi_title(self, path: str) -> str:
        return self._kpi_chart().kpi_title(path)

    def _kpi_cards_to_linhas(self, kpi: dict) -> list[str]:
        return self._kpi_chart().kpi_cards_to_linhas(kpi)

    def _format_num(self, value) -> str:
        return self._column_labels.format_num(value)

    def _analyser_markdown(self, key: str, **values: str) -> str:
        return self._presenter_content()._analyser_markdown(key, **values)

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

    def _route_presentation(self, route: str, key: str, **values: str) -> str:
        return self._presenter_content()._route_presentation(route, key, **values)

    def _present_kpi_response(
        self,
        root: dict,
        path: str,
        *,
        entity: str | None = None,
    ) -> dict | None:
        return self._kpi_chart().present_kpi_response(root, path, entity=entity)

    def _present_sql_resultsets(self, root: dict, path: str) -> dict | None:
        return self._sql()._present_sql_resultsets(root, path)

    def _present_sql_rows(self, rows: list) -> dict | None:
        return self._sql()._present_sql_rows(rows)

    def _sql_result_title(self, root: dict, path: str) -> str:
        return self._sql()._sql_result_title(root, path)

    def _sql_empty_message(self, root: dict, path: str) -> str:
        return self._sql()._sql_empty_message(root, path)

    def _looks_like_inventory_below_minimum_sql_context(self, root: dict, path: str) -> bool:
        return self._sql()._looks_like_inventory_below_minimum_sql_context(root, path)

    def _looks_like_production_sql_context(self, root: dict, path: str) -> bool:
        return self._sql()._looks_like_production_sql_context(root, path)

    def _looks_like_inventory_below_minimum_row(self, row: dict) -> bool:
        return self._sql()._looks_like_inventory_below_minimum_row(row)

    def _looks_like_production_schedule_row(self, row: dict) -> bool:
        return self._sql()._looks_like_production_schedule_row(row)

    def _format_production_schedule_row(self, row: dict) -> str:
        return self._sql()._format_production_schedule_row(row)

    def _present_sql_dict_rows(
        self,
        rows: list[dict],
        *,
        title: str | None = None,
        record_total: int | None = None,
    ) -> dict:
        return self._sql()._present_sql_dict_rows(rows, title=title, record_total=record_total)

    @staticmethod
    def _sql_resultset_record_total(resultsets: list) -> int | None:
        return ExternalActionSqlPresenter._sql_resultset_record_total(resultsets)

    def _collect_sql_resultset_rows(self, resultsets: list) -> list[dict]:
        return self._sql()._collect_sql_resultset_rows(resultsets)

    def _is_tabular_data(self, row: dict) -> bool:
        return isinstance(row, dict) and len(row) >= 2

    def _is_stock_data(self, row: dict) -> bool:
        return self._kpi_chart()._is_stock_data(row)

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

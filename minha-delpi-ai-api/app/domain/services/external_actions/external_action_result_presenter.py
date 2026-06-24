"""Humanização e apresentação schema-first de resultados de actions externas."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)
from app.domain.services.chat_presentation_column_label_context import (
    ExternalActionColumnLabelContext,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
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
        previous_labels = self._active_schema_labels
        previous_formats = self._active_schema_formats
        previous_path = self._active_presentation_path
        self._active_presentation_path = str(path or "").strip()
        self._active_schema_labels = self._column_labels.merge_meta_field_labels({}, data)
        self._active_schema_formats = self._column_labels.merge_meta_field_formats({}, data)

        try:
            error = self._detect_api_error(data, path=path)

            if error:
                return error

            root = self._unwrap_data(data)
            profile = ChatOperationalResponseProfileService.resolve(data, path=path)

            empty_operational = self._present_empty_operational_result(path=path, root=root)

            if empty_operational:
                return empty_operational

            if isinstance(root, dict) and self._looks_like_kpi_response(
                root,
                path,
                entity=profile.entity,
            ):
                kpi_result = self._kpi_chart().present_kpi_response(
                    root,
                    path,
                    entity=profile.entity,
                )

                if kpi_result:
                    return kpi_result

            if isinstance(root, dict):
                sql_result = self._sql()._present_sql_resultsets(root, path)

                if sql_result:
                    return sql_result

                rows = root.get("rows") if isinstance(root.get("rows"), list) else None

                if rows is None:
                    rows = self._sql()._coerce_sql_row_list(root)

                if isinstance(rows, list) and rows:
                    sql_result = self._sql()._present_sql_rows(rows)

                    if sql_result:
                        if isinstance(sql_result, dict):
                            sql_result.setdefault("dados", root)
                            sql_result.setdefault("sqlRows", rows)

                        return sql_result

            if isinstance(root, list) and root:
                sql_result = self._sql()._present_sql_rows(root)

                if sql_result:
                    return sql_result

            from app.domain.services.chat_schema_driven_presentation_service import (
                ChatSchemaDrivenPresentationService,
            )

            bundle = ChatSchemaDrivenPresentationService.build_bundle(
                self,
                data,
                path=path,
                entity=profile.entity,
            )

            for visual in (
                bundle.table,
                bundle.kpi,
                bundle.chart,
                bundle.tree,
                bundle.text,
            ):
                if isinstance(visual, dict):
                    return self._operational_response().present_visual(
                        visual,
                        data=data,
                        path=path,
                    )

            visual = self.build_presentation(data, path=path)

            if visual:
                return self._operational_response().present_visual(
                    visual,
                    data=data,
                    path=path,
                )

            if isinstance(root, dict):
                fallback = self._present_dict_fallback(root, path)

                if fallback:
                    return fallback

            return {
                "titulo": self._presenter_text("generic", "defaultQueryTitle"),
                "linhas": [self._presenter_text("generic", "queryResultTitle")],
                "dados": root,
            }
        finally:
            self._active_schema_labels = previous_labels
            self._active_schema_formats = previous_formats
            self._active_presentation_path = previous_path

    def prepare_presentation_data(self, data, *, path: str = ""):
        return data

    def build_presentation(
        self,
        data,
        *,
        path: str = "",
        response_schema: dict | None = None,
    ) -> dict | None:
        schema_labels = self._column_labels.resolve_schema_labels(response_schema)
        previous_path = self._active_presentation_path
        self._active_presentation_path = str(path or "").strip()
        self._active_schema_labels = self._column_labels.merge_meta_field_labels(
            schema_labels,
            data,
        )
        self._active_schema_formats = self._column_labels.merge_meta_field_formats(
            {},
            data,
        )

        try:
            profile = ChatOperationalResponseProfileService.resolve(data, path=path)
            root = self._unwrap_data(data)

            from app.domain.services.external_actions.external_action_sql_capability_service import (
                ExternalActionSqlCapabilityService,
            )

            if isinstance(root, dict) and isinstance(root.get("resultsets"), list):
                if ExternalActionSqlCapabilityService.is_sql_result_payload(
                    root
                ) or ExternalActionSqlCapabilityService.is_sql_execution_context(path=path):
                    rows = self._collect_sql_resultset_rows(root.get("resultsets"))
                    title = self._sql_result_title(root, path)

                    if not rows:
                        empty_table = self._sql()._build_sql_resultset_empty_table(
                            root,
                            title=title,
                            path=path,
                        )

                        if empty_table:
                            return empty_table

                    if rows:
                        return self._build_items_table(rows, title=title, path=path)

            if isinstance(root, dict) and ExternalActionSqlCapabilityService.is_sql_execution_context(
                path=path,
            ):
                rows = root.get("rows") if isinstance(root.get("rows"), list) else None

                if rows is None:
                    rows = self._sql()._coerce_sql_row_list(root)

                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    title = self._sql()._sql_result_title(root, path)

                    return self._build_items_table(rows, title=title, path=path)

            from app.domain.services.chat_schema_driven_presentation_service import (
                ChatSchemaDrivenPresentationService,
            )

            return ChatSchemaDrivenPresentationService.finish_schema_first_primary(
                self,
                data,
                path=path,
                entity=profile.entity,
                response_schema=response_schema,
            )
        finally:
            self._active_schema_labels = None
            self._active_schema_formats = None
            self._active_presentation_path = previous_path

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
        from app.domain.services.chat_schema_driven_presentation_service import (
            ChatSchemaDrivenPresentationService,
        )

        profile = ChatOperationalResponseProfileService.resolve(data, path=path)

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

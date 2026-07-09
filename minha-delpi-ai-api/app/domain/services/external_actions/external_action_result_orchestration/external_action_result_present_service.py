"""present — ExternalActionResultPresenter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionResultPresentService:
    @staticmethod
    def _is_low_signal_presentation(presented: dict, root: Any) -> bool:
        linhas = [str(line).strip() for line in (presented.get("linhas") or []) if str(line).strip()]
        joined = " ".join(linhas).lower()

        if not joined:
            return True

        generic_markers = (
            "resultado da consulta",
            "formato original",
            "dados retornados pela api",
            "```json",
        )

        if not any(marker in joined for marker in generic_markers):
            return False

        if isinstance(root, dict):
            product = root.get("product")

            if isinstance(product, dict):
                code = str(product.get("code") or "").strip()

                if code and code not in joined:
                    return True

        return True

    @staticmethod
    def present(host: ExternalActionResultPresenter, data, *, path: str = "") -> dict:
        previous_labels = host._active_schema_labels
        previous_formats = host._active_schema_formats
        previous_path = host._active_presentation_path
        host._active_presentation_path = str(path or "").strip()
        host._active_schema_labels = host._column_labels.merge_meta_field_labels({}, data)
        host._active_schema_formats = host._column_labels.merge_meta_field_formats({}, data)

        try:
            error = host._detect_api_error(data, path=path)

            if error:
                return error

            root = host._unwrap_data(data)
            profile = ChatOperationalResponseProfileService.resolve(data, path=path)

            empty_operational = host._present_empty_operational_result(path=path, root=root)

            if empty_operational:
                return empty_operational

            if isinstance(root, dict) and host._looks_like_kpi_response(
                root,
                path,
                entity=profile.entity,
            ):
                kpi_result = host._kpi_chart().present_kpi_response(
                    root,
                    path,
                    entity=profile.entity,
                )

                if kpi_result:
                    return kpi_result

            if isinstance(root, dict):
                from app.domain.services.external_actions.external_action_sql_capability_service import (
                    ExternalActionSqlCapabilityService,
                )

                sql_result = host._sql()._present_sql_resultsets(root, path)

                if sql_result:
                    return sql_result

                rows = root.get("rows") if isinstance(root.get("rows"), list) else None

                if rows is None and (
                    ExternalActionSqlCapabilityService.is_sql_execution_context(path=path)
                    or ExternalActionSqlCapabilityService.is_sql_result_payload(root)
                ):
                    rows = host._sql()._coerce_sql_row_list(root)

                if isinstance(rows, list) and rows:
                    sql_result = host._sql()._present_sql_rows(rows)

                    if sql_result:
                        if isinstance(sql_result, dict):
                            sql_result.setdefault("dados", root)
                            sql_result.setdefault("sqlRows", rows)

                        return sql_result

            if isinstance(root, list) and root:
                sql_result = host._sql()._present_sql_rows(root)

                if sql_result:
                    return sql_result

            from app.domain.services.chat_schema_driven_presentation_service import (
                ChatSchemaDrivenPresentationService,
            )

            bundle = ChatSchemaDrivenPresentationService.build_bundle(
                host,
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
                    presented = host._operational_response().present_visual(
                        visual,
                        data=data,
                        path=path,
                    )

                    if presented and not ExternalActionResultPresentService._is_low_signal_presentation(
                        presented,
                        root,
                    ):
                        return presented

            visual = host.build_presentation(data, path=path)

            if visual:
                presented = host._operational_response().present_visual(
                    visual,
                    data=data,
                    path=path,
                )

                if presented and not ExternalActionResultPresentService._is_low_signal_presentation(
                    presented,
                    root,
                ):
                    return presented

            if isinstance(root, dict):
                fallback = host._present_dict_fallback(root, path)

                if fallback:
                    return fallback

            return {
                "titulo": host._presenter_text("generic", "defaultQueryTitle"),
                "linhas": [host._presenter_text("generic", "queryResultTitle")],
                "dados": root,
            }
        finally:
            host._active_schema_labels = previous_labels
            host._active_schema_formats = previous_formats
            host._active_presentation_path = previous_path

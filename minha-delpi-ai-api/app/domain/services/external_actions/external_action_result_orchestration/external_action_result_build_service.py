"""build_presentation — ExternalActionResultPresenter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionResultBuildService:
    @staticmethod
    def build_presentation(
        host: ExternalActionResultPresenter,
        data,
        *,
        path: str = "",
        response_schema: dict | None = None,
    ) -> dict | None:
        schema_labels = host._column_labels.resolve_schema_labels(response_schema)
        previous_path = host._active_presentation_path
        host._active_presentation_path = str(path or "").strip()
        host._active_schema_labels = host._column_labels.merge_meta_field_labels(
            schema_labels,
            data,
        )
        host._active_schema_formats = host._column_labels.merge_meta_field_formats(
            {},
            data,
        )

        try:
            profile = ChatOperationalResponseProfileService.resolve(data, path=path)
            root = host._unwrap_data(data)

            from app.domain.services.external_actions.external_action_sql_capability_service import (
                ExternalActionSqlCapabilityService,
            )

            if isinstance(root, dict) and isinstance(root.get("resultsets"), list):
                if ExternalActionSqlCapabilityService.is_sql_result_payload(
                    root
                ) or ExternalActionSqlCapabilityService.is_sql_execution_context(path=path):
                    rows = host._collect_sql_resultset_rows(root.get("resultsets"))
                    title = host._sql_result_title(root, path)

                    if not rows:
                        empty_table = host._sql()._build_sql_resultset_empty_table(
                            root,
                            title=title,
                            path=path,
                        )

                        if empty_table:
                            return empty_table

                    if rows:
                        return host._build_items_table(rows, title=title, path=path)

            if isinstance(root, dict) and ExternalActionSqlCapabilityService.is_sql_execution_context(
                path=path,
            ):
                rows = root.get("rows") if isinstance(root.get("rows"), list) else None

                if rows is None:
                    rows = host._sql()._coerce_sql_row_list(root)

                if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                    title = host._sql()._sql_result_title(root, path)

                    return host._build_items_table(rows, title=title, path=path)

            from app.domain.services.chat_schema_driven_presentation_service import (
                ChatSchemaDrivenPresentationService,
            )

            return ChatSchemaDrivenPresentationService.finish_schema_first_primary(
                host,
                data,
                path=path,
                entity=profile.entity,
                response_schema=response_schema,
            )
        finally:
            host._active_schema_labels = None
            host._active_schema_formats = None
            host._active_presentation_path = previous_path

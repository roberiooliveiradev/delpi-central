"""Schema-driven auxiliaries — ExternalActionResultPresenter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_operational_response_profile_service import (
    ChatOperationalResponseProfileService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionResultSchemaAuxiliaryService:
    @staticmethod
    def apply_schema_driven_auxiliaries(
        host: ExternalActionResultPresenter,
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
            host,
            data,
            path=path,
            entity=profile.entity,
        )

        return {
            "text_presentation": ExternalActionResultSchemaAuxiliaryService.merge_schema_text_presentation(
                text_presentation,
                bundle.text,
            ),
            "tree_presentation": tree_presentation or bundle.tree,
            "table_presentation": table_presentation or bundle.table,
            "chart_presentation": chart_presentation or bundle.chart,
            "kpi_presentation": kpi_presentation or bundle.kpi,
        }

    @staticmethod
    def merge_schema_text_presentation(
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

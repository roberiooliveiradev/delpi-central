"""Narrativa e formatação compartilhada — rotas operacionais de produto (estilo analyser)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionOperationalRouteNarrativeService:
    _STARTED_YES = frozenset({"SIM", "SIM_SC2", "S", "YES", "TRUE", "1"})
    _STARTED_NO = frozenset({"NAO", "NÃO", "N", "NO", "FALSE", "0"})

    _PREVIEW_MAX = 3

    @classmethod
    def format_production_flag(cls, value: object) -> str:
        if value is None or value == "":
            return "—"

        if isinstance(value, bool):
            return "Sim" if value else "Não"

        text = str(value).strip()
        upper = text.upper()

        if upper in cls._STARTED_YES:
            return "Sim"

        if upper in cls._STARTED_NO:
            return "Não"

        return text

    @classmethod
    def format_quantity(
        cls,
        host: ExternalActionResultPresenter,
        value: object,
        *,
        field_key: str = "reported_quantity",
    ) -> str:
        if value is None or value == "":
            return "0"

        return host._format_field_value(field_key, value)

    @classmethod
    def compact_product_line(
        cls,
        host: ExternalActionResultPresenter,
        *,
        code: str,
        description: str,
    ) -> str:
        if code and description:
            return host._presenter_text(
                "analyserCompact",
                "productSummary",
                code=code,
                description=description,
            )

        if code:
            return host._presenter_text("analyserCompact", "productSummary", code=code, description="—")

        return ""

    @classmethod
    def append_item_preview(
        cls,
        host: ExternalActionResultPresenter,
        linhas: list[str],
        items: list,
        *,
        compact_for_rich_ui: bool,
        preview_line: str,
        empty_line: str,
        table_hint: str,
        format_item_line,
    ) -> None:
        if not items:
            linhas.append(empty_line)
            return

        linhas.append(preview_line)

        if compact_for_rich_ui:
            if table_hint:
                linhas.append(table_hint)
            return

        preview_items = [item for item in items[: cls._PREVIEW_MAX] if isinstance(item, dict)]

        for item in preview_items:
            line = format_item_line(item)

            if line:
                linhas.append(line)

        remaining = len(items) - len(preview_items)

        if remaining > 0:
            linhas.append(
                host._presenter_text(
                    "pagination",
                    "moreDetailRecords",
                    count=str(remaining),
                )
            )

        if table_hint and len(items) > cls._PREVIEW_MAX:
            linhas.append(table_hint)

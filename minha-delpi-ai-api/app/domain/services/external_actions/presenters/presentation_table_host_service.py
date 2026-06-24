"""Tabelas genéricas para schema-first — extraído dos presenters de produto removidos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as OpsTable,
)
from app.domain.services.chat_presentation_table_profile_inference_service import (
    ChatPresentationTableProfileInferenceService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


def infer_items_title(items: list, path: str) -> str | None:
    title = ChatAssistantContentService.title_for_path(
        "presenter_content",
        path,
        path_key="titlesByPathFragment",
    )

    if title:
        return title

    if items and isinstance(items[0], dict):
        first = items[0]

        if ("level" in first or "quantity" in first) and "code" in first:
            return ChatAssistantContentService.get(
                "presenter_content",
                "titlesByItemShape",
                "structure",
            )

        if "branch" in first or "warehouse" in first:
            return ChatAssistantContentService.get(
                "presenter_content",
                "titlesByItemShape",
                "stock",
            )

    return None


def build_items_table(
    host: ExternalActionResultPresenter,
    items: list,
    title: str | None = None,
    *,
    path: str = "",
    profile_name: str | None = None,
    entity: str | None = None,
    role: str = "generic",
) -> dict | None:
    if not items:
        return None

    dict_items = [item for item in items if isinstance(item, dict)]

    if not dict_items:
        return None

    effective_path = host._effective_presentation_path(path)

    if not title:
        title = host._presenter_text("generic", "itemsTableDefaultTitle")

    resolved_profile = profile_name or ChatPresentationTableProfileInferenceService.infer_profile_name(
        path=effective_path,
        entity=entity,
        sample_row=dict_items[0],
        column_labels=host._column_labels,
    )

    return OpsTable.build_items_table(
        host.column_label_context,
        dict_items,
        title=title,
        role=role,
        path=effective_path,
        profile_name=resolved_profile,
    )


def escape_markdown_table_cell(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_table(columns: list[tuple[str, str]], rows: list[dict]) -> list[str]:
    if not rows:
        return []

    header = "| " + " | ".join(label for _, label in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(escape_markdown_table_cell(row.get(key)) for key, _ in columns)
        + " |"
        for row in rows
    ]

    return [header, separator, *body]

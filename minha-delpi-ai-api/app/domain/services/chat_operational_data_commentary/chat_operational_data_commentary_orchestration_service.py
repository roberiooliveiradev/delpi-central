"""Delegate — comentário operacional."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_humanized_data_response_service import (
    ChatHumanizedDataResponseService,
)
from app.domain.services.chat_operational_commentary_builder_registry_service import (
    ChatOperationalCommentaryBuilderRegistryService,
)
from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_presentation_operational_table_service import (
    ChatPresentationOperationalTableService as _OpsTable,
)

from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)


class ChatOperationalDataCommentaryOrchestrationService:
    @classmethod
    def build(
        cls,
        profile_key: str,
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        key = str(profile_key or "").strip()

        if not isinstance(data, dict) or not key:
            return None

        if key not in ChatOperationalCommentaryProfileService.registered_profile_keys():
            return None

        metadata_only = ChatOperationalCommentaryProfileService.try_build_metadata_only(key)

        if metadata_only is not None:
            return metadata_only

        commentary = ChatOperationalCommentaryBuilderRegistryService.build(
            key,
            data,
            format_quantity=format_quantity,
        )

        if not commentary:
            return None

        if not (commentary.get("highlights") or commentary.get("attention")):
            if not commentary.get("visualHints") and not commentary.get("metadataOnly"):
                return None

        commentary["profileKey"] = key
        commentary["narrativeInsight"] = (
            ChatOperationalDataCommentarySupportService._build_narrative_insight(commentary)
        )

        return ChatHumanizedDataResponseService.normalize(commentary, profile_key=key)

    @classmethod
    def render_markdown_sections(cls, commentary: dict[str, Any] | None) -> str:
        if not isinstance(commentary, dict):
            return ""

        parts: list[str] = []
        quick_layer = ChatHumanizedDataResponseService.render_quick_layer_markdown(commentary)

        if quick_layer:
            parts.append(quick_layer)

        highlights = [
            str(line).strip()
            for line in (commentary.get("highlights") or [])
            if str(line or "").strip()
        ]
        attention = [
            str(line).strip()
            for line in (commentary.get("attention") or [])
            if str(line or "").strip()
        ]
        profile_key = ChatOperationalCommentaryProfileService.content_section(
            str(commentary.get("profileKey") or "factory_status")
        )

        if highlights:
            parts.extend(
                [
                    "",
                    ChatOperationalDataCommentarySupportService._text(
                        profile_key,
                        "highlightsHeader",
                    ),
                    "",
                    *[f"- {line}" for line in highlights],
                ]
            )

        if attention:
            parts.extend(
                [
                    "",
                    ChatOperationalDataCommentarySupportService._text(
                        profile_key,
                        "attentionHeader",
                    ),
                    "",
                    *[f"{index}. {line}" for index, line in enumerate(attention, start=1)],
                ]
            )

        return _OpsTable.join_markdown_blocks(parts)

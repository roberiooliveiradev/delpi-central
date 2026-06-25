from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.application.services.chat_canvas_ambiguity_service import (
    ChatCanvasAmbiguityService,
)
from app.domain.services.chat_attachment_content_service import ChatAttachmentContentService
from app.domain.services.chat_canvas_intent_service import ChatCanvasIntentService
from app.domain.services.chat_canvas_transform_service import ChatCanvasTransformService
from app.domain.services.chat_rich_presentation_canvas_export_service import (
    ChatRichPresentationCanvasExportService,
)


@dataclass(frozen=True)
class ChatCanvasOpenPayload:
    title: str
    markdown: str
    source_message_id: str | None


@dataclass(frozen=True)
class ChatCanvasAction:
    answer: str
    open_payload: ChatCanvasOpenPayload | None


class ChatCanvasContentService:
    """Resolve pedidos de lousa: cópia, append e merge com consultas operacionais."""

    _CANVAS_CONFIRMATION_RE = re.compile(
        r"^coloquei\s+[«\"].+[»\"]\s+na lousa",
        re.IGNORECASE,
    )

    @classmethod
    def resolve(
        cls,
        message: str,
        previous_messages: list[Any] | None,
        workspace_context: dict | None,
    ) -> ChatCanvasAction | None:
        if not (
            ChatCanvasIntentService.is_canvas_request(message)
            or ChatCanvasIntentService.is_canvas_transform_request(message)
        ):
            return None

        if not cls._canvas_enabled(workspace_context):
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("disabled"),
                open_payload=None,
            )

        if ChatCanvasIntentService.is_canvas_transform_request(message):
            return cls._resolve_transform(message, previous_messages)

        if ChatCanvasIntentService.is_canvas_operational_update_request(message):
            return None

        if ChatCanvasAmbiguityService.is_deictic_canvas_request(message):
            clarification = ChatCanvasAmbiguityService.build_clarification_answer(
                previous_messages=previous_messages,
            )

            if clarification:
                return ChatCanvasAction(answer=clarification, open_payload=None)

        if ChatCanvasIntentService.is_canvas_update_request(message):
            return cls._resolve_content_append(message, previous_messages)

        return cls._resolve_simple_copy(previous_messages)

    @classmethod
    def build_update_from_tools(
        cls,
        message: str,
        tool_calls: list[dict] | None,
        previous_messages: list[Any] | None,
        workspace_context: dict | None,
    ) -> ChatCanvasAction | None:
        if not ChatCanvasIntentService.is_canvas_operational_update_request(message):
            return None

        if not cls._canvas_enabled(workspace_context):
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("disabled"),
                open_payload=None,
            )

        base_markdown, base_title, source_message_id = cls._resolve_base_canvas_content(
            previous_messages
        )

        if not base_markdown:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("noContentToUpdate"),
                open_payload=None,
            )

        sections = cls._tool_calls_to_markdown_sections(tool_calls or [])

        if not sections:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("toolFetchFailed"),
                open_payload=None,
            )

        merged_markdown = cls._merge_markdown(base_markdown, sections)

        return ChatCanvasAction(
            answer=ChatAttachmentContentService.canvas_text(
                "operationalUpdateSuccess",
                title=base_title,
                count=str(len(sections)),
            ),
            open_payload=ChatCanvasOpenPayload(
                title=base_title,
                markdown=merged_markdown,
                source_message_id=source_message_id,
            ),
        )

    @classmethod
    def _resolve_transform(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> ChatCanvasAction:
        kind = ChatCanvasTransformService.detect_kind(message)

        if not kind:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("transformFormatUnknown"),
                open_payload=None,
            )

        base_markdown, base_title, source_message_id = cls._resolve_base_canvas_content(
            previous_messages
        )

        if not base_markdown:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("noContentToTransform"),
                open_payload=None,
            )

        transformed, label = ChatCanvasTransformService.transform(base_markdown, kind)
        title = (
            ChatAttachmentContentService.canvas_text(
                "transformTitleWithBase",
                label=label,
                baseTitle=base_title,
            )
            if base_title
            else label
        )

        return ChatCanvasAction(
            answer=ChatAttachmentContentService.canvas_text(
                "transformSuccess",
                label=label,
            ),
            open_payload=ChatCanvasOpenPayload(
                title=title[:120],
                markdown=transformed,
                source_message_id=source_message_id,
            ),
        )

    @classmethod
    def _resolve_simple_copy(
        cls,
        previous_messages: list[Any] | None,
    ) -> ChatCanvasAction:
        export_markdown, export_title = cls._last_drawing_export_from_history(
            previous_messages
        )

        if export_markdown:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text(
                    "drawingCopySuccess",
                    title=export_title,
                ),
                open_payload=ChatCanvasOpenPayload(
                    title=export_title,
                    markdown=export_markdown,
                    source_message_id=cls._last_drawing_source_message_id(previous_messages),
                ),
            )

        source = cls._find_last_substantive_assistant_message(previous_messages)

        if not source:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("noAssistantResponse"),
                open_payload=None,
            )

        metadata = cls._message_metadata(source)
        markdown = ChatRichPresentationCanvasExportService.build_markdown_from_assistant(
            str(source.get("content") or ""),
            metadata,
        ).strip()

        if not markdown:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("emptyAssistantResponse"),
                open_payload=None,
            )

        title = cls._derive_title(markdown)
        source_message_id = cls._message_id(source)

        return ChatCanvasAction(
            answer=ChatAttachmentContentService.canvas_text(
                "simpleCopySuccess",
                title=title,
            ),
            open_payload=ChatCanvasOpenPayload(
                title=title,
                markdown=markdown,
                source_message_id=source_message_id,
            ),
        )

    @classmethod
    def _resolve_content_append(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> ChatCanvasAction:
        base_markdown, base_title, source_message_id = cls._resolve_base_canvas_content(
            previous_messages
        )
        addition = cls._find_last_substantive_assistant_message(previous_messages)

        if not base_markdown and not addition:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("noContentToAppend"),
                open_payload=None,
            )

        if not base_markdown:
            return cls._resolve_simple_copy(previous_messages)

        if not addition:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("noRecentResponseToAppend"),
                open_payload=None,
            )

        addition_markdown = ChatRichPresentationCanvasExportService.build_markdown_from_assistant(
            str(addition.get("content") or ""),
            addition.get("metadata"),
        ).strip()

        if not addition_markdown:
            return ChatCanvasAction(
                answer=ChatAttachmentContentService.canvas_text("emptyAssistantResponse"),
                open_payload=None,
            )

        merged_markdown = cls._merge_markdown(base_markdown, [addition_markdown])

        return ChatCanvasAction(
            answer=ChatAttachmentContentService.canvas_text(
                "appendUpdateSuccess",
                title=base_title,
            ),
            open_payload=ChatCanvasOpenPayload(
                title=base_title,
                markdown=merged_markdown,
                source_message_id=source_message_id or cls._message_id(addition),
            ),
        )

    @classmethod
    def _resolve_base_canvas_content(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[str, str, str | None]:
        existing_markdown, existing_title, source_message_id = (
            cls._find_existing_canvas_from_history(previous_messages)
        )

        if existing_markdown:
            return existing_markdown, existing_title, source_message_id

        source = cls._find_last_substantive_assistant_message(previous_messages)

        if not source:
            return "", ChatAttachmentContentService.canvas_default_title(), None

        metadata = cls._message_metadata(source)
        markdown = ChatRichPresentationCanvasExportService.build_markdown_from_assistant(
            str(source.get("content") or ""),
            metadata,
        ).strip()

        if not markdown:
            return "", ChatAttachmentContentService.canvas_default_title(), None

        return markdown, cls._derive_title(markdown), cls._message_id(source)

    @classmethod
    def find_active_canvas(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[str, str, str | None]:
        """Markdown, título e sourceMessageId da lousa mais recente no histórico."""
        from app.domain.services.chat_canvas_history_service import ChatCanvasHistoryService

        return ChatCanvasHistoryService.find_active_canvas(previous_messages)

    @classmethod
    def _find_existing_canvas_from_history(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[str, str, str | None]:
        return cls.find_active_canvas(previous_messages)

    @classmethod
    def _tool_calls_to_markdown_sections(cls, tool_calls: list[dict]) -> list[str]:
        sections: list[str] = []

        for tool_call in tool_calls:
            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            section = cls._metadata_to_markdown_section(metadata)

            if section and section not in sections:
                sections.append(section)

        return sections

    @classmethod
    def _metadata_to_markdown_section(cls, metadata: dict) -> str | None:
        sections = ChatRichPresentationCanvasExportService.sections_from_tool_metadata(
            metadata
        )
        text_presentation = metadata.get("textPresentation")

        if isinstance(text_presentation, dict):
            markdown = str(text_presentation.get("markdown") or "").strip()

            if markdown:
                sections = [markdown, *sections]

        if not sections:
            return None

        return "\n\n".join(section for section in sections if section).strip() or None

    @classmethod
    def _merge_markdown(cls, base_markdown: str, sections: list[str]) -> str:
        parts = [str(base_markdown or "").strip()]

        for section in sections:
            cleaned = str(section or "").strip()

            if cleaned and cleaned not in parts[-1]:
                parts.append(cleaned)

        return "\n\n".join(part for part in parts if part)

    @classmethod
    def _canvas_enabled(cls, workspace_context: dict | None) -> bool:
        capabilities = (workspace_context or {}).get("capabilities") or {}
        canvas = capabilities.get("canvas")

        if isinstance(canvas, bool):
            return canvas

        return True

    @classmethod
    def _last_drawing_export_from_history(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[str | None, str]:
        if not previous_messages:
            return None, ChatAttachmentContentService.canvas_text("drawingReportDefault")

        for message in reversed(previous_messages):
            if str(cls._message_role(message) or "").lower() != "assistant":
                continue

            metadata = cls._message_metadata(message)
            export = metadata.get("drawingAnalysisExport")

            if not isinstance(export, dict):
                continue

            markdown = str(export.get("markdown") or "").strip()

            if not markdown:
                continue

            drawing = metadata.get("drawingAnalysis")

            code = ""

            if isinstance(drawing, dict):
                code = str(drawing.get("productCode") or "").strip()

            title = (
                ChatAttachmentContentService.canvas_text("drawingAnalysisTitle", code=code)
                if code
                else ChatAttachmentContentService.canvas_text("drawingReportDelpi")
            )

            return markdown, title

        return None, ChatAttachmentContentService.canvas_text("drawingReportDefault")

    @classmethod
    def _last_drawing_source_message_id(
        cls,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not previous_messages:
            return None

        for message in reversed(previous_messages):
            if str(cls._message_role(message) or "").lower() != "assistant":
                continue

            metadata = cls._message_metadata(message)

            if isinstance(metadata.get("drawingAnalysisExport"), dict):
                return cls._message_id(message)

        return None

    @classmethod
    def _find_last_substantive_assistant_message(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        if not previous_messages:
            return None

        for message in reversed(previous_messages):
            role = cls._message_role(message)

            if str(role or "").lower() != "assistant":
                continue

            content = cls._message_content(message)
            text = str(content or "").strip()

            if not text:
                continue

            if cls._is_canvas_confirmation_message(text):
                continue

            return {
                "id": cls._message_id(message),
                "content": text,
                "metadata": cls._message_metadata(message),
            }

        return None

    @classmethod
    def _is_canvas_confirmation_message(cls, content: str) -> bool:
        normalized = " ".join(str(content or "").split())

        if cls._CANVAS_CONFIRMATION_RE.match(normalized):
            return True

        lowered = normalized.lower()

        return lowered.startswith("coloquei ") and " na lousa" in lowered

    @classmethod
    def _derive_title(cls, markdown: str) -> str:
        for line in markdown.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("#"):
                return (
                    stripped.lstrip("#").strip()[:80]
                    or ChatAttachmentContentService.canvas_default_title()
                )

            plain = stripped.replace("**", "").replace("*", "").strip()

            if plain:
                return plain[:80]

        return ChatAttachmentContentService.canvas_default_title()

    @classmethod
    def _message_role(cls, message: Any) -> str | None:
        role = getattr(message, "role", None)

        if role is None and isinstance(message, dict):
            role = message.get("role")

        return str(role) if role is not None else None

    @classmethod
    def _message_content(cls, message: Any) -> str | None:
        content = getattr(message, "content", None)

        if content is None and isinstance(message, dict):
            content = message.get("content")

        return str(content) if content is not None else None

    @classmethod
    def _message_id(cls, message: Any) -> str | None:
        message_id = getattr(message, "id", None)

        if message_id is None and isinstance(message, dict):
            message_id = message.get("id")

        return str(message_id) if message_id is not None else None

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        metadata = getattr(message, "metadata", None)

        if metadata is None and isinstance(message, dict):
            metadata = message.get("metadata")

        return metadata if isinstance(metadata, dict) else {}

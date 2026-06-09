"""Textos de anexos e lousa — vocabulário em assistant/attachments.json."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "attachments"


class ChatAttachmentContentService:
    @classmethod
    def handoff_pattern(cls) -> re.Pattern[str]:
        pattern = ChatAssistantContentService.get(
            _BUNDLE,
            "welcome",
            "handoffPattern",
            default=r"^(?:segue|anexo|arquivo)\b",
        )

        return re.compile(pattern, re.IGNORECASE)

    @classmethod
    def short_ack_messages(cls) -> frozenset[str]:
        return frozenset(ChatAssistantContentService.list(_BUNDLE, "welcome", "shortAckMessages"))

    @classmethod
    def max_handoff_message_length(cls) -> int:
        value = ChatAssistantContentService.get_node(_BUNDLE, "welcome", "maxHandoffMessageLength")

        if isinstance(value, int) and value > 0:
            return value

        return 48

    @classmethod
    def welcome_block(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "welcome")

        return node if isinstance(node, dict) else {}

    @classmethod
    def unreadable_body(cls) -> str:
        return ChatAssistantContentService.get(_BUNDLE, "unreadable", "body").strip()

    @classmethod
    def large_file_block(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "largeFile")

        return node if isinstance(node, dict) else {}

    @classmethod
    def large_file_char_threshold(cls) -> int:
        block = cls.large_file_block()
        value = block.get("charThreshold")

        return int(value) if isinstance(value, int) and value > 0 else 120_000

    @classmethod
    def large_file_page_threshold(cls) -> int:
        block = cls.large_file_block()
        value = block.get("pageThreshold")

        return int(value) if isinstance(value, int) and value > 0 else 40

    @classmethod
    def follow_up_chips(cls) -> list[str]:
        return ChatAssistantContentService.list(_BUNDLE, "followUp", "chips")

    @classmethod
    def follow_up_queries(cls) -> dict[str, str]:
        return ChatAssistantContentService.get_mapping(_BUNDLE, "followUp", "queries")

    @classmethod
    def text_task_chips(cls, task: str) -> list[str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "followUp", "textTaskChips")

        if not isinstance(node, dict):
            return []

        chips = node.get(task)

        if not isinstance(chips, list):
            return []

        return [str(item).strip() for item in chips if str(item).strip()]

    @classmethod
    def preview_line(cls, key: str, **values: object) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "preview",
            "lines",
            key,
            **values,
        ).strip()

    @classmethod
    def reading_status_label(cls, status: str | None) -> str:
        mapping = ChatAssistantContentService.get_mapping(_BUNDLE, "preview", "readingStatus")
        normalized = str(status or "").strip().lower()

        return mapping.get(normalized) or mapping.get("default") or "Aguardando envio"

    @classmethod
    def reading_status_format(cls, key: str, **values: object) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "preview",
            "readingStatusFormats",
            key,
            **values,
        ).strip()

    @classmethod
    def index_reason_label(cls, reason: str) -> str | None:
        mapping = ChatAssistantContentService.get_mapping(_BUNDLE, "preview", "indexReason")
        configured = mapping.get(str(reason or "").strip())

        return configured.strip() if isinstance(configured, str) and configured.strip() else None

    @classmethod
    def canvas_text(cls, key: str, **values: str) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "canvasResponses",
            key,
            **values,
        ).strip()

    @classmethod
    def canvas_default_title(cls) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "canvasResponses",
            "defaultTitle",
        ).strip()

    @classmethod
    def deictic_terms(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "canvasAmbiguity", "deicticTerms"))

    @classmethod
    def referent_label(cls, key: str) -> str:
        return ChatAssistantContentService.get(
            _BUNDLE,
            "canvasAmbiguity",
            "referentLabels",
            key,
        ).strip()

    @classmethod
    def format_options_list(cls, options: list[str]) -> str:
        if not options:
            return ""

        if len(options) == 1:
            return options[0]

        joiner = ChatAssistantContentService.get(
            _BUNDLE,
            "canvasAmbiguity",
            "optionsJoiner",
            default=", ",
        )
        last_joiner = ChatAssistantContentService.get(
            _BUNDLE,
            "canvasAmbiguity",
            "optionsLastJoiner",
            default=" ou ",
        )

        return joiner.join(options[:-1]) + last_joiner + options[-1]

    @classmethod
    def clarification_answer(cls, options: list[str]) -> str:
        hint = ChatAssistantContentService.get(
            _BUNDLE,
            "canvasAmbiguity",
            "clarificationHint",
        )
        template = ChatAssistantContentService.get(
            _BUNDLE,
            "canvasAmbiguity",
            "clarificationQuestion",
            default="Você quer colocar na lousa {options}?\n\n{hint}",
        )

        return template.format(
            options=cls.format_options_list(options),
            hint=hint,
        )

    @classmethod
    def min_assistant_content_length(cls) -> int:
        value = ChatAssistantContentService.get_node(
            _BUNDLE,
            "canvasAmbiguity",
            "minAssistantContentLength",
        )

        if isinstance(value, int) and value > 0:
            return value

        return 80

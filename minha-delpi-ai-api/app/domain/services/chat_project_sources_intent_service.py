"""Detecção de perguntas sobre inventário e escopo de fontes de projeto."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatProjectSourcesIntentService:
    _BUNDLE = "turn_preparation"
    _CONTENT_PREFIX = ("directAnswers", "projectSources")
    _FILE_EXTENSION_RE = re.compile(
        r"([^\\/\n?\"'`]+?\.(?:docx|xlsx|pdf|txt|md|csv|pptx))\??",
        re.IGNORECASE,
    )

    @classmethod
    def _normalized(cls, message: str) -> str:
        return re.sub(r"\s+", " ", str(message or "").strip().lower())

    @classmethod
    def _normalize_match_key(cls, value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or "").casefold())
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"\s+", " ", text)
        text = text.replace("1o ", "1º ").replace("1o.", "1º.")

        return text.strip()

    @classmethod
    def _phrase_list(cls, key: str) -> tuple[str, ...]:
        phrases = ChatAssistantContentService.list(
            cls._BUNDLE,
            *cls._CONTENT_PREFIX,
            key,
        )

        return tuple(phrase.strip().lower() for phrase in phrases if phrase.strip())

    @classmethod
    def _matches_any(cls, message: str, key: str) -> bool:
        normalized = cls._normalized(message)

        if not normalized:
            return False

        return any(phrase in normalized for phrase in cls._phrase_list(key))

    @classmethod
    def is_inventory_question(cls, message: str) -> bool:
        return cls._matches_any(message, "inventoryPhrases")

    @classmethod
    def is_content_question(
        cls,
        message: str,
        *,
        memory_snapshot: dict | None = None,
        previous_messages: list | None = None,
    ) -> bool:
        if cls._matches_any(message, "contentQuestionPhrases"):
            return True

        if cls.extract_document_reference(message):
            return True

        from app.domain.services.chat_project_source_slot_resolver_service import (
            ChatProjectSourceSlotResolverService,
        )
        from app.domain.services.chat_project_sources_inventory_service import (
            ChatProjectSourcesInventoryService,
        )

        if ChatProjectSourceSlotResolverService.looks_like_slot_reference(message):
            inventory = ChatProjectSourcesInventoryService.read_inventory(
                memory_snapshot,
                previous_messages=previous_messages,
            )

            if inventory:
                return True

        return False

    @classmethod
    def resolve_slotted_source(
        cls,
        message: str,
        *,
        memory_snapshot: dict | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        from app.domain.services.chat_project_source_slot_resolver_service import (
            ChatProjectSourceSlotResolverService,
        )
        from app.domain.services.chat_project_sources_inventory_service import (
            ChatProjectSourcesInventoryService,
        )

        inventory = ChatProjectSourcesInventoryService.read_inventory(
            memory_snapshot,
            previous_messages=previous_messages,
        )

        if not inventory:
            return None

        return ChatProjectSourceSlotResolverService.resolve(message, inventory)

    @classmethod
    def extract_document_reference(cls, message: str) -> str | None:
        raw = str(message or "").strip()

        if not raw:
            return None

        match = cls._FILE_EXTENSION_RE.search(raw)

        if not match:
            return None

        return match.group(1).strip(" \"'`")

    @classmethod
    def should_restrict_to_project_sources(
        cls,
        message: str,
        *,
        memory_snapshot: dict | None = None,
        previous_messages: list | None = None,
    ) -> bool:
        if cls.is_inventory_question(message):
            return True

        if cls.is_content_question(
            message,
            memory_snapshot=memory_snapshot,
            previous_messages=previous_messages,
        ):
            return True

        return cls._matches_any(message, "scopedPhrases")

    @classmethod
    def _chunk_scope(cls, chunk: dict) -> str:
        metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}

        return str(
            metadata.get("scope")
            or chunk.get("sourceType")
            or chunk.get("scope")
            or ""
        ).strip()

    @classmethod
    def _chunk_title(cls, chunk: dict) -> str:
        metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}

        return str(
            chunk.get("title")
            or metadata.get("originalFilename")
            or metadata.get("original_filename")
            or ""
        ).strip()

    @classmethod
    def chunk_matches_document_reference(cls, chunk: dict, reference: str) -> bool:
        reference_key = cls._normalize_match_key(reference)
        title_key = cls._normalize_match_key(cls._chunk_title(chunk))

        if not reference_key or not title_key:
            return False

        return reference_key in title_key or title_key in reference_key

    @classmethod
    def build_content_chunk_filter(
        cls,
        message: str,
        *,
        memory_snapshot: dict | None = None,
        previous_messages: list | None = None,
    ) -> Callable[[dict], bool] | None:
        if not cls.is_content_question(
            message,
            memory_snapshot=memory_snapshot,
            previous_messages=previous_messages,
        ):
            return None

        reference = cls.extract_document_reference(message)
        slotted = cls.resolve_slotted_source(
            message,
            memory_snapshot=memory_snapshot,
            previous_messages=previous_messages,
        )
        slotted_source_id = str((slotted or {}).get("projectSourceId") or "").strip()

        def _filter(chunk: dict) -> bool:
            scope = cls._chunk_scope(chunk)

            if scope != "project_source" and chunk.get("sourceType") != "project_source":
                return False

            if slotted_source_id:
                document_id = str(chunk.get("documentId") or "").strip()
                metadata = chunk.get("metadata") if isinstance(chunk.get("metadata"), dict) else {}
                metadata_document_id = str(metadata.get("documentId") or "").strip()

                return document_id == slotted_source_id or metadata_document_id == slotted_source_id

            if reference:
                return cls.chunk_matches_document_reference(chunk, reference)

            return True

        return _filter

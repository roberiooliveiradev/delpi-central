"""Fast-path de turno curto — padrões via ``fast_path.json``."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_small_talk_pattern_service import ChatSmallTalkPatternService


@lru_cache(maxsize=8)
def _fast_path_pattern(key: str) -> re.Pattern[str]:
    source = ChatAssistantContentService.get("fast_path", "patterns", key, default="")

    if not str(source or "").strip():
        raise KeyError(f"fast_path.patterns.{key} ausente")

    return re.compile(str(source), re.IGNORECASE)


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


class ChatFastPathService:
    @staticmethod
    def is_small_talk(message: str) -> bool:
        return ChatSmallTalkPatternService.is_small_talk(message)

    @staticmethod
    def should_use(
        message: str,
        *,
        enabled: bool = True,
        max_chars: int = 30,
        attachment_ids: list[str] | None = None,
        previous_messages: list | None = None,
        workspace_context: dict | None = None,
        host_context: dict | None = None,
    ) -> bool:
        if not enabled:
            return False

        if attachment_ids:
            return False

        text = str(message or "").strip()

        if previous_messages and ChatFastPathService._requires_tools_after_session_reply(
            text,
            previous_messages=previous_messages,
        ):
            return False

        if not text:
            return False

        # Confirmação de write / apply TV não pode pular tools.
        from app.domain.services.chat_write_confirmation_service import (
            ChatWriteConfirmationService,
        )

        if ChatWriteConfirmationService.user_confirmed(text):
            return False

        from app.domain.services.chat_host_surface_context_service import (
            ChatHostSurfaceContextService,
        )
        from app.domain.services.chat_tv_dashboard_copilot_intent_service import (
            ChatTvDashboardCopilotIntentService,
        )

        if ChatTvDashboardCopilotIntentService.matches(text):
            return False

        if ChatHostSurfaceContextService.is_tv_mutation_turn(
            text,
            host_context,
            workspace_context=workspace_context,
        ):
            return False

        if ChatFastPathService.is_small_talk(text):
            return True

        if len(text) > max(1, max_chars):
            return False

        normalized = _normalize_text(text)

        # Retry / follow-up operacional nunca esvazia tools (ex.: «tente novamente»).
        from app.domain.services.chat_error_auto_recovery_service import (
            ChatErrorAutoRecoveryService,
        )
        from app.domain.services.chat_follow_up_intent_service import (
            ChatFollowUpIntentService,
        )

        if ChatErrorAutoRecoveryService.looks_like_recovery_request(text):
            return False

        if ChatFollowUpIntentService.is_operational_follow_up(text):
            return False

        if ChatFollowUpIntentService.is_retry_or_continue_request(text):
            return False

        if _fast_path_pattern("knowledgeHint").search(normalized):
            return False

        if _fast_path_pattern("operationalHint").search(text):
            return False

        if _fast_path_pattern("refinementHint").search(normalized):
            return False

        if normalized in set(
            ChatAssistantContentService.list("fast_path", "blockedExactNormalized")
        ):
            return False

        word_count = len(normalized.split())

        return word_count <= 2 and not normalized.endswith("?")

    @staticmethod
    def _requires_tools_after_session_reply(
        message: str,
        *,
        previous_messages: list,
    ) -> bool:
        from app.domain.services.chat_active_pending_service import (
            ChatActivePendingService,
        )
        from app.domain.services.chat_active_query_session_service import (
            ChatActiveQuerySessionService,
        )

        pending = ChatActivePendingService.find_from_messages(previous_messages)

        if pending:
            resolved = ChatActivePendingService.try_resolve(message, pending)

            if resolved and resolved.get("requiresTool"):
                return True

        session = ChatActiveQuerySessionService.find_session_from_messages(previous_messages)

        if session and ChatActiveQuerySessionService.should_continue_session(
            message,
            session,
        ):
            return True

        return False

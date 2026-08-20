"""Reescreve «tente novamente» para a última pergunta operacional da sessão."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_error_auto_recovery_service import (
    ChatErrorAutoRecoveryService,
)
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatOperationalRetryMessageService:
    @classmethod
    def rewrite_if_needed(
        cls,
        message: str | None,
        previous_messages: list[Any] | None,
    ) -> tuple[str, bool]:
        raw = str(message or "").strip()

        if not raw or not ChatFollowUpIntentService.is_retry_or_continue_request(raw):
            return raw, False

        # Se já há tool operacional no histórico, o recovery de erro trata.
        operation = ChatErrorAutoRecoveryService.collect_operation(
            None,
            previous_messages=previous_messages,
            prefer_failed=True,
        ) or ChatErrorAutoRecoveryService.collect_operation(
            None,
            previous_messages=previous_messages,
            prefer_failed=False,
        )

        if operation and operation.get("actionId"):
            return raw, False

        prior = cls._last_operational_user_message(previous_messages)

        if prior and prior.lower() != raw.lower():
            return prior, True

        return raw, False

    @classmethod
    def _last_operational_user_message(
        cls,
        previous_messages: list[Any] | None,
    ) -> str | None:
        for item in reversed(previous_messages or []):
            if not isinstance(item, dict):
                continue
            if str(item.get("role") or "").strip().lower() != "user":
                continue
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            if ChatFollowUpIntentService.is_retry_or_continue_request(content):
                continue
            if ChatProductQueryIntentService.extract_product_code(content):
                return content
            if ChatFollowUpIntentService.is_operational_follow_up(content):
                return content
            lowered = content.lower()
            if any(
                token in lowered
                for token in (
                    "estoque",
                    "produto",
                    "fornecedor",
                    "estrutura",
                    "sql",
                    "ov",
                    "kpi",
                    "lmp",
                )
            ):
                return content

        return None

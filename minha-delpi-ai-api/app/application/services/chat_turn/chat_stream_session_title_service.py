"""Título automático de sessão no stream — Fase 4B lote 2."""

from __future__ import annotations

import logging
import threading
from uuid import UUID

from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.infrastructure.config.settings import Settings


logger = logging.getLogger("minha-delpi-ai-api.stream_chat")


class ChatStreamSessionTitleService:
    @staticmethod
    def should_generate(
        session,
        previous_messages: list | None,
        *,
        resend_from_message_id: str | None,
    ) -> bool:
        if resend_from_message_id:
            return False

        if previous_messages:
            return False

        title = (session.title or "").strip().lower()
        empty_titles = {
            "",
            *(
                str(item).strip().lower()
                for item in ChatAssistantContentService.list(
                    "stream",
                    "sessionTitleEmptyValues",
                )
            ),
        }

        return title in empty_titles

    @staticmethod
    def fallback_from_message(message: str) -> str:
        normalized = " ".join(message.split()).strip()

        if not normalized:
            return str(
                ChatAssistantContentService.get("stream", "sessionTitleDefault")
                or "Nova conversa"
            )

        if len(normalized) <= 48:
            return normalized

        return normalized[:48].rstrip() + "..."

    @staticmethod
    def apply_fallback_rename(
        chat_repository: ChatSessionRepositoryPort,
        *,
        session_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        chat_repository.rename_session(
            session_id=session_id,
            user_id=user_id,
            title=ChatStreamSessionTitleService.fallback_from_message(message),
        )

    def schedule_llm_refine(
        self,
        *,
        chat_repository: ChatSessionRepositoryPort,
        llm_gateway: LlmGatewayPort,
        session_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        if not Settings.CHAT_SESSION_TITLE_LLM_ENABLED:
            return

        from flask import current_app, has_app_context

        if not has_app_context():
            return

        app = current_app._get_current_object()

        def worker() -> None:
            with app.app_context():
                try:
                    self._generate_and_apply(
                        chat_repository=chat_repository,
                        llm_gateway=llm_gateway,
                        session_id=session_id,
                        user_id=user_id,
                        message=message,
                    )
                    from app.extensions.db import db

                    db.session.commit()
                except Exception:
                    from app.extensions.db import db

                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    logger.exception("session_title_llm_refine_failed")

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _generate_and_apply(
        *,
        chat_repository: ChatSessionRepositoryPort,
        llm_gateway: LlmGatewayPort,
        session_id: UUID,
        user_id: UUID,
        message: str,
    ) -> None:
        fallback_title = ChatStreamSessionTitleService.fallback_from_message(message)
        title_system = str(
            ChatAssistantContentService.get("stream", "titleGenerationSystem") or ""
        )
        title_user_template = str(
            ChatAssistantContentService.get("stream", "titleGenerationUserTemplate") or ""
        )

        try:
            generated_title = llm_gateway.generate(
                [
                    {"role": "system", "content": title_system},
                    {
                        "role": "user",
                        "content": title_user_template.format(message=message),
                    },
                ]
            ).strip()
        except Exception:
            generated_title = fallback_title

        title = ChatStreamSessionTitleService._normalize_generated_title(
            generated_title
        ) or fallback_title

        chat_repository.rename_session(
            session_id=session_id,
            user_id=user_id,
            title=title,
        )

    @staticmethod
    def _normalize_generated_title(value: str) -> str:
        normalized = " ".join(value.replace("\n", " ").split())
        normalized = normalized.strip(" .\"'`")

        if not normalized:
            return ""

        if len(normalized) > 80:
            normalized = normalized[:80].rstrip()

        return normalized

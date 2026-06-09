"""Agendamento de indexação de anexos em background (upload não bloqueante)."""

from __future__ import annotations

import logging
import threading
from uuid import UUID

from flask import Flask

from app.extensions.db import db

logger = logging.getLogger(__name__)


class ChatAttachmentIndexSchedulerService:
    @classmethod
    def enqueue(
        cls,
        app: Flask,
        *,
        user_id: str,
        session_id: str,
        attachment_id: str,
    ) -> None:
        thread = threading.Thread(
            target=cls._run,
            kwargs={
                "app": app,
                "user_id": user_id,
                "session_id": session_id,
                "attachment_id": attachment_id,
            },
            daemon=True,
            name=f"chat-attachment-index-{attachment_id}",
        )
        thread.start()

    @classmethod
    def _run(
        cls,
        app: Flask,
        *,
        user_id: str,
        session_id: str,
        attachment_id: str,
    ) -> None:
        with app.app_context():
            try:
                from app.composition.chat_composer import (
                    make_index_chat_attachment_use_case,
                )
                from app.composition.repository_composer import (
                    make_chat_attachment_repository,
                )

                repository = make_chat_attachment_repository()
                attachment = repository.get_attachment_by_id(
                    user_id=UUID(user_id),
                    attachment_id=UUID(attachment_id),
                )

                if not attachment:
                    logger.warning(
                        "chat_attachment_index_missing",
                        extra={
                            "attachment_id": attachment_id,
                            "session_id": session_id,
                        },
                    )
                    return

                if str(attachment.status) not in {"indexing", "uploaded"}:
                    return

                make_index_chat_attachment_use_case().execute(
                    user_id=user_id,
                    attachment=attachment,
                )
                db.session.commit()
            except Exception:
                logger.exception(
                    "chat_attachment_index_failed",
                    extra={
                        "attachment_id": attachment_id,
                        "session_id": session_id,
                    },
                )

                try:
                    db.session.rollback()
                except Exception:
                    pass

                cls._mark_index_failed(user_id=user_id, attachment_id=attachment_id)

    @classmethod
    def _mark_index_failed(cls, *, user_id: str, attachment_id: str) -> None:
        try:
            from app.composition.repository_composer import (
                make_chat_attachment_repository,
            )

            repository = make_chat_attachment_repository()
            repository.update_status(
                attachment_id=UUID(attachment_id),
                status="index_failed",
                metadata={
                    "indexed": False,
                    "indexReason": "background_index_failed",
                },
            )
            db.session.commit()
        except Exception:
            logger.exception(
                "chat_attachment_index_failed_status_update",
                extra={"attachment_id": attachment_id, "user_id": user_id},
            )

            try:
                db.session.rollback()
            except Exception:
                pass

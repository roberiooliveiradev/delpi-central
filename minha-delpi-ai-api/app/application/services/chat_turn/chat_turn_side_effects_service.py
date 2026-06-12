"""Efeitos colaterais best-effort no início do turno — send e stream."""

from __future__ import annotations


class ChatTurnSideEffectsService:
    @staticmethod
    def warm_learned_normalization() -> None:
        try:
            from app.application.services.chat_learned_normalization_service import (
                ChatLearnedNormalizationService,
            )

            ChatLearnedNormalizationService().ensure_loaded()
        except Exception:
            return

    @staticmethod
    def capture_learning_from_turn(*, message: str, session, user_id: str) -> None:
        try:
            from app.infrastructure.config.settings import Settings

            from app.application.services.chat_platform_runtime_access import (
                learning_pipeline_settings,
            )

            learning = learning_pipeline_settings()

            if not learning.get("learningEnabled") or not learning.get(
                "learningCaptureFromTurn"
            ):
                return

            from app.application.services.chat_learning_capture_service import (
                ChatLearningCaptureService,
            )

            project_id = getattr(session, "project_id", None)
            ChatLearningCaptureService().capture_explicit_definition_from_turn(
                message=message,
                project_id=str(project_id) if project_id else None,
                created_by=user_id,
            )
        except Exception:
            return

    @staticmethod
    def capture_user_memory_from_turn(
        *,
        message: str,
        session,
        user_id: str,
        session_id: str,
    ) -> None:
        try:
            from app.infrastructure.config.settings import Settings

            if not Settings.CHAT_USER_MEMORY_ENABLED or not Settings.CHAT_USER_MEMORY_CAPTURE:
                return

            from app.application.services.chat_user_memory_service import (
                ChatUserMemoryService,
            )

            project_id = getattr(session, "project_id", None)
            ChatUserMemoryService().capture_from_turn(
                message=message,
                user_id=user_id,
                project_id=str(project_id) if project_id else None,
                session_id=session_id,
            )
        except Exception:
            return

    @staticmethod
    def capture_glossary_from_turn(*, message: str, session, user_id: str) -> None:
        try:
            from app.application.services.chat_platform_runtime_access import (
                learning_pipeline_settings,
            )

            learning = learning_pipeline_settings()

            if not learning.get("learningEnabled") or not learning.get(
                "learningGlossaryCapture"
            ):
                return

            from app.application.services.chat_meaning_discovery_service import (
                ChatMeaningDiscoveryService,
            )

            project_id = getattr(session, "project_id", None)
            ChatMeaningDiscoveryService().capture_unknown_term_from_turn(
                message=message,
                project_id=str(project_id) if project_id else None,
                created_by=user_id,
            )
        except Exception:
            return

    @classmethod
    def capture_all_from_turn(
        cls,
        *,
        message: str,
        session,
        user_id: str,
        session_id: str,
    ) -> None:
        cls.capture_learning_from_turn(message=message, session=session, user_id=user_id)
        cls.capture_user_memory_from_turn(
            message=message,
            session=session,
            user_id=user_id,
            session_id=session_id,
        )
        cls.capture_glossary_from_turn(message=message, session=session, user_id=user_id)

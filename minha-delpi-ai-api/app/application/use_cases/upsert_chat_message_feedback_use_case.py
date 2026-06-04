from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.domain.exceptions.chat_exceptions import (
    ChatSessionAccessDeniedError,
    ChatSessionNotFoundError,
)
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.services.chat_feedback_admin_metrics_service import (
    ChatFeedbackAdminMetricsService,
)
from app.domain.services.chat_feedback_content_service import ChatFeedbackContentService
from app.domain.services.chat_feedback_context_service import ChatFeedbackContextService
from app.infrastructure.persistence.postgres_chat_message_feedback_repository import (
    PostgresChatMessageFeedbackRepository,
)


class UpsertChatMessageFeedbackUseCase:
    def __init__(
        self,
        session_repository: ChatSessionRepositoryPort,
        feedback_repository: PostgresChatMessageFeedbackRepository | None = None,
    ):
        self.session_repository = session_repository
        self.feedback_repository = feedback_repository or PostgresChatMessageFeedbackRepository()

    def execute(
        self,
        *,
        user_id: str,
        session_id: str,
        message_id: str,
        rating: int | None,
        reason: str | None = None,
        comment: str | None = None,
    ) -> dict | None:
        session = self.session_repository.get_session_by_id(UUID(session_id))

        if not session:
            raise ChatSessionNotFoundError()

        if str(session.user_id) != user_id:
            raise ChatSessionAccessDeniedError()

        message_session_id = self.feedback_repository.get_message_session_id(UUID(message_id))

        if not message_session_id or str(message_session_id) != session_id:
            raise ValueError("message not found in session")

        assistant = self.feedback_repository.get_assistant_message(UUID(message_id))

        if not assistant:
            raise ValueError("feedback is only available for assistant messages")

        user_uuid = UUID(user_id)
        message_uuid = UUID(message_id)

        if rating is None:
            removed = self.feedback_repository.delete_feedback(
                message_id=message_uuid,
                user_id=user_uuid,
            )

            return {"removed": removed}

        if rating not in (-1, 1):
            raise ValueError("rating must be -1 or 1")

        normalized_reason = ChatFeedbackContentService.normalize_reason(reason)

        if rating == 1:
            normalized_reason = None

        assistant_meta = getattr(assistant, "metadata", None) or {}
        context_metadata = ChatFeedbackContextService.snapshot_from_assistant_metadata(
            assistant_meta if isinstance(assistant_meta, dict) else None,
            session_id=session_id,
            agent_id=str(session.agent_id) if session.agent_id else None,
        )
        sanitized_comment = ChatFeedbackContextService.sanitize_comment(comment)

        result = self.feedback_repository.upsert_feedback(
            message_id=message_uuid,
            user_id=user_uuid,
            rating=rating,
            reason=normalized_reason,
            comment=sanitized_comment,
            context_metadata=context_metadata,
        )

        if rating == -1:
            from app.application.services.chat_active_pending_service import (
                ChatActivePendingService,
            )

            if ChatActivePendingService.should_attach_routing_snapshot(
                normalized_reason,
            ):
                snapshot = ChatActivePendingService.routing_snapshot_from_assistant_metadata(
                    assistant_meta if isinstance(assistant_meta, dict) else None,
                )

                if snapshot:
                    result["routingSnapshot"] = snapshot

            corrective = ChatFeedbackContentService.corrective_actions_for_reason(
                normalized_reason,
            )

            if corrective:
                result["correctiveActions"] = corrective

        if rating == 1:
            self._capture_fine_tuning_sample(
                message_uuid=message_uuid,
                feedback_id=result.get("id"),
                context_metadata=context_metadata,
                user_id=user_id,
            )

            thanks = ChatFeedbackContentService.thanks_for_rating(
                rating,
                seed=message_id,
            )

            if thanks:
                result["thanksMessage"] = thanks

        result["auditMetadata"] = ChatFeedbackAdminMetricsService.feedback_audit_metadata(
            message_id=message_id,
            session_id=session_id,
            rating=rating,
            reason=normalized_reason,
            comment=sanitized_comment,
            context=context_metadata,
        )

        if rating == -1:
            self._capture_learning_candidate(
                message_uuid=message_uuid,
                reason=normalized_reason,
                session=session,
                user_id=user_id,
            )
            self._capture_evaluation_case(
                message_uuid=message_uuid,
                reason=normalized_reason,
                feedback_id=result.get("id"),
                user_id=user_id,
            )

        return result

    def _capture_learning_candidate(
        self,
        *,
        message_uuid: UUID,
        reason: str | None,
        session,
        user_id: str,
    ) -> None:
        """Aprendizagem contínua (playbook §16): best-effort, nunca quebra o feedback."""
        from app.infrastructure.config.settings import Settings

        if not Settings.CHAT_LEARNING_ENABLED or not Settings.CHAT_LEARNING_CAPTURE_FROM_FEEDBACK:
            return

        try:
            user_question = self.feedback_repository.get_user_question_for_assistant(
                message_uuid,
            )

            if not user_question:
                return

            from app.application.services.chat_learning_capture_service import (
                ChatLearningCaptureService,
            )

            project_id = None
            session_project = getattr(session, "project_id", None)

            if session_project:
                project_id = str(session_project)

            ChatLearningCaptureService().capture_from_negative_feedback(
                user_question=user_question,
                reason=reason,
                project_id=project_id,
                created_by=user_id,
            )
        except Exception:
            return

    def _capture_evaluation_case(
        self,
        *,
        message_uuid: UUID,
        reason: str | None,
        feedback_id: int | None,
        user_id: str,
    ) -> None:
        """Casos de regressão (Fase 6): best-effort, nunca quebra o feedback."""
        from app.infrastructure.config.settings import Settings

        if not Settings.CHAT_LEARNING_ENABLED:
            return

        try:
            user_question = self.feedback_repository.get_user_question_for_assistant(
                message_uuid,
            )

            if not user_question:
                return

            from app.application.services.chat_evaluation_case_service import (
                ChatEvaluationCaseService,
            )

            ChatEvaluationCaseService().capture_from_negative_feedback(
                user_question=user_question,
                reason=reason,
                feedback_id=feedback_id,
                created_by=user_id,
            )
        except Exception:
            return

    def _capture_fine_tuning_sample(
        self,
        *,
        message_uuid: UUID,
        feedback_id: int | None,
        context_metadata: dict | None,
        user_id: str,
    ) -> None:
        """Fine-tuning offline (Fase 7): best-effort em feedback positivo."""
        from app.infrastructure.config.settings import Settings

        if not Settings.CHAT_LEARNING_ENABLED:
            return

        try:
            from app.application.services.chat_fine_tuning_service import ChatFineTuningService

            ChatFineTuningService().capture_from_positive_feedback(
                message_id=message_uuid,
                feedback_id=feedback_id,
                context_metadata=context_metadata,
                created_by=user_id,
            )
        except Exception:
            return

from datetime import datetime, timezone
from uuid import UUID

from app.infrastructure.db.models.chat_message_feedback_model import (
    AiChatMessageFeedbackModel,
)
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.extensions.db import db


class PostgresChatMessageFeedbackRepository:
    def upsert_feedback(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
        rating: int,
        reason: str | None = None,
        comment: str | None = None,
        context_metadata: dict | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        row = (
            AiChatMessageFeedbackModel.query.filter_by(
                message_id=message_id,
                user_id=user_id,
            ).first()
        )

        if row:
            row.rating = rating
            row.reason = reason
            row.comment = comment
            row.context_metadata = context_metadata
            row.updated_at = now
        else:
            row = AiChatMessageFeedbackModel(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                reason=reason,
                comment=comment,
                context_metadata=context_metadata,
                created_at=now,
                updated_at=now,
            )
            db.session.add(row)

        db.session.flush()

        return self._to_dict(row)

    def delete_feedback(self, *, message_id: UUID, user_id: UUID) -> bool:
        row = (
            AiChatMessageFeedbackModel.query.filter_by(
                message_id=message_id,
                user_id=user_id,
            ).first()
        )

        if not row:
            return False

        db.session.delete(row)
        db.session.flush()
        return True

    def get_feedback_for_user(
        self,
        *,
        message_id: UUID,
        user_id: UUID,
    ) -> dict | None:
        row = (
            AiChatMessageFeedbackModel.query.filter_by(
                message_id=message_id,
                user_id=user_id,
            ).first()
        )

        if not row:
            return None

        return self._to_dict(row)

    def list_feedback_by_message_ids(
        self,
        *,
        message_ids: list[UUID],
        user_id: UUID,
    ) -> dict[str, dict]:
        if not message_ids:
            return {}

        rows = (
            AiChatMessageFeedbackModel.query.filter(
                AiChatMessageFeedbackModel.message_id.in_(message_ids),
                AiChatMessageFeedbackModel.user_id == user_id,
            ).all()
        )

        return {str(row.message_id): self._to_dict(row) for row in rows}

    def get_assistant_message(self, message_id: UUID) -> AiChatMessageModel | None:
        return (
            AiChatMessageModel.query.filter(
                AiChatMessageModel.id == message_id,
                AiChatMessageModel.role == "assistant",
            ).first()
        )

    def get_user_question_for_assistant(self, message_id: UUID) -> str | None:
        assistant = AiChatMessageModel.query.filter_by(id=message_id).first()

        if not assistant or not assistant.parent_message_id:
            return None

        parent = AiChatMessageModel.query.filter(
            AiChatMessageModel.id == assistant.parent_message_id,
            AiChatMessageModel.role == "user",
        ).first()

        if not parent or not parent.content:
            return None

        return str(parent.content)

    def get_message_session_id(self, message_id: UUID) -> UUID | None:
        row = AiChatMessageModel.query.filter_by(id=message_id).first()

        if not row:
            return None

        return row.session_id

    def list_feedback_since(self, *, since: datetime) -> list[dict]:
        rows = (
            AiChatMessageFeedbackModel.query.filter(
                AiChatMessageFeedbackModel.created_at >= since,
            )
            .order_by(AiChatMessageFeedbackModel.created_at.desc())
            .limit(5000)
            .all()
        )

        return [self._to_dict(row) for row in rows]

    def _to_dict(self, row: AiChatMessageFeedbackModel) -> dict:
        payload = {
            "id": int(row.id),
            "messageId": str(row.message_id),
            "userId": str(row.user_id),
            "rating": int(row.rating),
            "createdAt": row.created_at.isoformat(),
            "updatedAt": row.updated_at.isoformat(),
        }

        if row.reason:
            payload["reason"] = str(row.reason)

        if row.comment:
            payload["comment"] = str(row.comment)

        if isinstance(row.context_metadata, dict):
            payload["contextMetadata"] = dict(row.context_metadata)

        return payload

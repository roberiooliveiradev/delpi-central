from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_

from app.domain.ports.response_evaluation_repository_port import (
    ResponseEvaluationQuery,
    ResponseEvaluationRepositoryPort,
)
from app.extensions.db import db
from app.infrastructure.db.models.chat_message_model import AiChatMessageModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel
from app.infrastructure.db.models.response_evaluation_model import AiResponseEvaluationModel


class PostgresResponseEvaluationRepository(ResponseEvaluationRepositoryPort):
    def upsert_evaluation(
        self,
        *,
        message_id: UUID,
        session_id: UUID,
        evaluator_user_id: UUID,
        score: int,
        verdict: str,
        comment: str | None,
        suggestions: dict | None,
        metadata: dict | None,
    ) -> dict:
        model = AiResponseEvaluationModel.query.filter(
            AiResponseEvaluationModel.message_id == message_id,
        ).first()

        now = datetime.now(timezone.utc)

        if model:
            model.evaluator_user_id = evaluator_user_id
            model.score = score
            model.verdict = verdict
            model.comment = comment
            model.suggestions = suggestions
            model.evaluation_metadata = metadata
            model.updated_at = now
        else:
            model = AiResponseEvaluationModel(
                message_id=message_id,
                session_id=session_id,
                evaluator_user_id=evaluator_user_id,
                score=score,
                verdict=verdict,
                comment=comment,
                suggestions=suggestions,
                evaluation_metadata=metadata,
                created_at=now,
                updated_at=now,
            )
            db.session.add(model)

        db.session.flush()

        return self._serialize_evaluation(model)

    def get_evaluation_by_message_id(self, message_id: UUID) -> dict | None:
        model = AiResponseEvaluationModel.query.filter(
            AiResponseEvaluationModel.message_id == message_id,
        ).first()

        if not model:
            return None

        return self._serialize_evaluation(model)

    def list_evaluations(
        self,
        query: ResponseEvaluationQuery,
    ) -> tuple[list[dict], int]:
        base_query = AiResponseEvaluationModel.query.join(
            AiChatMessageModel,
            AiChatMessageModel.id == AiResponseEvaluationModel.message_id,
        )

        base_query = self._apply_evaluation_filters(base_query, query)
        total = base_query.count()

        models = (
            base_query.order_by(AiResponseEvaluationModel.created_at.desc())
            .offset(query.offset)
            .limit(query.limit)
            .all()
        )

        items = []

        for model in models:
            message = AiChatMessageModel.query.filter(
                AiChatMessageModel.id == model.message_id,
            ).first()
            items.append(self._serialize_evaluation(model, message=message))

        return items, total

    def get_summary(self) -> dict:
        total = AiResponseEvaluationModel.query.count()

        if total == 0:
            return {
                "total": 0,
                "averageScore": None,
                "helpfulRate": None,
                "distribution": [],
                "recent24h": 0,
            }

        rows = db.session.query(
            AiResponseEvaluationModel.verdict,
            db.func.count(AiResponseEvaluationModel.id),
        ).group_by(AiResponseEvaluationModel.verdict)

        distribution = []
        helpful_count = 0

        for verdict, count in rows:
            count_value = int(count or 0)
            distribution.append({"verdict": verdict, "count": count_value})

            if verdict == "helpful":
                helpful_count += count_value

        average_score = db.session.query(
            db.func.avg(AiResponseEvaluationModel.score),
        ).scalar()

        since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_24h = (
            AiResponseEvaluationModel.query.filter(
                AiResponseEvaluationModel.created_at >= since,
            ).count()
        )

        return {
            "total": total,
            "averageScore": round(float(average_score), 2) if average_score is not None else None,
            "helpfulRate": round(helpful_count / total, 4) if total else None,
            "distribution": distribution,
            "recent24h": recent_24h,
        }

    def list_assistant_message_candidates(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> tuple[list[dict], int]:
        base_query = (
            db.session.query(AiChatMessageModel, AiResponseEvaluationModel)
            .join(
                AiChatSessionModel,
                AiChatSessionModel.id == AiChatMessageModel.session_id,
            )
            .outerjoin(
                AiResponseEvaluationModel,
                AiResponseEvaluationModel.message_id == AiChatMessageModel.id,
            )
            .filter(AiChatMessageModel.role == "assistant")
        )

        normalized_search = str(search or "").strip()

        if normalized_search:
            pattern = f"%{normalized_search}%"
            base_query = base_query.filter(
                or_(
                    AiChatMessageModel.content.ilike(pattern),
                    AiChatSessionModel.title.ilike(pattern),
                )
            )

        total = base_query.count()

        rows = (
            base_query.order_by(AiChatMessageModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []

        for message_model, evaluation_model in rows:
            items.append(
                self._serialize_candidate(message_model, evaluation_model),
            )

        return items, total

    def get_assistant_message_context(self, message_id: UUID) -> dict | None:
        message = AiChatMessageModel.query.filter(
            AiChatMessageModel.id == message_id,
            AiChatMessageModel.role == "assistant",
        ).first()

        if not message:
            return None

        session = AiChatSessionModel.query.filter(
            AiChatSessionModel.id == message.session_id,
        ).first()

        previous_user_message = (
            AiChatMessageModel.query.filter(
                AiChatMessageModel.session_id == message.session_id,
                AiChatMessageModel.role == "user",
                AiChatMessageModel.created_at < message.created_at,
            )
            .order_by(AiChatMessageModel.created_at.desc())
            .first()
        )

        evaluation = AiResponseEvaluationModel.query.filter(
            AiResponseEvaluationModel.message_id == message.id,
        ).first()

        return {
            "message": self._serialize_message(message),
            "session": {
                "id": str(session.id) if session else None,
                "title": session.title if session else None,
                "agentId": str(session.agent_id) if session and session.agent_id else None,
            },
            "userQuestion": previous_user_message.content if previous_user_message else None,
            "evaluation": self._serialize_evaluation(evaluation) if evaluation else None,
        }

    def _apply_evaluation_filters(self, query, evaluation_query: ResponseEvaluationQuery):
        if evaluation_query.verdict:
            query = query.filter(
                AiResponseEvaluationModel.verdict == evaluation_query.verdict,
            )

        if evaluation_query.min_score is not None:
            query = query.filter(
                AiResponseEvaluationModel.score >= evaluation_query.min_score,
            )

        if evaluation_query.max_score is not None:
            query = query.filter(
                AiResponseEvaluationModel.score <= evaluation_query.max_score,
            )

        normalized_search = str(evaluation_query.search or "").strip()

        if normalized_search:
            pattern = f"%{normalized_search}%"
            query = query.filter(
                or_(
                    AiChatMessageModel.content.ilike(pattern),
                    AiResponseEvaluationModel.comment.ilike(pattern),
                )
            )

        return query

    def _serialize_message(self, model: AiChatMessageModel) -> dict:
        metadata = model.message_metadata or {}

        return {
            "id": str(model.id),
            "sessionId": str(model.session_id),
            "role": model.role,
            "content": model.content,
            "metadata": metadata,
            "createdAt": model.created_at.isoformat(),
            "sourceCount": len(metadata.get("sources") or []),
            "guidelineCount": len(metadata.get("adminGuidelines") or []),
            "toolCallCount": len(metadata.get("toolCalls") or []),
        }

    def _serialize_evaluation(
        self,
        model: AiResponseEvaluationModel,
        *,
        message: AiChatMessageModel | None = None,
    ) -> dict:
        payload = {
            "id": model.id,
            "messageId": str(model.message_id),
            "sessionId": str(model.session_id),
            "evaluatorUserId": str(model.evaluator_user_id),
            "score": model.score,
            "verdict": model.verdict,
            "comment": model.comment,
            "suggestions": model.suggestions or {},
            "metadata": model.evaluation_metadata or {},
            "createdAt": model.created_at.isoformat(),
            "updatedAt": model.updated_at.isoformat(),
        }

        if message is not None:
            payload["messagePreview"] = message.content[:500]
            payload["messageCreatedAt"] = message.created_at.isoformat()

        return payload

    def _serialize_candidate(
        self,
        message: AiChatMessageModel,
        evaluation: AiResponseEvaluationModel | None,
    ) -> dict:
        metadata = message.message_metadata or {}

        return {
            "messageId": str(message.id),
            "sessionId": str(message.session_id),
            "contentPreview": message.content[:500],
            "createdAt": message.created_at.isoformat(),
            "sourceCount": len(metadata.get("sources") or []),
            "guidelineCount": len(metadata.get("adminGuidelines") or []),
            "evaluation": self._serialize_evaluation(evaluation) if evaluation else None,
        }

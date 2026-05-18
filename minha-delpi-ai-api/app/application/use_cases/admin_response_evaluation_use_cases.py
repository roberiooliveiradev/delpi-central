from uuid import UUID

from app.application.services.response_evaluation_suggestion_service import (
    ResponseEvaluationSuggestionService,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.response_evaluation_repository_port import (
    ResponseEvaluationQuery,
    ResponseEvaluationRepositoryPort,
)


class ListAdminResponseCandidatesUseCase:
    def __init__(self, repository: ResponseEvaluationRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> dict:
        safe_limit = max(1, min(int(limit), 50))
        safe_offset = max(0, int(offset))

        items, total = self.repository.list_assistant_message_candidates(
            limit=safe_limit,
            offset=safe_offset,
            search=search,
        )

        return {
            "items": items,
            "pagination": {
                "limit": safe_limit,
                "offset": safe_offset,
                "total": total,
                "hasNext": safe_offset + safe_limit < total,
                "hasPrevious": safe_offset > 0,
            },
        }


class GetAdminResponseEvaluationContextUseCase:
    def __init__(
        self,
        repository: ResponseEvaluationRepositoryPort,
        suggestion_service: ResponseEvaluationSuggestionService | None = None,
    ):
        self.repository = repository
        self.suggestion_service = suggestion_service or ResponseEvaluationSuggestionService()

    def execute(self, *, message_id: str, score: int | None = None) -> dict:
        context = self.repository.get_assistant_message_context(UUID(str(message_id)))

        if not context:
            raise ValueError("assistant message not found")

        effective_score = score if score is not None else (
            context.get("evaluation") or {}
        ).get("score", 3)

        verdict = self.suggestion_service.score_to_verdict(int(effective_score))
        suggestions = self.suggestion_service.build_suggestions(
            score=int(effective_score),
            verdict=verdict,
            message_metadata=context.get("message", {}).get("metadata"),
            user_question=context.get("userQuestion"),
            assistant_answer=context.get("message", {}).get("content", ""),
        )

        return {
            **context,
            "suggestedScore": int(effective_score),
            "suggestedVerdict": verdict,
            "suggestions": suggestions,
        }


class SaveAdminResponseEvaluationUseCase:
    def __init__(
        self,
        repository: ResponseEvaluationRepositoryPort,
        audit_repository: AuditRepositoryPort | None = None,
        suggestion_service: ResponseEvaluationSuggestionService | None = None,
    ):
        self.repository = repository
        self.audit_repository = audit_repository
        self.suggestion_service = suggestion_service or ResponseEvaluationSuggestionService()

    def execute(
        self,
        *,
        message_id: str,
        evaluator_user_id: str,
        score: int,
        comment: str | None = None,
    ) -> dict:
        safe_score = max(1, min(int(score), 5))
        verdict = self.suggestion_service.score_to_verdict(safe_score)

        context = self.repository.get_assistant_message_context(UUID(str(message_id)))

        if not context:
            raise ValueError("assistant message not found")

        message = context["message"]
        suggestions = self.suggestion_service.build_suggestions(
            score=safe_score,
            verdict=verdict,
            message_metadata=message.get("metadata"),
            user_question=context.get("userQuestion"),
            assistant_answer=message.get("content", ""),
        )

        evaluation_metadata = {
            "userQuestionPreview": (context.get("userQuestion") or "")[:500],
            "sourceCount": message.get("sourceCount", 0),
            "guidelineCount": message.get("guidelineCount", 0),
            "toolCallCount": message.get("toolCallCount", 0),
        }

        saved = self.repository.upsert_evaluation(
            message_id=UUID(str(message_id)),
            session_id=UUID(str(message["sessionId"])),
            evaluator_user_id=UUID(str(evaluator_user_id)),
            score=safe_score,
            verdict=verdict,
            comment=(comment or "").strip() or None,
            suggestions=suggestions,
            metadata=evaluation_metadata,
        )

        if self.audit_repository:
            self.audit_repository.log(
                user_id=UUID(str(evaluator_user_id)),
                action="admin.response.evaluated",
                context="admin",
                metadata={
                    "message_id": str(message_id),
                    "session_id": message.get("sessionId"),
                    "score": safe_score,
                    "verdict": verdict,
                    "document_suggestions": len(suggestions.get("documents") or []),
                    "guideline_suggestions": len(suggestions.get("guidelines") or []),
                },
            )

        return saved


class ListAdminResponseEvaluationsUseCase:
    def __init__(self, repository: ResponseEvaluationRepositoryPort):
        self.repository = repository

    def execute(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        verdict: str | None = None,
        min_score: int | None = None,
        max_score: int | None = None,
        search: str | None = None,
    ) -> dict:
        safe_limit = max(1, min(int(limit), 100))
        safe_offset = max(0, int(offset))

        items, total = self.repository.list_evaluations(
            ResponseEvaluationQuery(
                limit=safe_limit,
                offset=safe_offset,
                verdict=verdict,
                min_score=min_score,
                max_score=max_score,
                search=search,
            )
        )

        return {
            "items": items,
            "pagination": {
                "limit": safe_limit,
                "offset": safe_offset,
                "total": total,
                "hasNext": safe_offset + safe_limit < total,
                "hasPrevious": safe_offset > 0,
            },
        }


class GetAdminResponseEvaluationSummaryUseCase:
    def __init__(self, repository: ResponseEvaluationRepositoryPort):
        self.repository = repository

    def execute(self) -> dict:
        return self.repository.get_summary()

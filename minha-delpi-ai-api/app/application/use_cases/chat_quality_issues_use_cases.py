from app.domain.ports.chat_quality_issue_repository_port import ChatQualityIssueRepositoryPort
from app.domain.services.chat_feedback_issue_service import ChatFeedbackIssueService


def _default_issue_repository() -> ChatQualityIssueRepositoryPort:
    from app.composition.repository_composer import make_chat_quality_issue_repository

    return make_chat_quality_issue_repository()


class EvaluateFeedbackIssuesUseCase:
    def __init__(
        self,
        issue_repository: ChatQualityIssueRepositoryPort | None = None,
    ):
        self.issue_repository = issue_repository or _default_issue_repository()

    def execute(
        self,
        *,
        alerts: list[dict] | None,
        feedback_summary: dict | None = None,
    ) -> list[dict]:
        _ = self.issue_repository

        return ChatFeedbackIssueService.evaluate_alerts(
            alerts,
            source="feedback_auto",
            feedback_summary=feedback_summary,
        )


class ListAdminQualityIssuesUseCase:
    def __init__(
        self,
        issue_repository: ChatQualityIssueRepositoryPort | None = None,
    ):
        self.issue_repository = issue_repository or _default_issue_repository()

    def execute(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        items, total = self.issue_repository.list_issues(
            status=status,
            limit=limit,
            offset=offset,
        )

        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "hasNext": offset + limit < total,
                "hasPrevious": offset > 0,
            },
        }


class UpdateAdminQualityIssueStatusUseCase:
    def __init__(
        self,
        issue_repository: ChatQualityIssueRepositoryPort | None = None,
    ):
        self.issue_repository = issue_repository or _default_issue_repository()

    def execute(self, *, issue_id: int, status: str) -> dict:
        allowed = {"open", "in_progress", "resolved", "dismissed"}
        normalized = str(status or "").strip()

        if normalized not in allowed:
            raise ValueError("invalid issue status")

        updated = self.issue_repository.update_status(issue_id, status=normalized)

        if not updated:
            raise ValueError("issue not found")

        return updated

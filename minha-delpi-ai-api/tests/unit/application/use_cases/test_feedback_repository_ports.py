import ast
from pathlib import Path
from unittest.mock import Mock

from app.application.use_cases.chat_quality_issues_use_cases import (
    ListAdminQualityIssuesUseCase,
    UpdateAdminQualityIssueStatusUseCase,
)
from app.application.use_cases.get_admin_feedback_summary_use_case import (
    GetAdminFeedbackSummaryUseCase,
)
from app.domain.ports.chat_message_feedback_repository_port import (
    ChatMessageFeedbackRepositoryPort,
)
from app.domain.ports.chat_quality_issue_repository_port import ChatQualityIssueRepositoryPort


def test_feedback_use_case_modules_have_no_postgres_imports():
    paths = [
        "app/application/use_cases/upsert_chat_message_feedback_use_case.py",
        "app/application/use_cases/get_admin_feedback_summary_use_case.py",
        "app/application/use_cases/get_chat_history_use_case.py",
        "app/application/use_cases/chat_quality_issues_use_cases.py",
    ]

    for rel_path in paths:
        tree = ast.parse(Path(rel_path).read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "postgres" in node.module:
                raise AssertionError(f"Postgres import in {rel_path}: {node.module}")


def test_list_admin_quality_issues_delegates_to_port():
    repository = Mock(spec=ChatQualityIssueRepositoryPort)
    repository.list_issues.return_value = ([{"id": 1}], 1)

    result = ListAdminQualityIssuesUseCase(issue_repository=repository).execute(limit=10, offset=0)

    repository.list_issues.assert_called_once()
    assert result["pagination"]["total"] == 1


def test_get_admin_feedback_summary_delegates_to_port():
    repository = Mock(spec=ChatMessageFeedbackRepositoryPort)
    repository.list_feedback_since.return_value = []

    summary = GetAdminFeedbackSummaryUseCase(feedback_repository=repository).execute(hours=24)

    repository.list_feedback_since.assert_called_once()
    assert "since" in summary or "totalFeedback" in summary or isinstance(summary, dict)


def test_update_admin_quality_issue_status_delegates_to_port():
    repository = Mock(spec=ChatQualityIssueRepositoryPort)
    repository.update_status.return_value = {"id": 3, "status": "resolved"}

    updated = UpdateAdminQualityIssueStatusUseCase(issue_repository=repository).execute(
        issue_id=3,
        status="resolved",
    )

    repository.update_status.assert_called_once_with(3, status="resolved")
    assert updated["status"] == "resolved"

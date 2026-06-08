import ast
from pathlib import Path


def _class_bases(module_path: str, class_name: str) -> list[str]:
    tree = ast.parse(Path(module_path).read_text())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            bases: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            return bases
    raise AssertionError(f"{class_name} not found in {module_path}")


def test_postgres_external_action_repository_declares_port():
    bases = _class_bases(
        "app/infrastructure/persistence/postgres_external_action_repository.py",
        "PostgresExternalActionRepository",
    )
    assert "ExternalActionRepositoryPort" in bases


def test_postgres_chat_skill_repository_declares_port():
    bases = _class_bases(
        "app/infrastructure/persistence/postgres_chat_skill_repository.py",
        "PostgresChatSkillRepository",
    )
    assert "ChatSkillRepositoryPort" in bases


def test_postgres_chat_quality_report_repository_declares_port():
    bases = _class_bases(
        "app/infrastructure/persistence/postgres_chat_quality_report_repository.py",
        "PostgresChatQualityReportRepository",
    )
    assert "ChatQualityReportRepositoryPort" in bases


def test_postgres_chat_message_feedback_repository_declares_port():
    bases = _class_bases(
        "app/infrastructure/persistence/postgres_chat_message_feedback_repository.py",
        "PostgresChatMessageFeedbackRepository",
    )
    assert "ChatMessageFeedbackRepositoryPort" in bases


def test_postgres_chat_quality_issue_repository_declares_port():
    bases = _class_bases(
        "app/infrastructure/persistence/postgres_chat_quality_issue_repository.py",
        "PostgresChatQualityIssueRepository",
    )
    assert "ChatQualityIssueRepositoryPort" in bases

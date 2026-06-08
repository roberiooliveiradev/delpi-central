import ast
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from app.application.use_cases.admin_chat_skill_use_cases import (
    CreateAdminChatSkillUseCase,
    DeactivateAdminChatSkillUseCase,
    UpdateAdminChatSkillUseCase,
)
from app.domain.ports.chat_skill_repository_port import ChatSkillRepositoryPort


def test_admin_chat_skill_use_cases_module_has_no_postgres_imports():
    tree = ast.parse(Path("app/application/use_cases/admin_chat_skill_use_cases.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "postgres" in node.module:
            raise AssertionError(f"Postgres import found: {node.module}")


def test_create_admin_chat_skill_delegates_to_port():
    repository = Mock(spec=ChatSkillRepositoryPort)
    repository.create.return_value = {"skillKey": "company-knowledge", "id": str(uuid4())}

    result = CreateAdminChatSkillUseCase(repository=repository).execute(
        {"skillKey": "company-knowledge", "label": "Company"}
    )

    repository.create.assert_called_once()
    assert result["skillKey"] == "company-knowledge"


def test_update_admin_chat_skill_delegates_to_port():
    skill_id = str(uuid4())
    repository = Mock(spec=ChatSkillRepositoryPort)
    repository.update.return_value = {"id": skill_id, "label": "Updated"}

    result = UpdateAdminChatSkillUseCase(repository=repository).execute(
        skill_id,
        {"label": "Updated"},
    )

    repository.update.assert_called_once()
    assert result["label"] == "Updated"


def test_deactivate_admin_chat_skill_delegates_to_port():
    skill_id = str(uuid4())
    repository = Mock(spec=ChatSkillRepositoryPort)
    repository.deactivate.return_value = True

    deleted = DeactivateAdminChatSkillUseCase(repository=repository).execute(skill_id)

    repository.deactivate.assert_called_once()
    assert deleted is True

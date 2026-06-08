import ast
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from app.application.use_cases.admin_agent_specialization_use_cases import (
    GetAdminAgentSpecializationUseCase,
    ListAdminSpecializedAgentsUseCase,
    SaveAdminAgentSpecializationUseCase,
)
from app.domain.entities.chat_agent import ChatAgent
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort

_AGENT_ADMIN_MODULES = [
    "app/application/use_cases/admin_agent_specialization_use_cases.py",
    "app/application/use_cases/admin_agent_simulate_use_case.py",
]


def _agent(*, metadata: dict | None = None) -> ChatAgent:
    now = datetime.now(timezone.utc)
    return ChatAgent(
        id=uuid4(),
        name="Agente teste",
        description="desc",
        system_prompt="prompt",
        enabled=True,
        metadata=metadata,
        created_at=now,
        updated_at=now,
        category="ops",
        visibility="system",
    )


def test_admin_agent_modules_have_no_postgres_or_sqlalchemy_imports():
    for rel_path in _AGENT_ADMIN_MODULES:
        tree = ast.parse(Path(rel_path).read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "postgres" not in node.module
                assert "sqlalchemy" not in node.module
                assert "infrastructure.db.models" not in node.module


def test_list_admin_specialized_agents_delegates_to_port():
    repository = Mock(spec=ChatAgentRepositoryPort)
    repository.list_enabled_ordered.return_value = [
        _agent(metadata={"specialization": {"domain": "ops", "presetKey": "ops"}})
    ]

    payload = ListAdminSpecializedAgentsUseCase(repository).execute()

    repository.list_enabled_ordered.assert_called_once_with()
    assert payload["items"][0]["hasSpecialization"] is True


def test_get_admin_agent_specialization_delegates_to_port():
    agent = _agent(metadata={"specialization": {"domain": "ops"}})
    repository = Mock(spec=ChatAgentRepositoryPort)
    repository.get_by_id.return_value = agent

    payload = GetAdminAgentSpecializationUseCase(repository).execute(agent_id=str(agent.id))

    repository.get_by_id.assert_called_once_with(agent.id)
    assert payload["agentId"] == str(agent.id)
    assert payload["enabled"] is True


def test_save_admin_agent_specialization_updates_metadata_and_audits():
    agent = _agent(metadata={})
    updated = _agent(
        metadata={"specialization": {"domain": "ops", "presetKey": "ops", "enabled": True}},
    )
    updated = ChatAgent(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        system_prompt=agent.system_prompt,
        enabled=agent.enabled,
        metadata={"specialization": {"domain": "ops", "presetKey": "ops", "enabled": True}},
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        category=agent.category,
        visibility=agent.visibility,
    )

    repository = Mock(spec=ChatAgentRepositoryPort)
    repository.get_by_id.return_value = agent
    repository.update_metadata.return_value = updated
    audit_repository = Mock(spec=AuditRepositoryPort)

    payload = SaveAdminAgentSpecializationUseCase(
        repository,
        audit_repository=audit_repository,
    ).execute(
        agent_id=str(agent.id),
        specialization_payload={"enabled": True, "domain": "ops", "presetKey": "ops"},
        user_id=str(uuid4()),
    )

    repository.update_metadata.assert_called_once()
    audit_repository.log.assert_called_once()
    assert payload["enabled"] is True

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.chat_sources_use_cases import CreateAgentSourceUseCase
from app.domain.entities.chat_agent import ChatAgent
from app.domain.entities.knowledge_document import KnowledgeDocument


def _agent():
    return ChatAgent(
        id=uuid4(),
        key="produtos",
        name="Produtos",
        description=None,
        system_prompt="prompt",
        enabled=True,
        metadata={},
        created_at=None,
        updated_at=None,
        owner_user_id=uuid4(),
        visibility="private",
        category=None,
        icon=None,
        response_style=None,
        max_tool_calls=5,
        requires_confirmation_for_write=False,
    )


def _document(title: str = "manual.md"):
    return KnowledgeDocument(
        id=uuid4(),
        title=title,
        source_type="agent_source",
        source_ref="ref",
        content="conteudo",
        metadata={
            "scope": "agent_source",
            "agentKey": "produtos",
            "contentHash": "abc123",
        },
        active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_execute_file_returns_duplicate_without_reingesting():
    agent = _agent()
    existing = _document()

    agent_repository = MagicMock()
    agent_repository.get_accessible_by_id.return_value = (agent, "owner")

    knowledge_repository = MagicMock()
    knowledge_repository.list_documents_by_metadata.return_value = [(existing, 3)]

    pipeline = MagicMock()
    pipeline.prepare.return_value = MagicMock(content_hash="abc123", chunks=[MagicMock()])

    file_storage = MagicMock()
    file_storage.save.return_value = {
        "storagePath": "/tmp/test-file.md",
        "sizeBytes": 12,
    }

    text_extractor = MagicMock()
    text_extractor.extract.return_value = {
        "supported": True,
        "content": "conteudo extraido",
        "metadata": {},
    }

    ingest_use_case = MagicMock()

    use_case = CreateAgentSourceUseCase(
        agent_repository=agent_repository,
        knowledge_repository=knowledge_repository,
        ingest_use_case=ingest_use_case,
        text_extractor=text_extractor,
        file_storage=file_storage,
        pipeline=pipeline,
    )

    result = use_case.execute_file(
        user_id=str(uuid4()),
        agent_id=str(agent.id),
        original_filename="manual.md",
        content_type="text/markdown",
        content=b"# titulo",
    )

    assert result.duplicate is True
    assert result.id == str(existing.id)
    ingest_use_case.execute.assert_not_called()

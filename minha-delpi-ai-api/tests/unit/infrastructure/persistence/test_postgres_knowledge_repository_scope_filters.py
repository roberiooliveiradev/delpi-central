from sqlalchemy.dialects import postgresql

from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


class FakeQuery:
    def __init__(self):
        self.filters = []

    def filter(self, *clauses):
        self.filters.extend(clauses)
        return self


def _render_clause(clause) -> str:
    return str(
        clause.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def _render_filters(query: FakeQuery) -> str:
    return "\n".join(_render_clause(item) for item in query.filters)


def test_scope_filters_include_global_session_project_agent_and_user_guards():
    repository = PostgresKnowledgeRepository()
    query = FakeQuery()

    result = repository._apply_scope_filters(
        query,
        {
            "include_global": True,
            "user_id": "user-1",
            "session_id": "session-1",
            "project_id": "project-1",
            "agent_key": "agent-1",
        },
    )

    assert result is query

    rendered = _render_filters(query)

    assert "userId" in rendered
    assert "user-1" in rendered

    assert "global" in rendered

    assert "session_source" in rendered
    assert "sessionId" in rendered
    assert "session-1" in rendered

    assert "project_source" in rendered
    assert "projectId" in rendered
    assert "project-1" in rendered

    assert "agent_source" in rendered
    assert "agentKey" in rendered
    assert "agent-1" in rendered


def test_scope_filters_for_agent_requires_agent_source_scope():
    repository = PostgresKnowledgeRepository()
    query = FakeQuery()

    result = repository._apply_scope_filters(
        query,
        {
            "include_global": False,
            "user_id": "user-1",
            "agent_key": "agent-1",
        },
    )

    assert result is query

    rendered = _render_filters(query)

    assert "userId" in rendered
    assert "user-1" in rendered
    assert "agentKey" in rendered
    assert "agent-1" in rendered
    assert "agent_source" in rendered

    assert "project_source" not in rendered
    assert "session_source" not in rendered
    assert "global" not in rendered


def test_scope_filters_for_project_requires_project_source_scope():
    repository = PostgresKnowledgeRepository()
    query = FakeQuery()

    result = repository._apply_scope_filters(
        query,
        {
            "include_global": False,
            "user_id": "user-1",
            "project_id": "project-1",
        },
    )

    assert result is query

    rendered = _render_filters(query)

    assert "userId" in rendered
    assert "user-1" in rendered
    assert "projectId" in rendered
    assert "project-1" in rendered
    assert "project_source" in rendered

    assert "agent_source" not in rendered
    assert "session_source" not in rendered
    assert "global" not in rendered


def test_scope_filters_for_session_requires_session_source_scope():
    repository = PostgresKnowledgeRepository()
    query = FakeQuery()

    result = repository._apply_scope_filters(
        query,
        {
            "include_global": False,
            "user_id": "user-1",
            "session_id": "session-1",
        },
    )

    assert result is query

    rendered = _render_filters(query)

    assert "userId" in rendered
    assert "user-1" in rendered
    assert "sessionId" in rendered
    assert "session-1" in rendered
    assert "session_source" in rendered

    assert "agent_source" not in rendered
    assert "project_source" not in rendered
    assert "global" not in rendered


def test_scope_filters_without_allowed_clauses_only_applies_user_guard():
    repository = PostgresKnowledgeRepository()
    query = FakeQuery()

    result = repository._apply_scope_filters(
        query,
        {
            "include_global": False,
            "user_id": "user-1",
        },
    )

    assert result is query
    assert len(query.filters) == 1

    rendered = _render_filters(query)

    assert "userId" in rendered
    assert "user-1" in rendered
    assert "session_source" not in rendered
    assert "project_source" not in rendered
    assert "agent_source" not in rendered
    assert "global" not in rendered


def test_scope_filters_include_attachment_ids_when_present():
    repository = PostgresKnowledgeRepository()
    query = FakeQuery()

    result = repository._apply_scope_filters(
        query,
        {
            "include_global": False,
            "user_id": "user-1",
            "session_id": "session-1",
            "attachment_ids": ["attachment-1", "attachment-2"],
        },
    )

    assert result is query

    rendered = _render_filters(query)

    assert "attachmentId" in rendered
    assert "attachment-1" in rendered
    assert "attachment-2" in rendered
    assert "session_source" in rendered
    assert "session-1" in rendered

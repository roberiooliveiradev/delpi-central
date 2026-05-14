from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)


class FakeQuery:
    def __init__(self):
        self.filters = []

    def filter(self, *clauses):
        self.filters.extend(clauses)
        return self


def test_scope_filters_include_project_agent_session_scopes(monkeypatch):
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
    assert len(query.filters) == 2

    rendered = " ".join(str(item) for item in query.filters)

    assert "session_source" in rendered
    assert "sessionId" in rendered
    assert "project_source" in rendered
    assert "projectId" in rendered
    assert "agent_source" in rendered
    assert "agentKey" in rendered
    assert "userId" in rendered


def test_scope_filters_without_allowed_clauses_only_applies_user_filter():
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
    assert "userId" in str(query.filters[0])

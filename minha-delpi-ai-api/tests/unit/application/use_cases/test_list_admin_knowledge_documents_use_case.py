from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.use_cases.list_admin_knowledge_documents_use_case import (
    ListAdminKnowledgeDocumentsUseCase,
)
from app.domain.entities.knowledge_document import KnowledgeDocument


class FakeKnowledgeRepository:
    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self._doc = KnowledgeDocument(
            id=uuid4(),
            title="Doc",
            source_type="text",
            source_ref=None,
            content="x",
            metadata={"scope": "global"},
            active=True,
            created_at=now,
            updated_at=now,
        )

    def list_documents_with_chunk_count(self, **kwargs):
        return [(self._doc, 2)]

    def count_documents(self, **kwargs):
        active = kwargs.get("active")
        if active is True:
            return 3
        if active is False:
            return 1
        return 4

    def get_global_curatorial_facets(self):
        return {
            "categories": [],
            "namespaces": [],
            "domains": [],
            "tags": [],
            "sourceTypes": ["text"],
        }

    def get_global_document_summary(self):
        return {
            "total": 4,
            "active": 3,
            "inactive": 1,
            "pendingIndex": 1,
        }


def test_list_admin_knowledge_documents_includes_summary():
    use_case = ListAdminKnowledgeDocumentsUseCase(FakeKnowledgeRepository())

    result = use_case.execute(limit=10, offset=0)

    assert result["summary"] == {
        "total": 4,
        "active": 3,
        "inactive": 1,
        "pendingIndex": 1,
    }
    assert result["pagination"]["total"] == 4

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.use_cases.update_admin_knowledge_document_metadata_use_case import (
    UpdateAdminKnowledgeDocumentMetadataUseCase,
)
from app.domain.entities.knowledge_document import KnowledgeDocument


def _document(**overrides):
    base = {
        "id": uuid4(),
        "title": "Manual",
        "source_type": "manual",
        "source_ref": "global:manual",
        "content": "conteudo",
        "metadata": {"scope": "global", "category": "legado"},
        "active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return KnowledgeDocument(**base)


def test_updates_document_metadata():
    document = _document()
    updated = _document(metadata={"scope": "global", "category": "novo", "tags": ["faq"]})
    repository = Mock()
    repository.get_document_by_id.return_value = document
    repository.update_document_metadata.return_value = updated

    use_case = UpdateAdminKnowledgeDocumentMetadataUseCase(repository)
    result = use_case.execute(
        document_id=str(document.id),
        category="novo",
        tags=["faq"],
        priority=3,
    )

    repository.update_document_metadata.assert_called_once()
    saved_metadata = repository.update_document_metadata.call_args.args[1]
    assert saved_metadata["category"] == "novo"
    assert saved_metadata["tags"] == ["faq"]
    assert saved_metadata["priority"] == 3
    assert result["category"] == "novo"
    assert result["tags"] == ["faq"]


def test_raises_when_document_not_found():
    repository = Mock()
    repository.get_document_by_id.return_value = None

    use_case = UpdateAdminKnowledgeDocumentMetadataUseCase(repository)

    with pytest.raises(ValueError, match="document not found"):
        use_case.execute(document_id=str(uuid4()), category="x")

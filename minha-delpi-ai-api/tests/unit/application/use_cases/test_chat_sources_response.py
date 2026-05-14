from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.application.use_cases.chat_sources_use_cases import _source_response


def test_source_response_exposes_indexing_metadata():
    now = datetime.now(timezone.utc)

    document = SimpleNamespace(
        id=uuid4(),
        title="Manual",
        source_type="project_source",
        source_ref="source-ref",
        active=True,
        created_at=now,
        updated_at=now,
        metadata={
            "scope": "project_source",
            "projectId": "project-1",
            "agentKey": "agent-1",
            "attachmentId": "attachment-1",
            "originalFilename": "manual.pdf",
            "contentType": "application/pdf",
            "extractor": {
                "extractor": "pypdf",
                "extension": ".pdf",
            },
        },
    )

    response = _source_response(document, chunk_count=3)

    assert response.scope == "project_source"
    assert response.project_id == "project-1"
    assert response.agent_key == "agent-1"
    assert response.attachment_id == "attachment-1"
    assert response.original_filename == "manual.pdf"
    assert response.content_type == "application/pdf"
    assert response.chunk_count == 3
    assert response.indexed is True
    assert response.extractor == {
        "extractor": "pypdf",
        "extension": ".pdf",
    }
    assert response.index_reason is None


def test_source_response_marks_not_indexed_when_chunk_count_is_zero():
    now = datetime.now(timezone.utc)

    document = SimpleNamespace(
        id=uuid4(),
        title="Arquivo vazio",
        source_type="agent_source",
        source_ref="source-ref",
        active=True,
        created_at=now,
        updated_at=now,
        metadata={
            "scope": "agent_source",
            "agentKey": "agent-1",
            "indexReason": "empty_extracted_content",
        },
    )

    response = _source_response(document, chunk_count=0)

    assert response.indexed is False
    assert response.index_reason == "empty_extracted_content"
    assert response.extractor is None

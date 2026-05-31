from app.application.services.chat_attachment_response_service import (
    ChatAttachmentResponseService,
)
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4


def test_to_response_includes_reading_status_and_preview():
    attachment = SimpleNamespace(
        id=uuid4(),
        session_id=uuid4(),
        message_id=None,
        project_id=None,
        agent_id=None,
        filename="file.csv",
        original_filename="dados.csv",
        content_type="text/csv",
        size_bytes=120,
        status="indexed",
        metadata={
            "indexed": True,
            "preview": {
                "kind": "spreadsheet",
                "columns": ["Produto", "Qtd"],
            },
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = ChatAttachmentResponseService.to_response(attachment)

    assert response.metadata is not None
    assert response.metadata["readingStatus"] == "Indexado"
    assert response.metadata["preview"]["columns"] == ["Produto", "Qtd"]

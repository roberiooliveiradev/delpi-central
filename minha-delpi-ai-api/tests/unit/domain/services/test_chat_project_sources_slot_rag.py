from app.domain.services.chat_project_sources_intent_service import (
    ChatProjectSourcesIntentService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


def test_slotted_content_question_builds_document_filter():
    inventory = [
        {
            "projectSourceId": "doc-1",
            "title": "1º TREINAMENTO — FEVEREIRO 2026.docx",
            "ordinal": 1,
        }
    ]
    previous_messages = [
        {
            "role": "assistant",
            "metadata": {
                "contextSnapshot": {
                    "lastProjectSourcesInventory": inventory,
                }
            },
        }
    ]

    chunk_filter = ChatProjectSourcesIntentService.build_content_chunk_filter(
        "resuma o conteúdo do primeiro arquivo",
        previous_messages=previous_messages,
    )

    assert chunk_filter is not None

    matching_chunk = {
        "documentId": "doc-1",
        "sourceType": "project_source",
        "metadata": {"scope": "project_source"},
    }
    other_chunk = {
        "documentId": "doc-2",
        "sourceType": "project_source",
        "metadata": {"scope": "project_source"},
    }

    assert chunk_filter(matching_chunk) is True
    assert chunk_filter(other_chunk) is False


def test_first_file_summary_is_not_pure_text_task_when_inventory_exists():
    previous_messages = [
        {
            "role": "assistant",
            "metadata": {
                "contextSnapshot": {
                    "lastProjectSourcesInventory": [
                        {
                            "projectSourceId": "doc-1",
                            "title": "TREINAMENTO.docx",
                            "ordinal": 1,
                        }
                    ],
                }
            },
        }
    ]

    assert not ChatTextTaskIntentService.is_pure_text_task(
        "resuma o conteúdo do primeiro arquivo",
        previous_messages=previous_messages,
    )

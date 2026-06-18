from app.domain.services.chat_project_source_slot_resolver_service import (
    ChatProjectSourceSlotResolverService,
)
from app.domain.services.chat_project_sources_inventory_service import (
    ChatProjectSourcesInventoryService,
)


def test_serialize_sources_preserves_order_and_ids():
    class Source:
        def __init__(self, source_id: str, title: str, *, chunks: int = 1):
            self.id = source_id
            self.title = title
            self.original_filename = title
            self.source_type = "project_source"
            self.content_type = "application/pdf"
            self.chunk_count = chunks
            self.indexed = True
            self.metadata = {"sizeBytes": 2048}

    serialized = ChatProjectSourcesInventoryService.serialize_sources(
        [
            Source("doc-1", "TREINAMENTO.docx"),
            Source("doc-2", "MANUAL.pdf"),
        ]
    )

    assert len(serialized) == 2
    assert serialized[0]["projectSourceId"] == "doc-1"
    assert serialized[0]["ordinal"] == 1
    assert serialized[1]["projectSourceId"] == "doc-2"


def test_read_inventory_from_previous_assistant_snapshot():
    inventory = [
        {
            "projectSourceId": "doc-1",
            "title": "TREINAMENTO.docx",
            "ordinal": 1,
            "indexed": True,
            "chunkCount": 4,
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

    assert ChatProjectSourcesInventoryService.read_from_previous_messages(
        previous_messages
    ) == inventory


def test_resolve_first_file_slot_from_inventory():
    inventory = [
        {
            "projectSourceId": "doc-1",
            "title": "1º TREINAMENTO — FEVEREIRO 2026.docx",
            "ordinal": 1,
        },
        {
            "projectSourceId": "doc-2",
            "title": "MANUAL.pdf",
            "ordinal": 2,
        },
    ]

    resolved = ChatProjectSourceSlotResolverService.resolve(
        "resuma o conteúdo do primeiro arquivo",
        inventory,
    )

    assert resolved is not None
    assert resolved["projectSourceId"] == "doc-1"


def test_looks_like_slot_reference_for_training_prompt():
    assert ChatProjectSourceSlotResolverService.looks_like_slot_reference(
        "resuma o conteúdo do primeiro arquivo"
    )

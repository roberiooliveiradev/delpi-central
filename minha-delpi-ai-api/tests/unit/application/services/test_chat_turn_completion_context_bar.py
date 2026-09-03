"""contextBar None não pode derrubar o turno (missing product após ROL)."""

from app.application.services.chat_turn.chat_turn_completion_metadata_service import (
    ChatTurnCompletionMetadataService,
)


def test_attach_turn_grounding_context_bar_tolerates_null_context_bar():
    metadata = {
        "interactivity": {"contextBar": None},
    }
    tool_context = {
        "turnGrounding": {
            "status": "grounded",
            "referringTo": {"label": "ROL financeiro"},
        }
    }

    ChatTurnCompletionMetadataService._attach_turn_grounding_context_bar(
        metadata,
        tool_context=tool_context,
        workspace_context=None,
    )

    assert metadata["interactivity"]["contextBar"]["summary"] == "ROL financeiro"

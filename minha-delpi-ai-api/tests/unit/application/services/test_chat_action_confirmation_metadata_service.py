"""Playbook 08 — metadata de confirmação para MFE."""

from app.application.services.chat_action_confirmation_metadata_service import (
    ChatActionConfirmationMetadataService,
)


def test_attach_action_confirmation_from_blocked_tool():
    metadata: dict = {}

    ChatActionConfirmationMetadataService.attach_to_assistant_metadata(
        metadata,
        tool_calls=[
            {
                "name": "execute_external_action",
                "arguments": {"actionId": "api_externa.delete_item"},
                "metadata": {
                    "blockReason": "confirmation_required",
                    "path": "/items/1",
                    "sensitivity": "destructive",
                },
            }
        ],
        user_message="exclua o item 1",
    )

    confirmation = metadata.get("actionConfirmation")

    assert confirmation is not None
    assert confirmation["actionId"] == "api_externa.delete_item"
    assert confirmation["confirmQuery"] == "confirmo. exclua o item 1"
    assert confirmation["confirmLabel"] == "Confirmar"

"""Playbook 08 — confirmação de escrita."""

from app.domain.services.chat_write_confirmation_service import (
    ChatWriteConfirmationService,
)


def test_blocks_destructive_without_confirm():
    action = {
        "method": "DELETE",
        "path": "/records/1",
        "sensitivity": "destructive",
        "summary": "Excluir registro",
    }

    assert ChatWriteConfirmationService.should_block_execution(
        message="exclua o registro 1",
        action=action,
    )


def test_allows_after_confirm():
    action = {
        "method": "DELETE",
        "path": "/records/1",
        "sensitivity": "destructive",
    }

    assert not ChatWriteConfirmationService.should_block_execution(
        message="confirmo, pode excluir o registro 1",
        action=action,
    )


def test_read_action_not_blocked():
    assert not ChatWriteConfirmationService.should_block_execution(
        message="qual o estoque do produto 10080001",
        action={
            "method": "GET",
            "path": "/products/{code}/stock",
            "sensitivity": "read",
        },
    )

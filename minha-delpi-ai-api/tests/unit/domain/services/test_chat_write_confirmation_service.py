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


def test_user_confirmed_accepts_pode_aplicar():
    assert ChatWriteConfirmationService.user_confirmed("pode aplicar") is True


def test_read_action_not_blocked():
    assert not ChatWriteConfirmationService.should_block_execution(
        message="qual o estoque do produto 10080001",
        action={
            "method": "GET",
            "path": "/products/{code}/stock",
            "sensitivity": "read",
        },
    )


def test_pac_create_plan_requires_confirmation_before_write():
    action = {
        "method": "POST",
        "path": "/quality/action-plans",
        "operationId": "create_quality_action_plan",
        "sensitivity": "write",
        "summary": "Criar plano de ação qualidade",
    }

    assert ChatWriteConfirmationService.should_block_execution(
        message="crie um plano PAC para NC externa na filial 01",
        action=action,
    )

    assert not ChatWriteConfirmationService.should_block_execution(
        message="confirmo. crie o plano PAC para NC externa na filial 01",
        action=action,
    )


def test_post_without_write_sensitivity_still_blocked_without_confirm():
    """F3 — selection/execution parity: sensitive method without confirm blocks."""
    action = {
        "method": "POST",
        "path": "/widgets",
        "sensitivity": "",
        "summary": "Criar widget",
    }
    assert ChatWriteConfirmationService.action_requires_confirmation(action)
    assert ChatWriteConfirmationService.should_block_execution(
        message="cria o widget",
        action=action,
    )


def test_sql_post_is_parallel_safe_and_skips_write_confirm():
    action = {
        "method": "POST",
        "path": "/data/sql",
        "sensitivity": "sql",
    }
    assert ChatWriteConfirmationService.is_parallel_safe_read(action)
    assert not ChatWriteConfirmationService.action_requires_confirmation(action)

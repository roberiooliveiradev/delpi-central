from app.domain.services.chat_operational_pipeline_service import (
    ChatOperationalPipelineService,
)


def test_should_optimize_for_product_code_with_allowed_actions():
    assert ChatOperationalPipelineService.should_optimize(
        "descrição do produto 10080047",
        ["action-1"],
    )


def test_should_optimize_for_stock_follow_up_terms():
    assert ChatOperationalPipelineService.should_optimize(
        "busque o estoque desse produto",
        ["action-1"],
    )


def test_should_not_optimize_without_allowed_actions():
    assert not ChatOperationalPipelineService.should_optimize(
        "descrição do produto 10080047",
        [],
    )


def test_should_not_optimize_long_mixed_documental_operational_question():
    message = (
        "explique o procedimento completo de como consultar estoque "
        "e saldo disponível nas filiais segundo a política interna da empresa"
    )

    assert len(message) > 100
    assert not ChatOperationalPipelineService.should_optimize(
        message,
        ["action-1"],
    )

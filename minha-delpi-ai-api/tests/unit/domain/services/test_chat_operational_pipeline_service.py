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

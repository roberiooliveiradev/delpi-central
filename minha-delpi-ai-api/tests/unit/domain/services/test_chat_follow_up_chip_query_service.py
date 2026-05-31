from app.domain.services.chat_follow_up_chip_query_service import (
    ChatFollowUpChipQueryService,
)


def test_detects_structure_chip_query():
    assert ChatFollowUpChipQueryService.is_explicit_chip_query(
        "mostre a estrutura do produto 10080001",
    )


def test_detects_stock_chip_query():
    assert ChatFollowUpChipQueryService.is_explicit_chip_query(
        "qual o estoque do produto 90260015?",
    )


def test_ignores_vague_follow_up_without_full_chip_shape():
    assert not ChatFollowUpChipQueryService.is_explicit_chip_query("agora estoque")

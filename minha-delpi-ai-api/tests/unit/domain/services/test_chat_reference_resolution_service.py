from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)


def test_resolve_product_on_follow_up():
    resolved, used = ChatReferenceResolutionService.resolve(
        "agora estoque",
        {"productCode": "10080001"},
    )

    assert used == ["productCode"]
    assert resolved[0]["value"] == "10080001"


def test_no_resolve_when_code_in_message():
    resolved, used = ChatReferenceResolutionService.resolve(
        "estoque do produto 10080002",
        {"productCode": "10080001"},
    )

    assert used == []
    assert resolved == []

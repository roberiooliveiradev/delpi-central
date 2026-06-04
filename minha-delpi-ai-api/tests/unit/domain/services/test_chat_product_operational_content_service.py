from app.domain.services.chat_product_operational_content_service import (
    ChatProductOperationalContentService,
)


def test_scope_labels_from_api_path_loads_json():
    labels = ChatProductOperationalContentService.scope_labels_from_api_path(
        "/products/10080022/stock"
    )

    assert labels == ["estoque"]


def test_join_list_pt_two_items():
    joined = ChatProductOperationalContentService.join_list_pt(
        ["estoque", "onde o item é usado"]
    )

    assert joined == "estoque e onde o item é usado"

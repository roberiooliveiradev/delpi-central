from app.application.services.response_meta_builder import ResponseMetaBuilder


def test_build_includes_data_version_and_shape() -> None:
    meta = ResponseMetaBuilder.build(
        operation_id="get_product_stock",
        entity="product_stock",
        shape="paged_list",
    )
    assert meta["dataVersion"] == "2026-06"
    assert meta["operationId"] == "get_product_stock"
    assert meta["entity"] == "product_stock"
    assert meta["shape"] == "paged_list"


def test_pagination_from_data_reads_page_fields() -> None:
    pagination = ResponseMetaBuilder.pagination_from_data(
        {"page": 1, "page_size": 50, "total": 2, "total_pages": 1}
    )
    assert pagination == {
        "page": 1,
        "page_size": 50,
        "total": 2,
        "total_pages": 1,
    }

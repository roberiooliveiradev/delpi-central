import pytest

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


def test_pagination_from_data_reads_operational_playbook_fields() -> None:
    pagination = ResponseMetaBuilder.pagination_from_data(
        {
            "items": [],
            "summary": {},
            "pagination": {
                "limit": 50,
                "offset": 0,
                "returned": 50,
                "is_complete": False,
            },
        }
    )
    assert pagination == {
        "limit": 50,
        "offset": 0,
        "returned": 50,
        "is_complete": False,
    }


@pytest.mark.parametrize(
    ("data", "expected_shape"),
    [
        ({"page": 1, "page_size": 10, "total": 0, "items": []}, "paged_list"),
        ({"root": {"code": "X"}, "items": []}, "hierarchy"),
        ({"product": {"code": "90269001"}, "stock": []}, "product_snapshot"),
        (
            {
                "product": {"code": "90269001"},
                "structure": {},
                "guide": {},
            },
            "composite_analysis",
        ),
        ({"items": [{"a": 1}], "summary": {"total": 1}}, "playbook_report"),
        ({"rol": 100}, "scalar"),
        ([], "paged_list"),
        ([{"id": 1}], "scalar"),
    ],
)
def test_infer_shape(data, expected_shape) -> None:
    assert ResponseMetaBuilder.infer_shape(data) == expected_shape

from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)


def test_extract_api_delpi_response_meta_reads_root_meta() -> None:
    envelope = {
        "success": True,
        "message": "ok",
        "data": {"items": []},
        "meta": {
            "entity": "product_stock",
            "shape": "paged_list",
        },
    }
    meta = ExecuteExternalActionUseCase._extract_api_delpi_response_meta(envelope)
    assert meta == {"entity": "product_stock", "shape": "paged_list"}


def test_extract_api_delpi_response_meta_ignores_plain_payload() -> None:
    assert ExecuteExternalActionUseCase._extract_api_delpi_response_meta({"items": []}) is None

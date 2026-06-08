import json
from unittest.mock import MagicMock

from app.application.dto.product.product_analyser_request import ProductAnalyserRequest
from app.application.use_cases.product.product_analyser_use_case import ProductAnalyserUseCase


def _large_block(prefix: str, count: int = 100) -> dict:
    return {
        "items": [
            {"code": f"{prefix}{index:04d}", "description": f"ITEM {index}"}
            for index in range(count)
        ],
        "total": count,
    }


def _build_use_case(
    *,
    structure_payload: dict,
    guide_payload: dict,
    inspection_payload: dict,
) -> ProductAnalyserUseCase:
    product = MagicMock()
    product.to_dict.return_value = {
        "code": "90269001",
        "description": "PRODUTO FICTICIO PA",
        "type": "PA",
        "drawing_code": "IGNORAR",
    }
    search_result = MagicMock(items=[product])

    search_uc = MagicMock()
    search_uc.execute.return_value = search_result

    structure_uc = MagicMock()
    structure_uc.execute.return_value = structure_payload

    guide_uc = MagicMock()
    guide_uc.execute.return_value = guide_payload

    inspection_uc = MagicMock()
    inspection_uc.execute.return_value = inspection_payload

    return ProductAnalyserUseCase(
        search_products_use_case=search_uc,
        structure_use_case=structure_uc,
        guide_use_case=guide_uc,
        inspection_use_case=inspection_uc,
    )


def test_analyser_summary_payload_is_smaller_than_full() -> None:
    full_structure = _large_block("50")
    full_guide = _large_block("G")
    full_inspection = _large_block("I")
    summary_structure = {
        "items": full_structure["items"][:3],
        "total": full_structure["total"],
    }
    summary_guide = {
        "items": full_guide["items"][:3],
        "total": full_guide["total"],
    }
    summary_inspection = {
        "items": full_inspection["items"][:3],
        "total": full_inspection["total"],
    }

    use_case = _build_use_case(
        structure_payload=full_structure,
        guide_payload=full_guide,
        inspection_payload=full_inspection,
    )

    def structure_side_effect(dto):
        if dto.page_size == 3:
            return summary_structure
        return full_structure

    def guide_side_effect(dto):
        if dto.page_size == 3:
            return summary_guide
        return full_guide

    def inspection_side_effect(dto):
        if dto.page_size == 3:
            return summary_inspection
        return full_inspection

    use_case.structure_use_case.execute.side_effect = structure_side_effect
    use_case.guide_use_case.execute.side_effect = guide_side_effect
    use_case.inspection_use_case.execute.side_effect = inspection_side_effect

    full_result = use_case.execute(ProductAnalyserRequest(code="90269001", view="full"))
    summary_result = use_case.execute(ProductAnalyserRequest(code="90269001", view="summary"))

    full_size = len(json.dumps(full_result, ensure_ascii=False))
    summary_size = len(json.dumps(summary_result, ensure_ascii=False))

    assert summary_size < full_size * 0.3


def test_analyser_summary_limits_sections_and_product_fields() -> None:
    use_case = _build_use_case(
        structure_payload={"items": [{"code": "50219001"}], "total": 1},
        guide_payload={"items": [{"operation": "10"}], "total": 1},
        inspection_payload={"items": [{"work_center": "QP6"}], "total": 1},
    )

    result = use_case.execute(ProductAnalyserRequest(code="90269001", view="summary"))

    assert "drawing_code" not in (result.get("product") or {})
    assert len(result["structure"]["items"]) <= 3
    assert len(result["guide"]["items"]) <= 3
    assert len(result["inspection"]["items"]) <= 3

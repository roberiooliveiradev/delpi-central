"""INT-1 Front B — product structure full-mode must not emit null pagination."""

from __future__ import annotations

from typing import Any

from app.application.dto.product.list_product_structured_request import (
    ListProductStructureRequest,
)
from app.application.external_capabilities.dynamic_information.projection import (
    bound_response_payload,
    classify_source_pagination,
    derive_response_completeness,
)
from app.application.use_cases.product.list_product_structure_use_case import (
    ListProductStructureUseCase,
)


class _FakeStructureRepo:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.last_max_depth: int | None = None

    def fetch_structure_rows(self, code: str, max_depth: int):
        self.last_max_depth = max_depth
        return list(self._rows)


def _chicote_rows() -> list[dict[str, Any]]:
    return [
        {
            "parent_code": "90260921",
            "parent_description": "CHICOTE DE LIGACAO",
            "parent_type": "PA",
            "parent_unit": "MI",
            "component_code": "10020003",
            "component_description": "CABO PVC",
            "component_type": "MP",
            "component_unit": "MT",
            "quantity": 175.0,
            "bom_level": 1,
        }
    ]


def test_full_mode_omits_null_pagination_and_marks_complete() -> None:
    repo = _FakeStructureRepo(_chicote_rows())
    uc = ListProductStructureUseCase(repo)
    result = uc.execute(ListProductStructureRequest(code="90260921"))

    assert repo.last_max_depth == 999
    assert result["root"]["code"] == "90260921"
    assert len(result["items"]) == 1
    assert result["items"][0]["code"] == "10020003"
    assert result["total"] == 1
    assert "page" not in result
    assert "page_size" not in result
    assert "total_pages" not in result

    assert classify_source_pagination(result) == "complete"
    is_complete, truncated = derive_response_completeness(result)
    assert is_complete is True and truncated is False
    bounded = bound_response_payload(result, max_bytes=200_000, max_items=50)
    assert bounded["is_complete"] is True


def test_full_mode_empty_structure_omits_null_pagination() -> None:
    repo = _FakeStructureRepo([])
    uc = ListProductStructureUseCase(repo)
    result = uc.execute(ListProductStructureRequest(code="MISSING"))

    assert result["root"] is None
    assert result["items"] == []
    assert result["total"] == 0
    assert "page" not in result
    assert "page_size" not in result
    assert "total_pages" not in result
    assert classify_source_pagination(result) == "complete"
    assert derive_response_completeness(result) == (True, False)


def test_paged_mode_preserves_page_envelope() -> None:
    repo = _FakeStructureRepo(_chicote_rows())
    uc = ListProductStructureUseCase(repo)
    result = uc.execute(
        ListProductStructureRequest(code="90260921", page=1, page_size=50)
    )

    assert result["page"] == 1
    assert result["page_size"] == 50
    assert result["total"] == 1
    assert result["total_pages"] == 1
    assert classify_source_pagination(result) == "complete"

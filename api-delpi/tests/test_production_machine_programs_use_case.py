"""Use case — top intermediários para programas de máquina."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.dto.production.list_machine_program_top_intermediates_request import (
    ListMachineProgramTopIntermediatesRequest,
)
from app.application.use_cases.production.list_production_machine_program_top_intermediates_use_case import (
    ListProductionMachineProgramTopIntermediatesUseCase,
)


def test_list_top_intermediates_requires_branch() -> None:
    use_case = ListProductionMachineProgramTopIntermediatesUseCase(MagicMock())
    with pytest.raises(ValueError, match="branch"):
        use_case.execute(ListMachineProgramTopIntermediatesRequest(branch=""))


def test_list_top_intermediates_default_period_and_paging() -> None:
    repo = MagicMock()
    repo.fetch_top_intermediates.return_value = (
        [
            {
                "intermediate_code": "50212155",
                "intermediate_description": "PI teste",
                "finished_product_code": "90123456",
                "cutting_work_center": "CT-12",
                "has_open_production_order": True,
                "qty_produced": 100.0,
                "appointment_count": 3,
            }
        ],
        1,
    )
    use_case = ListProductionMachineProgramTopIntermediatesUseCase(repo)
    result = use_case.execute(
        ListMachineProgramTopIntermediatesRequest(branch="01", page=1, page_size=10)
    )

    assert result["total"] == 1
    assert result["page"] == 1
    assert result["items"][0]["intermediate_code"] == "50212155"
    assert result["summary"]["branch_filter_applied"] is True
    assert result["summary"]["top_limit"] == 100
    assert result["summary"]["is_complete"] is True
    call_kwargs = repo.fetch_top_intermediates.call_args.kwargs
    assert call_kwargs["branch"] == "01"
    assert call_kwargs["page_size"] == 10
    assert len(call_kwargs["date_start"]) == 8
    assert len(call_kwargs["date_end_exclusive"]) == 8


def test_list_top_intermediates_caps_total_at_100() -> None:
    repo = MagicMock()
    repo.fetch_top_intermediates.return_value = ([{"intermediate_code": f"5{i:07d}"} for i in range(10)], 450)
    use_case = ListProductionMachineProgramTopIntermediatesUseCase(repo)
    result = use_case.execute(
        ListMachineProgramTopIntermediatesRequest(branch="01", page=1, page_size=10)
    )

    assert result["total"] == 100
    assert len(result["items"]) == 10
    assert result["total_pages"] == 10
    assert result["summary"]["is_complete"] is True


def test_list_top_intermediates_rejects_page_beyond_top_limit() -> None:
    repo = MagicMock()
    repo.fetch_top_intermediates.return_value = ([{"intermediate_code": "50212155"}], 450)
    use_case = ListProductionMachineProgramTopIntermediatesUseCase(repo)
    result = use_case.execute(
        ListMachineProgramTopIntermediatesRequest(branch="01", page=11, page_size=10)
    )

    assert result["items"] == []
    assert result["total"] == 100
    assert result["summary"]["top_limit"] == 100

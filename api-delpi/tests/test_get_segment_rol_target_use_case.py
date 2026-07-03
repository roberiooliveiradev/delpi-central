from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.use_cases.commercial.get_segment_rol_target_use_case import (
    GetSegmentRolTargetUseCase,
)
from app.domain.entities.commercial.new_business_rol_pct import NewBusinessRolPct


def test_get_segment_rol_target_use_case_returns_weg_rol() -> None:
    repository = MagicMock()
    repository.get_new_business_rol_pct.return_value = NewBusinessRolPct(
        branch="01",
        start_date="01-05-2026",
        end_date="31-05-2026",
        total_rol=1_000_000.0,
        new_business_rol=400_000.0,
        weg_rol=600_000.0,
        new_business_rol_pct=40.0,
    )

    use_case = GetSegmentRolTargetUseCase(
        new_business_rol_pct_repository=repository,
        segment_kind="weg",
    )

    result = use_case.execute(
        CommercialTargetRequest(
            branch="01",
            start_date="01-05-2026",
            end_date="31-05-2026",
        )
    )

    assert result["rol"] == 600_000.0
    assert result["branch"] == "01"


def test_get_segment_rol_target_use_case_returns_new_business_rol() -> None:
    repository = MagicMock()
    repository.get_new_business_rol_pct.return_value = NewBusinessRolPct(
        branch="02",
        start_date="01-05-2026",
        end_date="31-05-2026",
        total_rol=800_000.0,
        new_business_rol=250_000.0,
        weg_rol=550_000.0,
        new_business_rol_pct=31.25,
    )

    use_case = GetSegmentRolTargetUseCase(
        new_business_rol_pct_repository=repository,
        segment_kind="new_business",
    )

    result = use_case.execute(
        CommercialTargetRequest(
            branch="02",
            start_date="01-05-2026",
            end_date="31-05-2026",
        )
    )

    assert result["rol"] == 250_000.0

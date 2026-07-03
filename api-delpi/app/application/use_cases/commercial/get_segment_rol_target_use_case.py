from __future__ import annotations

from typing import Literal

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from app.domain.ports.commercial.new_business_rol_pct_repository_port import (
    NewBusinessRolPctRepositoryPort,
)

SegmentRolKind = Literal["weg", "new_business"]

_ROL_FIELD_BY_KIND: dict[SegmentRolKind, str] = {
    "weg": "weg_rol",
    "new_business": "new_business_rol",
}


class GetSegmentRolTargetUseCase:
    def __init__(
        self,
        *,
        new_business_rol_pct_repository: NewBusinessRolPctRepositoryPort,
        segment_kind: SegmentRolKind,
    ) -> None:
        self._new_business_rol_pct_repository = new_business_rol_pct_repository
        self._segment_kind = segment_kind
        self._rol_field = _ROL_FIELD_BY_KIND[segment_kind]

    def execute(self, request: CommercialTargetRequest) -> dict:
        indicator = self._new_business_rol_pct_repository.get_new_business_rol_pct(
            NewBusinessRolPctRequest(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                customer_segment=None,
            )
        )
        rol_value = float(getattr(indicator, self._rol_field) or 0)

        return {
            "branch": request.branch,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "rol": rol_value,
        }

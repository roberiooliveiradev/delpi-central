from __future__ import annotations

from typing import Optional

from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)


def parse_customer_segment(value: Optional[str]) -> Optional[str]:
    return CommercialCustomerSegmentService.normalize_customer_segment(value)


def build_get_commercial_proposal_request(
    proposal_number: str,
    *,
    branch: str,
    revision: Optional[str] = None,
) -> GetCommercialProposalRequest:
    normalized_branch = (branch or "").strip()
    if not normalized_branch:
        raise ValueError("branch é obrigatório.")

    normalized_number = (proposal_number or "").strip()
    if not normalized_number:
        raise ValueError("proposal_number é obrigatório.")

    return GetCommercialProposalRequest(
        branch=normalized_branch,
        proposal_number=normalized_number,
        revision=(revision or "").strip() or None,
    )

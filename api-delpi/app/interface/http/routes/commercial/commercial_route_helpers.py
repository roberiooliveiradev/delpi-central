from __future__ import annotations

from typing import Optional

from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)
from app.domain.services.commercial_customer_codes_filter_service import (
    CommercialCustomerCodesFilterService,
)


def parse_customer_segment(value: Optional[str]) -> Optional[str]:
    return CommercialCustomerSegmentService.normalize_customer_segment(value)


def parse_customer_codes(value: Optional[str]) -> Optional[list[str]]:
    return CommercialCustomerCodesFilterService.normalize(value)


def parse_customer_names(value: Optional[str]) -> Optional[list[str]]:
    from app.domain.services.commercial_customer_name_filter_service import (
        CommercialCustomerNameFilterService,
    )

    return CommercialCustomerNameFilterService.normalize(value)


def parse_include_flags(value: Optional[str]):
    from app.domain.services.commercial_analysis_filter_service import (
        CommercialAnalysisFilterService,
    )

    return CommercialAnalysisFilterService.parse_include_flags(value)


def build_commercial_analysis_filter_request(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    granularity: str = "week",
    branch: Optional[str] = None,
    customer_segment: Optional[str] = None,
    customer_codes: Optional[str] = None,
    customer_names: Optional[str] = None,
    exclude_customer_codes: Optional[str] = None,
    exclude_customer_names: Optional[str] = None,
    group_by: str = "customer",
    page: int = 1,
    page_size: int = 50,
    include: Optional[str] = None,
):
    from app.domain.services.commercial_analysis_filter_request import (
        CommercialAnalysisFilterRequest,
    )

    request = CommercialAnalysisFilterRequest(
        start_date=start_date,
        end_date=end_date,
        granularity=granularity,
        branch=branch,
        customer_segment=parse_customer_segment(customer_segment),
        customer_codes=parse_customer_codes(customer_codes),
        customer_names=parse_customer_names(customer_names),
        exclude_customer_codes=parse_customer_codes(exclude_customer_codes),
        exclude_customer_names=parse_customer_names(exclude_customer_names),
        group_by=group_by,
        page=page,
        page_size=page_size,
        include_flags=parse_include_flags(include),
    )
    request.validate()
    return request


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

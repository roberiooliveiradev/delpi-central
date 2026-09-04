from dataclasses import dataclass
from typing import Optional


@dataclass
class SummarizeCommercialProposalsByCollaboratorRequest:
    """Opening-date universe (AD1_DATA); never filtered by list status."""

    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    product_code: Optional[str] = None
    product_group: Optional[str] = None

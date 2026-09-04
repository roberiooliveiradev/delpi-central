from dataclasses import dataclass
from typing import Optional


@dataclass
class SummarizeCommercialProposalsByCollaboratorRequest:
    """Period filters for collaborator summary (list Status is not applied).

    Open/lost use AD1_DATA; won uses acceptance date — same semantics as the proposals list.
    """

    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    product_code: Optional[str] = None
    product_group: Optional[str] = None

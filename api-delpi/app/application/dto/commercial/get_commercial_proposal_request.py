from dataclasses import dataclass
from typing import Optional


@dataclass
class GetCommercialProposalRequest:
    branch: str
    proposal_number: str
    revision: Optional[str] = None

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class CommercialProposal:
    branch: str
    proposal_number: str
    revision: str
    description: Optional[str] = None
    proposal_date: Optional[str] = None
    end_date: Optional[str] = None
    status_code: Optional[str] = None
    status_label: Optional[str] = None
    status_category: Optional[str] = None
    customer_code: Optional[str] = None
    customer_store: Optional[str] = None
    stage: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

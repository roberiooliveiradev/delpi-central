from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.entities.commercial.commercial_proposal import CommercialProposal


@dataclass
class CommercialProposalDetail(CommercialProposal):
    customer_store: Optional[str] = None
    customer_name: Optional[str] = None
    seller_code: Optional[str] = None
    seller_name: Optional[str] = None
    process_code: Optional[str] = None
    process_label: Optional[str] = None
    stage_label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "seller_code": self.seller_code,
            "seller_name": self.seller_name,
            "process_code": self.process_code,
            "process_label": self.process_label,
            "stage_label": self.stage_label,
        }

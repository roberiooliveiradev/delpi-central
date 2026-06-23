from __future__ import annotations

from typing import Optional

from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)


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

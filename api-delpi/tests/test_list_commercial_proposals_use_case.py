from unittest.mock import MagicMock

from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.models.page import Page
from app.application.use_cases.commercial.list_commercial_proposals_use_case import (
    ListCommercialProposalsUseCase,
)
from app.domain.entities.commercial.commercial_proposal import CommercialProposal


def test_list_commercial_proposals_use_case_returns_page_dict() -> None:
    repository = MagicMock()
    repository.list_proposals.return_value = Page(
        items=[
            CommercialProposal(
                branch="01",
                proposal_number="000123",
                revision="01",
                status_code="9",
                status_label="Ganha",
                status_category="won",
            )
        ],
        total=1,
        page=1,
        page_size=50,
    )

    use_case = ListCommercialProposalsUseCase(repository)
    result = use_case.execute(
        ListCommercialProposalsRequest(
            start_date="2026-01-01",
            end_date="2026-05-31",
            branch="01",
        )
    )

    repository.list_proposals.assert_called_once()
    assert result["total"] == 1
    assert result["items"][0]["proposal_number"] == "000123"
    assert result["items"][0]["status_label"] == "Ganha"

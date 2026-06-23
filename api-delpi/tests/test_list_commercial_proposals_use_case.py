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


def test_get_commercial_proposal_use_case_returns_detail_dict() -> None:
    from app.application.dto.commercial.get_commercial_proposal_request import (
        GetCommercialProposalRequest,
    )
    from app.application.use_cases.commercial.get_commercial_proposal_use_case import (
        GetCommercialProposalUseCase,
    )
    from app.domain.entities.commercial.commercial_proposal_detail import (
        CommercialProposalDetail,
    )
    from app.domain.entities.lmp.lmp_product import LMPProduct

    repository = MagicMock()
    repository.get_proposal.return_value = CommercialProposalDetail(
        branch="01",
        proposal_number="003446",
        revision="08",
        description="OV teste",
        status_code="9",
        status_label="Ganha",
        status_category="won",
        customer_name="Cliente X",
    )

    lmp_repository = MagicMock()
    lmp_repository.list_ov_products.return_value = [
        LMPProduct(
            code="90123456",
            description="Produto teste (REF-01)",
            group_code="100",
            type="PI",
            qtd_pi=2,
        )
    ]

    use_case = GetCommercialProposalUseCase(repository, lmp_repository)
    result = use_case.execute(
        GetCommercialProposalRequest(
            branch="01",
            proposal_number="003446",
            revision="08",
        )
    )

    repository.get_proposal.assert_called_once()
    lmp_repository.list_ov_products.assert_called_once_with(
        sale_number="003446",
        requested_branch="01",
    )
    assert result["proposal_number"] == "003446"
    assert result["customer_name"] == "Cliente X"
    assert len(result["list_products"]) == 1
    assert result["list_products"][0]["code"] == "90123456"
    assert result["list_products"][0]["qtd_pi"] == 2

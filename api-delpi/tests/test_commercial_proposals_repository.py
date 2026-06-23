from unittest.mock import patch

from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_proposals_repository import (
    CommercialProposalsRepository,
)


def test_list_proposals_won_filters_by_close_date_and_open_date() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        branch="01",
        status="won",
        page=1,
        page_size=50,
    )
    captured: dict[str, str] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["list_sql"] = sql
        captured["list_params"] = str(params)
        return []

    def _execute_one(sql: str, params: tuple) -> dict:
        captured["count_sql"] = sql
        return {"total": 0}

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                with patch.object(repository, "execute_one", side_effect=_execute_one):
                    repository.list_proposals(request)

    sql = captured["list_sql"]
    assert "AD1.AD1_DATA" in sql
    assert "AD1.AD1_DTFIM" in sql
    assert f"AD1.AD1_STATUS = '{WON_STATUS_CODE}'" in sql or (
        f"AD1.AD1_STATUS = ?" in sql
    )


def test_get_proposal_loads_header_with_customer_and_stage_labels() -> None:
    repository = CommercialProposalsRepository()
    request = GetCommercialProposalRequest(
        branch="01",
        proposal_number="003446",
        revision="08",
    )
    captured: dict[str, str] = {}

    def _execute_one(sql: str, params: tuple) -> dict:
        captured["sql"] = sql
        captured["params"] = str(params)
        return {
            "branch": "01",
            "proposal_number": "003446",
            "revision": "08",
            "description": "Teste",
            "proposal_date": "20260130",
            "end_date": "20260623",
            "status_code": "9",
            "customer_code": "000123",
            "customer_store": "01",
            "stage": "000013",
            "process_code": "000001",
            "seller_code": "000001",
            "customer_name": "Cliente",
            "seller_name": "Vendedor",
            "stage_label": "ENCERRADO",
            "process_label": "OPORTUNIDADE",
        }

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_one", side_effect=_execute_one):
                result = repository.get_proposal(request)

    sql = captured["sql"]
    assert "FROM AD1010 AD1" in sql
    assert "AC2010 AC2" in sql
    assert "AC1010 AC1" in sql
    assert result is not None
    assert result.stage_label == "ENCERRADO"
    assert result.customer_name == "Cliente"

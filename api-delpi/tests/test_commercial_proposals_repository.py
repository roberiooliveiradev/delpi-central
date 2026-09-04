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


def test_list_proposals_won_filters_by_acceptance_date() -> None:
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
    assert "AD1.AD1_DTASSI" in sql
    assert "proposal_acceptance_date" in sql
    assert f"AD1.AD1_STATUS = '{WON_STATUS_CODE}'" in sql or (
        f"AD1.AD1_STATUS = ?" in sql
    )


def test_list_proposals_applies_customer_segment_filter() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        customer_segment="new_business",
        page=1,
        page_size=50,
    )
    captured: dict[str, str] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["list_sql"] = sql
        return []

    def _execute_one(sql: str, params: tuple) -> dict:
        return {"total": 0}

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                with patch.object(repository, "execute_one", side_effect=_execute_one):
                    repository.list_proposals(request)

    sql = captured["list_sql"]
    assert "AD1.AD1_CODCLI" in sql
    assert "NOT (" in sql
    assert "000001" in sql


def test_list_proposals_applies_sort_by_on_server() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        page=1,
        page_size=20,
        sort_by="proposal_number",
        sort_dir="asc",
    )
    captured: dict[str, str] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["list_sql"] = sql
        return []

    def _execute_one(sql: str, params: tuple) -> dict:
        return {"total": 0}

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                with patch.object(repository, "execute_one", side_effect=_execute_one):
                    repository.list_proposals(request)

    sql = captured["list_sql"]
    assert "ORDER BY proposal_number ASC" in sql
    assert "proposal_number ASC, proposal_number ASC" not in sql


def test_list_proposals_sort_by_stage_on_server() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        page=1,
        page_size=20,
        sort_by="stage",
        sort_dir="desc",
    )
    captured: dict[str, str] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["list_sql"] = sql
        return []

    def _execute_one(sql: str, params: tuple) -> dict:
        return {"total": 0}

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                with patch.object(repository, "execute_one", side_effect=_execute_one):
                    repository.list_proposals(request)

    assert "ORDER BY stage DESC" in captured["list_sql"]


def test_list_proposals_applies_search_on_latest_rows() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        page=1,
        page_size=20,
        search="weg",
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
    assert "WHERE rn = 1" in sql
    assert "AD1_DESCRI COLLATE Latin1_General_CI_AI LIKE ?" in sql
    assert "%weg%" in captured["list_params"]


def test_list_proposals_applies_product_code_and_group_exists() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        page=1,
        page_size=20,
        product_code="90AAAA01",
        product_group="1234",
    )
    captured: dict[str, str] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["list_sql"] = sql
        captured["list_params"] = str(params)
        return []

    def _execute_one(sql: str, params: tuple) -> dict:
        return {"total": 0}

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                with patch.object(repository, "execute_one", side_effect=_execute_one):
                    repository.list_proposals(request)

    sql = captured["list_sql"]
    assert "EXISTS" in sql
    assert "ADJ010 ADJ" in sql
    assert "SB1010 SB1" in sql
    assert "ADJ.ADJ_PROD" in sql
    assert "B1_GRUPO" in sql
    assert "90AAAA01" in captured["list_params"]
    assert "1234" in captured["list_params"]


def test_list_proposals_without_product_filters_omits_exists() -> None:
    repository = CommercialProposalsRepository()
    request = ListCommercialProposalsRequest(
        start_date="2026-01-01",
        end_date="2026-06-30",
        page=1,
        page_size=20,
    )
    captured: dict[str, str] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["list_sql"] = sql
        return []

    def _execute_one(sql: str, params: tuple) -> dict:
        return {"total": 0}

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                with patch.object(repository, "execute_one", side_effect=_execute_one):
                    repository.list_proposals(request)

    assert "ADJ010" not in captured["list_sql"]

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

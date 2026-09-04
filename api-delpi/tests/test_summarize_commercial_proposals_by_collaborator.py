from unittest.mock import patch

from app.application.dto.commercial.summarize_commercial_proposals_by_collaborator_request import (
    SummarizeCommercialProposalsByCollaboratorRequest,
)
from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_proposals_repository import (
    CommercialProposalsRepository,
)


def test_summarize_by_collaborator_groups_without_page_cap() -> None:
    repository = CommercialProposalsRepository()
    request = SummarizeCommercialProposalsByCollaboratorRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_segment="weg",
    )
    captured: dict[str, object] = {}

    def _execute_query(sql: str, params: tuple) -> list:
        captured["sql"] = sql
        captured["params"] = params
        return [
            {
                "seller_code": "000001",
                "seller_name": "Ana",
                "open_count": 35,
                "won_count": 11,
                "lost_count": 0,
                "total_count": 46,
                "age_days_avg": 15.333,
            }
        ]

    with patch.object(CommercialProposalsRepository, "__enter__", return_value=repository):
        with patch.object(CommercialProposalsRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=_execute_query):
                result = repository.summarize_by_collaborator(request)

    sql = str(captured["sql"])
    assert "GROUP BY" in sql
    assert "OFFSET" not in sql.upper()
    assert "FETCH NEXT" not in sql.upper()
    assert "AD1.AD1_DATA" in sql
    assert WON_STATUS_CODE in sql
    assert "AD1_DTASSI" not in sql
    assert result["truncated"] is False
    assert result["source_count"] == 46
    assert result["items"][0]["seller_code"] == "000001"
    assert result["items"][0]["won_count"] == 11
    assert result["items"][0]["age_days_avg"] == 15.3


def test_collaborator_summary_route_path_registered() -> None:
    from app.interface.http.routes.commercial.commercial_router import router

    paths = [getattr(route, "path", "") for route in router.routes]
    assert any(path.endswith("/proposals/collaborator-summary") for path in paths)

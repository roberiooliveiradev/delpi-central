from unittest.mock import MagicMock

from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.services.response_meta_builder import ResponseMetaBuilder
from app.application.use_cases.lmp.get_lmp_use_case import GetLMPUseCase
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_history_event import LMPHistoryEvent
from app.domain.entities.lmp.lmp_product import LMPProduct


def test_get_lmp_use_case_enriches_dashboard_status_fields():
    repository = MagicMock()
    repository.get_lmp.return_value = LMP(
        branch="01",
        sale_number="003578",
        sale_description="BUHLER - 1 ITEM",
        listing_kind="LMP",
        start_date="20260520",
        end_date=None,
        engineering_status="ABERTA",
        qtd_engineering_entries=3,
        qtd_engineering_closed=1,
        qtd_advanced_from_engineering=1,
        qtd_returned_from_engineering=0,
        engineering_total_minutes=120,
        qtd_pi=0,
        costumer_name="BUHLER",
        list_products=[
            LMPProduct(code="10080001", description="ITEM TESTE", qtd_pi=0),
        ],
        list_history=[
            LMPHistoryEvent(
                revision="001",
                process_code="000003",
                stage_code="000003",
                start_date="20260520",
                start_time="08:30",
                duration_minutes=45,
                status="1",
                is_engineering=True,
            ),
        ],
    )

    use_case = GetLMPUseCase(repository)
    result = use_case.execute(
        GetLMPRequest(
            sale_number="003578",
            date_start="20260501",
            date_end="20260531",
            branch="01",
        )
    )

    assert result["sale_number"] == "003578"
    assert result["listing_kind"] == "LMP"
    assert result["start_date"] == "2026-05-20"
    assert result["end_date"] is None
    assert result["data_limite"] == "2026-05-26"
    assert result["nivel"] in {"Nível 1", "Nível 2", "Nível 3"}
    assert "status" in result
    assert "lead_time_util" in result
    assert len(result["list_products"]) == 1
    assert result["list_history"] == []


def test_lmp_related_routes_includes_history_links():
    routes = ResponseMetaBuilder.lmp_related_routes("003578", branch="01")

    assert routes["detail"] == "/engineering/lmps/003578?branch=01"
    assert routes["historyEvents"] == "/engineering/lmps/003578/history/events?branch=01"
    assert routes["historyFlow"] == "/engineering/lmps/003578/history/flow?branch=01"
    assert routes["dashboardItems"] == "/engineering/lmps/dashboard/items"
    assert routes["dashboardSummary"] == "/engineering/lmps/dashboard/summary"
    assert routes["list"] == "/engineering/lmps"

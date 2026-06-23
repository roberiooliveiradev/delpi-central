from unittest.mock import MagicMock

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.use_cases.lmp.get_lmp_history_events_use_case import (
    GetLmpHistoryEventsUseCase,
)
from app.application.use_cases.lmp.get_lmp_history_flow_use_case import (
    GetLmpHistoryFlowUseCase,
)
from app.domain.entities.lmp.lmp_history_event import LMPHistoryEvent


def test_get_lmp_history_events_use_case_enriches_items():
    repository = MagicMock()
    repository.get_lmp_history_panel_context.return_value = {
        "branch": "01",
        "reference_revision": "03",
        "panel_start_date": "20260615",
    }
    repository.get_lmp_history_events.return_value = [
        LMPHistoryEvent(
            revision="03",
            process_code="000003",
            stage_code="000003",
            start_date="20260615",
            start_time="08:30",
            duration_minutes=30,
            status="1",
            is_engineering=True,
        ),
    ]

    use_case = GetLmpHistoryEventsUseCase(repository)
    result = use_case.execute(
        GetLmpHistoryRequest(
            sale_number="003092",
            date_start="20260601",
            date_end="20260615",
            branch="01",
        )
    )

    assert result["sale_number"] == "003092"
    assert result["reference_revision"] == "03"
    assert result["total"] == 1
    assert result["items"][0]["process_label"] == "Engenharia"
    assert result["items"][0]["is_current"] is True


def test_get_lmp_history_flow_use_case_detects_transition():
    repository = MagicMock()
    repository.get_lmp_history_panel_context.return_value = {
        "branch": "01",
        "reference_revision": "03",
        "panel_start_date": "20260615",
    }
    repository.get_lmp_history_flow.return_value = [
        LMPHistoryEvent(
            revision="03",
            process_code="000003",
            stage_code="000003",
            start_date="20260615",
            start_time="08:30",
            end_date="20260615",
            end_time="09:00",
            status="2",
            is_engineering=True,
            next_revision="03",
            next_process_code="000004",
            next_stage_code="000010",
            next_start_date="20260615",
        ),
    ]

    use_case = GetLmpHistoryFlowUseCase(repository)
    result = use_case.execute(
        GetLmpHistoryRequest(
            sale_number="003092",
            branch="01",
        )
    )

    assert result["total"] == 1
    assert result["items"][0]["flow_transition"] == "advanced_from_engineering"
    assert result["items"][0]["flow_transition_label"] == "Saída da engenharia (avanço)"

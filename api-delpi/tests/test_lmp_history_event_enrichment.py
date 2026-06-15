from datetime import datetime

from app.domain.services.lmp_history_event_enrichment import (
    enrich_history_event,
    enrich_history_events,
    format_duration_display,
    is_engineering_flow,
    is_event_open,
    label_for_history_status,
)


def test_label_for_history_status_maps_known_codes():
    assert label_for_history_status("1") == "Em andamento"
    assert label_for_history_status("2") == "Encerrado"
    assert label_for_history_status("9") == "Status 9"


def test_is_engineering_flow_when_stage_is_engineering_even_if_process_differs():
    event = {
        "process_code": "000001",
        "stage_code": "000003",
        "is_engineering": False,
    }

    assert is_engineering_flow(event) is True


def test_format_duration_display_for_open_event():
    assert format_duration_display(2880, is_open=True) == "Em andamento · 2 dia(s)"
    assert format_duration_display(90, is_open=True) == "Em andamento · 1 h"


def test_enrich_history_event_marks_open_and_late():
    event = enrich_history_event(
        {
            "revision": "01",
            "process_code": "000001",
            "stage_code": "000003",
            "start_date": "20241125",
            "start_time": "16:28",
            "limit_date": "20241126",
            "limit_time": "16:28",
            "duration_minutes": 120,
            "status": "1",
            "is_engineering": False,
        },
        now=datetime(2026, 6, 15, 12, 0),
    )

    assert event["process_label"] == "Abertura"
    assert event["stage_label"] == "Engenharia"
    assert event["status_label"] == "Em andamento"
    assert event["is_open"] is True
    assert event["is_late"] is True
    assert event["is_engineering_flow"] is True
    assert event["duration_display"] == "Em andamento · 2 h"


def test_enrich_history_events_marks_last_open_as_current():
    events = enrich_history_events(
        [
            {
                "revision": "01",
                "process_code": "000002",
                "stage_code": "000002",
                "end_date": "20241125",
                "end_time": "10:00",
            },
            {
                "revision": "01",
                "process_code": "000001",
                "stage_code": "000003",
                "start_date": "20241125",
                "start_time": "16:28",
            },
        ]
    )

    assert is_event_open(events[0]) is False
    assert events[1]["is_current"] is True
    assert events[0]["is_current"] is False

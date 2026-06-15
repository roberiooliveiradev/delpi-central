from datetime import datetime

from app.domain.services.lmp_history_event_enrichment import (
    enrich_history_event,
    enrich_history_events,
    format_duration_display,
    is_engineering_flow,
    is_event_open,
    label_for_history_status,
    resolve_history_reference_revision,
    resolve_history_status_label,
    resolve_process_label,
    resolve_stage_label,
    revisions_match,
)


def test_label_for_history_status_maps_known_codes():
    assert label_for_history_status("1") == "Em andamento"
    assert label_for_history_status("2") == "Encerrado"
    assert label_for_history_status("9") == "Concluído"


def test_label_for_history_status_maps_extended_codes():
    assert label_for_history_status("5") == "Aguardando"
    assert label_for_history_status("8") == "Finalizado"


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


def test_resolve_labels_prefers_ac1010_and_ac2010_descriptions():
    event = {
        "process_code": "000001",
        "stage_code": "000005",
        "process_description": "Abertura comercial",
        "stage_description": "Follow-up pós-venda",
    }

    assert resolve_process_label(event) == "Abertura comercial"
    assert resolve_stage_label(event) == "Follow-up pós-venda"


def test_resolve_history_status_label_uses_encerrado_when_dtence_filled():
    event = {
        "status": "1",
        "end_date": "20241125",
        "end_time": "10:00",
    }

    assert resolve_history_status_label(event, is_open=False) == "Encerrado"


def test_enrich_history_events_scopes_current_event_to_reference_revision():
    events = enrich_history_events(
        [
            {
                "revision": "01",
                "process_code": "000001",
                "stage_code": "000001",
                "end_date": "20191106",
                "end_time": "08:33",
            },
            {
                "revision": "02",
                "process_code": "000001",
                "stage_code": "000005",
                "end_date": "20250714",
                "end_time": "23:59",
            },
            {
                "revision": "03",
                "process_code": "000001",
                "stage_code": "000001",
                "start_date": "20260615",
                "start_time": "08:00",
            },
        ],
        reference_revision="03",
    )

    assert events[0]["is_current"] is False
    assert events[1]["is_current"] is False
    assert events[2]["is_current"] is True


def test_revisions_match_ignores_leading_zeros():
    assert revisions_match("01", "001") is True
    assert revisions_match("02", "03") is False


def test_resolve_history_reference_revision_prefers_measurement():
    assert resolve_history_reference_revision("03", "02") == "03"
    assert resolve_history_reference_revision(None, "02") == "02"


def test_enrich_history_event_uses_totvs_descriptions_and_closed_status():
    event = enrich_history_event(
        {
            "revision": "01",
            "process_code": "000001",
            "stage_code": "000002",
            "process_description": "Abertura comercial",
            "stage_description": "Qualificação da oportunidade",
            "start_date": "20241125",
            "start_time": "08:00",
            "end_date": "20241125",
            "end_time": "08:05",
            "status": "1",
            "duration_minutes": 5,
        }
    )

    assert event["process_label"] == "Abertura comercial"
    assert event["stage_label"] == "Qualificação da oportunidade"
    assert event["status_label"] == "Encerrado"
    assert "process_description" not in event
    assert "stage_description" not in event

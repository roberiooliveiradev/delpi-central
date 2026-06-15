from app.domain.services.lmp_history_flow_transition import (
    detect_engineering_entry,
    detect_flow_transition,
    enrich_flow_transition_fields,
    label_for_flow_transition,
)


def test_detect_engineering_entry_when_previous_stage_is_not_engineering():
    event = {
        "revision": "01",
        "process_code": "000001",
        "stage_code": "000003",
        "is_engineering": True,
        "previous_revision": "01",
        "previous_process_code": "000001",
        "previous_stage_code": "000002",
    }

    assert detect_engineering_entry(event) is True


def test_detect_engineering_entry_false_when_previous_is_engineering():
    event = {
        "revision": "01",
        "process_code": "000001",
        "stage_code": "000008",
        "is_engineering": True,
        "previous_revision": "01",
        "previous_process_code": "000001",
        "previous_stage_code": "000003",
    }

    assert detect_engineering_entry(event) is False


def test_detect_flow_transition_advanced_from_engineering():
    event = {
        "revision": "01",
        "process_code": "000001",
        "stage_code": "000003",
        "end_date": "20191107",
        "is_engineering": True,
        "next_revision": "01",
        "next_process_code": "000001",
        "next_stage_code": "000004",
    }

    assert detect_flow_transition(event) == "advanced_from_engineering"


def test_detect_flow_transition_returned_from_engineering():
    event = {
        "revision": "01",
        "process_code": "000001",
        "stage_code": "000003",
        "end_date": "20191107",
        "is_engineering": True,
        "next_revision": "02",
        "next_process_code": "000001",
        "next_stage_code": "000002",
    }

    assert detect_flow_transition(event) == "returned_from_engineering"


def test_enrich_flow_transition_fields_exposes_labels():
    enriched = enrich_flow_transition_fields(
        {
            "revision": "01",
            "process_code": "000001",
            "stage_code": "000003",
            "end_date": "20191107",
            "is_engineering": True,
            "previous_revision": "01",
            "previous_process_code": "000001",
            "previous_stage_code": "000002",
            "next_revision": "02",
            "next_process_code": "000001",
            "next_stage_code": "000002",
        }
    )

    assert enriched["is_engineering_entry"] is True
    assert enriched["flow_transition"] == "returned_from_engineering"
    assert enriched["flow_transition_label"] == "Retorno da engenharia"
    assert "Entrada na engenharia" in enriched["flow_transition_labels"]
    assert "next_revision" not in enriched


def test_label_for_flow_transition():
    assert label_for_flow_transition("engineering_entry") == "Entrada na engenharia"

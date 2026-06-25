from app.domain.services.quality_action_plans.five_whys_service import (
    five_whys_track_lines,
    normalize_five_whys_payload,
    normalize_whys_list,
    serialize_five_whys_row,
)


def test_normalize_whys_list_accepts_strings_and_lists():
    assert normalize_whys_list(["  a ", "", "b"]) == ["a", "b"]
    assert normalize_whys_list("linha única") == ["linha única"]
    assert normalize_whys_list("a\n\nb") == ["a", "b"]


def test_normalize_five_whys_payload_migrates_legacy_columns():
    payload = normalize_five_whys_payload(
        {
            "why_1": "Falha no processo",
            "why_3": "Treinamento insuficiente",
            "detection_why_2": "Inspeção visual falhou",
            "root_cause": "Causa raiz",
        }
    )
    assert payload["occurrence_whys"] == ["Falha no processo", "Treinamento insuficiente"]
    assert payload["detection_whys"] == ["Inspeção visual falhou"]
    assert payload["root_cause"] == "Causa raiz"
    assert "why_1" not in payload


def test_serialize_five_whys_row_returns_arrays():
    row = serialize_five_whys_row(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "plan_id": "00000000-0000-0000-0000-000000000002",
            "occurrence_whys": ["a", "b"],
            "detection_whys": [],
            "root_cause": "raiz",
            "confidence_level": "medium",
        }
    )
    assert row is not None
    assert row["occurrence_whys"] == ["a", "b"]
    assert row["detection_whys"] == []


def test_five_whys_track_lines_labels_steps():
    lines = five_whys_track_lines(["primeiro", "segundo"], track_label="Ocorrência")
    assert lines == [
        "Ocorrência — Por quê 1: primeiro",
        "Ocorrência — Por quê 2: segundo",
    ]

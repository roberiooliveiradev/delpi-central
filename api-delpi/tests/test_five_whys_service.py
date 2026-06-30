from app.domain.services.quality_action_plans.five_whys_service import (
    five_whys_track_lines,
    format_why_step_answer_cell,
    format_why_step_cell,
    normalize_five_whys_payload,
    normalize_whys_list,
    normalize_whys_track,
    serialize_five_whys_row,
    split_legacy_why_text,
)


def test_normalize_whys_list_accepts_strings_and_lists():
    assert normalize_whys_list(["  a ", "", "b"]) == ["a", "b"]
    assert normalize_whys_list("linha única") == ["linha única"]
    assert normalize_whys_list("a\n\nb") == ["a", "b"]


def test_split_legacy_why_text_separates_question_and_answer():
    step = split_legacy_why_text(
        "Por que o cliente recebeu produto divergente? Porque o chicote foi expedido errado."
    )
    assert step["question"] == "Por que o cliente recebeu produto divergente?"
    assert step["answer"] == "Porque o chicote foi expedido errado."


def test_normalize_whys_track_accepts_structured_steps():
    track = normalize_whys_track(
        [
            {"question": "Por que falhou?", "answer": "Porque faltou treinamento."},
            "Legado em uma linha? Resposta legada.",
        ]
    )
    assert track == [
        {"question": "Por que falhou?", "answer": "Porque faltou treinamento."},
        {"question": "Legado em uma linha?", "answer": "Resposta legada."},
    ]


def test_normalize_five_whys_payload_migrates_legacy_columns():
    payload = normalize_five_whys_payload(
        {
            "why_1": "Falha no processo",
            "why_3": "Treinamento insuficiente",
            "detection_why_2": "Inspeção visual falhou",
            "root_cause": "Causa raiz",
        }
    )
    assert payload["occurrence_whys"] == [
        {"question": "", "answer": "Falha no processo"},
        {"question": "", "answer": "Treinamento insuficiente"},
    ]
    assert payload["detection_whys"] == [
        {"question": "", "answer": "Inspeção visual falhou"},
    ]
    assert payload["root_cause"] == "Causa raiz"
    assert "why_1" not in payload


def test_serialize_five_whys_row_returns_structured_arrays():
    row = serialize_five_whys_row(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "plan_id": "00000000-0000-0000-0000-000000000002",
            "occurrence_whys": [
                {"question": "Por quê 1?", "answer": "Resposta 1"},
                "Legado? Resposta legada.",
            ],
            "detection_whys": [],
            "root_cause": "raiz",
            "confidence_level": "medium",
        }
    )
    assert row is not None
    assert row["occurrence_whys"] == [
        {"question": "Por quê 1?", "answer": "Resposta 1"},
        {"question": "Legado?", "answer": "Resposta legada."},
    ]
    assert row["detection_whys"] == []


def test_five_whys_track_lines_labels_steps():
    lines = five_whys_track_lines(
        [{"question": "Por quê?", "answer": "Porque sim."}],
        track_label="Ocorrência",
    )
    assert lines == ["Ocorrência — Por quê 1: Por quê? Porque sim."]


def test_format_why_step_cell_uses_two_lines_when_both_fields_exist():
    assert (
        format_why_step_cell({"question": "Por quê?", "answer": "Porque sim."})
        == "Por quê?\nPorque sim."
    )


def test_format_why_step_answer_cell_exports_answer_only():
    assert (
        format_why_step_answer_cell({"question": "Por quê falhou?", "answer": "Material errado."})
        == "Material errado."
    )
    assert format_why_step_answer_cell("Só resposta legada") == "Só resposta legada"

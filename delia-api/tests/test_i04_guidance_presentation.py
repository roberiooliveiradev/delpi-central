"""K1/K2 presentation: whole guidance sections and prior-excerpt split.

Provider-neutral. No specialist-name branch. Budgets unchanged.
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    _detail_lines,
    _deterministic_guidance_content,
    _prior_excerpt_records,
    _render_synthesis,
)
from app.application.interaction.contracts import LIMITATION_RESULT_TRUNCATED


def _long_guide() -> dict:
    return {
        "objective": "Definir o indicador sem inventar meta da empresa.",
        "questions": [
            "What decision should this indicator change?",
            "What is the formula, unit, direction, source and frequency?",
        ],
        "criteria": "C" * 1500,
        "steps": ["S" * 1500],
        "limitations": "Guia somente leitura.",
    }


def test_short_guide_is_complete_without_truncation():
    body, limitations = _deterministic_guidance_content(
        "Qual é a orientação?",
        {
            "objective": "Orientação curta.",
            "prerequisites": ["Qual decisão o indicador muda?"],
            "steps": ["Registrar a fonte"],
        },
    )
    assert body is not None
    assert "Orientação curta." in body
    assert "Qual decisão o indicador muda?" in body
    assert "resultado parcial" not in body
    assert LIMITATION_RESULT_TRUNCATED not in limitations


def test_long_guide_keeps_whole_sections_and_names_the_rest():
    body, limitations = _deterministic_guidance_content(
        "Qual é a orientação?",
        _long_guide(),
    )
    assert body is not None
    assert len(body) <= 2000
    assert "Definir o indicador sem inventar meta da empresa." in body
    assert LIMITATION_RESULT_TRUNCATED in limitations
    assert "Seções do guia não exibidas neste turno:" in body
    if "C" * 100 in body:
        assert "C" * 1500 in body
    else:
        assert "criteria" in body
    assert "resultado parcial — truncado" not in body


def test_prior_bullet_does_not_keep_the_next_heading():
    prior = (
        "questions:\n"
        "- What decision should this indicator change?\n"
        "- What is the formula, unit, direction, source and frequency?\n"
        "steps:\n"
        "- Coletar definição"
    )
    excerpts = [record["excerpt"] for record in _prior_excerpt_records(prior)]
    formula = next(item for item in excerpts if item.startswith("- What is the formula"))
    assert "steps:" not in formula
    assert any(item == "steps:" or item.startswith("steps:") for item in excerpts)


def test_excerpt_render_does_not_nest_list_markers():
    lines = _detail_lines(
        [("excerpt", "- What decision should this indicator change?")]
    )
    assert lines == ["- What decision should this indicator change?"]
    assert "- -" not in lines[0]


def test_plain_excerpt_still_receives_one_marker():
    lines = _detail_lines([("excerpt", "Pergunta sem marcador")])
    assert lines == ["- Pergunta sem marcador"]


def test_list_synthesis_does_not_nest_excerpt_markers():
    records = _prior_excerpt_records(
        "prerequisites:\n"
        "- What decision should this indicator change?\n"
        "- What is the formula, unit, direction, source and frequency?"
    )
    body, reason = _render_synthesis(
        {
            "items": [
                {"record_index": 1, "fields": ["excerpt"]},
                {"record_index": 2, "fields": ["excerpt"]},
            ],
            "presentation": "list",
        },
        records,
    )
    assert reason == "rendered"
    assert body is not None
    assert "- -" not in body
    assert "What decision should this indicator change?" in body
    assert "formula, unit, direction" in body
    assert not body.rstrip().endswith("steps:")

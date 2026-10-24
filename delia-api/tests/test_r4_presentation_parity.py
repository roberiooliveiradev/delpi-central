"""R4/M06 — presentation parity characterization for the canonical owner.

Literal-output locks on the deterministic presentation helpers that R4
relocates to ``conversational_response.py``. These expectations pin
pt-BR wording, field order, bounds, escaping and control-plane
filtering byte-for-byte — the refactor is proven only if the same
inputs produce the same outputs after the move.
"""

from __future__ import annotations

from app.application.capability_provision.conversational_response import (
    _business_lines,
    _compose_answer,
    _detail_header,
    _detail_lines,
    _format_records,
    _format_structured,
    _insufficiency_content,
    _list_header,
    _md_business_lines,
    _md_leaf,
    _proven_field_differences,
    _render_synthesis,
)


RECORD = {
    "codigo": "10080092",
    "descricao": "TERM. BALA 0,50-2,27MM2",
    "tipo": "MP",
    "agent_directives": {"hidden": True},
}

RECORD_B = {
    "codigo": "04/10/1008",
    "descricao": "TERM. BALA 1,00-2,50MM2",
    "tipo": "MP",
}


def test_compose_answer_focused_sentence_verbatim():
    out = _compose_answer(
        RECORD, [("descricao", "TERM. BALA 0,50-2,27MM2")]
    )
    assert out == (
        'O campo "descricao" do registro 10080092 é: '
        'TERM. BALA 0,50-2,27MM2.'
    )


def test_compose_answer_identifier_field_selected():
    out = _compose_answer(RECORD, [("codigo", "10080092")])
    assert out == 'O campo "codigo" é: 10080092.'


def test_detail_header_uses_record_identifier():
    assert (
        _detail_header(RECORD) == "Detalhes do registro 10080092:"
    )


def test_detail_header_excerpt_records_not_registry():
    assert _detail_header({"excerpt": "Trecho A"}) == (
        "Trechos anteriores:"
    )


def test_detail_lines_omit_synthetic_excerpt_field_name():
    lines = _detail_lines(
        [("excerpt", "Trecho A"), ("codigo", "10080092")]
    )
    assert lines == ["- Trecho A", "- Codigo: 10080092"]


def test_list_header_authoritative_count():
    assert _list_header(2) == "Encontrei 2 registros:"


def test_list_header_page_slice_never_total():
    assert _list_header(2, has_more=True) == (
        "Mostrando 2 registro(s) nesta página; há mais resultados "
        "além desta página — este número não é o total."
    )


def test_list_header_prior_excerpts_wording():
    assert _list_header(
        2, records=({"excerpt": "a"}, {"excerpt": "b"})
    ) == "Recuperei 2 itens da orientação anterior:"


def test_proven_field_differences_scalar_diffs_only():
    diffs = _proven_field_differences(
        [("descricao", "A"), ("tipo", "MP"), ("excerpt", "x")],
        [("descricao", "B"), ("tipo", "MP"), ("excerpt", "y")],
    )
    assert diffs == ["- Descricao: A → B"]


def test_render_synthesis_answer_mode_single_selection():
    rendered, reason = _render_synthesis(
        {
            "items": [
                {"record_index": 0, "fields": ["descricao"]},
            ],
            "presentation": "answer",
        },
        (RECORD,),
    )
    assert reason == "rendered"
    assert rendered == (
        'O campo "descricao" do registro 10080092 é: '
        'TERM. BALA 0,50-2,27MM2.'
    )


def test_render_synthesis_list_mode_two_records():
    rendered, reason = _render_synthesis(
        {
            "items": [
                {"record_index": 0, "fields": ["codigo", "descricao"]},
                {"record_index": 1, "fields": ["codigo", "descricao"]},
            ],
            "presentation": "list",
        },
        (RECORD, RECORD_B),
    )
    assert reason == "rendered"
    assert rendered == (
        "Encontrei 2 registros:\n"
        "- 10080092 — TERM. BALA 0,50-2,27MM2\n"
        "- 04/10/1008 — TERM. BALA 1,00-2,50MM2"
    )


def test_render_synthesis_rejects_invalid_selection():
    rendered, reason = _render_synthesis(
        {"items": [{"record_index": 9, "fields": ["descricao"]}]},
        (RECORD,),
    )
    assert rendered is None
    assert reason != "rendered"


def test_format_structured_filters_control_plane_and_none():
    lines = _format_structured(
        {"codigo": "10080092", "agent_directives": {"x": 1}, "vazio": None}
    )
    assert lines == ["codigo: 10080092"]


def test_format_records_numbered_bounded():
    lines = _format_records([RECORD, RECORD_B])
    assert lines[0] == "1."
    assert lines[1] == "  codigo: 10080092"
    assert lines[4] == "2."


def test_business_lines_unwraps_envelope_items():
    lines = _business_lines(
        {"data": {"items": [RECORD]}, "total": 55}
    )
    assert any("codigo: 10080092" in line for line in lines)


def test_business_lines_explicit_empty():
    assert _business_lines({"data": {"items": []}}) == [
        "Nenhum resultado encontrado."
    ]


def test_md_leaf_escapes_all_markup():
    assert _md_leaf("*bold* [x](y) `c`") == (
        "\\*bold\\* \\[x\\]\\(y\\) \\`c\\`"
    )


def test_md_business_lines_markdown_projection():
    lines = _md_business_lines({"data": {"items": [RECORD]}})
    assert any("**codigo:**" in line for line in lines)


def test_insufficiency_content_ptbr_literal():
    assert _insufficiency_content().startswith(
        "Com as evidências disponíveis não consigo responder"
    )

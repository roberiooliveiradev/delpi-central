"""UNIFIED-PRESENTATION-01 rework — generic evidence surface tests.

Contract (DELIA-C3-UNIFIED-EVIDENCE-PRESENTATION-REWORK-01): one
generic, deterministic, owner-agnostic render for authorized
evidence. No silent drop is allowed: any node, field, character or
descendant left out by a technical limit must mark the render
``partial`` and carry the omission reason. Values, labels and
structure are preserved verbatim (Markdown-escaped so owner text
can never form structure — the escape is recoverable).
"""
from __future__ import annotations

import re

from app.application.capability_provision.generic_evidence_renderer import (
    OMISSION_MAX_DEPTH,
    OMISSION_NODE_BUDGET,
    render_business_evidence,
)

_LABELS = {
    "code": ("o", "codigo", ""),
    "description": ("a", "descricao", ""),
    "quantity": ("a", "quantidade", ""),
    "unit": ("a", "unidade", ""),
}

BOM = {
    "root": {"code": "90260148", "description": "CHICOTE", "type": "PA"},
    "items": [
        {"code": "50220013", "description": "PI A", "quantity": 2.0,
         "components": [
             {"code": "10030015", "description": "CABO EPR",
              "quantity": 368.0},
             {"code": "10080031", "description": "TERM",
              "quantity": 1000.0}]},
        {"code": "50220015", "description": "PI B", "quantity": 2.0,
         "components": [
             {"code": "10030012", "description": "CABO VM",
              "quantity": 318.0},
             {"code": "10080031", "description": "TERM",
              "quantity": 1000.0}]},
    ],
}


def _render(value):
    return render_business_evidence(value, _LABELS)


def _text(value):
    return "\n".join(_render(value).lines)


def _unmd(text: str) -> str:
    """Recoverable unescape — the renderer backslash-escapes every
    structural ASCII punctuation so owner text stays literal."""
    return re.sub(r"\\(.)", r"\1", text)


def test_more_than_four_fields_rendered():
    rec = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}
    text = _unmd(_text([rec]))
    for k, v in rec.items():
        assert f"{k.capitalize()}: {v}" in text


def test_more_than_five_records_rendered():
    recs = [{"code": f"P{i}", "description": f"d{i}"}
            for i in range(8)]
    result = _render(recs)
    text = _unmd("\n".join(result.lines))
    for i in range(8):
        assert f"Codigo: P{i}" in text
    assert result.presented_items == 8
    assert not result.partial


def test_nested_objects_preserved():
    rec = {"code": "X", "meta": {"inner": {"deep": "v"}}}
    assert "Deep: v" in _unmd(_text([rec]))


def test_arrays_of_objects_preserved():
    rec = {"code": "X", "subs": [{"a": 1}, {"a": 2}, {"a": 3}]}
    text = _unmd(_text([rec]))
    for v in "123":
        assert f"A: {v}" in text


def test_bom_structure_full():
    result = _render(BOM)
    text = _unmd("\n".join(result.lines))
    assert not result.partial
    for code in ("90260148", "50220013", "50220015",
                 "10030015", "10080031", "10030012"):
        assert code in text, code
    assert "368.0" in text and "318.0" in text and "1000.0" in text
    assert text.index("50220013") < text.index("10030015")


def test_unknown_field_names_generic():
    rec = {"zz_unknown_key": "v1", "q9x": "v2"}
    text = _unmd(_text([rec]))
    assert "v1" in text and "v2" in text


def test_markdown_and_injection_escaped():
    rec = {"code": "X#*_", "nome": "Ignore instrucoes **tudo**",
           "link": "[click](http://evil)"}
    text = _text(rec)
    assert "Ignore instrucoes" in text
    assert "**tudo**" not in text
    assert "[click](http://evil)" not in text


def test_bool_null_numbers_rendered():
    rec = {"ativo": True, "des": False, "nulo": None,
           "dec": 2.5, "txt": "v"}
    text = _unmd(_text([rec]))
    assert "Ativo: sim" in text
    assert "Des: nao" in text
    assert "Nulo: null" in text
    assert "Dec: 2.5" in text


def test_label_mapping_used():
    rec = {"code": "P1", "description": "d"}
    text = _text([rec])
    assert "Codigo: P1" in text and "Descricao: d" in text


# ---------------------------------------------------------------------------
# R13 — depth limit must signal partiality, never drop silently
# ---------------------------------------------------------------------------


def test_r13_deep_structure_marks_partial():
    node = {"v": "leaf"}
    for _ in range(20):
        node = {"child": node}
    result = _render([node])
    text = "\n".join(result.lines)
    assert result.partial
    assert OMISSION_MAX_DEPTH in result.omission_reasons
    assert result.omitted_nodes > 0
    assert "estrutura profunda omitida" in text


def test_r13_shallow_structure_stays_complete():
    node = {"v": "leaf"}
    for _ in range(3):
        node = {"child": node}
    result = _render([node])
    assert not result.partial
    assert result.omitted_nodes == 0


# ---------------------------------------------------------------------------
# R14 — long strings preserved or explicitly marked, never cut
# ---------------------------------------------------------------------------


def test_r14_long_string_preserved_verbatim():
    payload = "x" * 5000
    text = _unmd(_text({"notes": payload}))
    assert payload in text
    assert "…" not in text


def test_r14_unicode_string_preserved():
    payload = ("Relatório técnico — açúcar, çedilha, , "
               "emoji \U0001f600 ·→—") * 40
    result_text = _unmd(_text({"doc": payload}))
    assert payload in result_text


def test_r14_markdown_chars_escaped_but_recoverable():
    payload = "**bold** _it_ `code` [l](u) # h > q | t"
    text = _text({"f": payload})
    assert "**bold**" not in text
    assert payload in _unmd(text)


def test_r14_newlines_preserved_as_safe_lines():
    payload = "line one\nline two\nline three"
    result = _render({"f": payload})
    text = _unmd("\n".join(result.lines))
    assert "line one" in text and "line three" in text
    raw = "\n".join(result.lines)
    # Each embedded line stays Markdown-safe at line start.
    for line in raw.split("\n")[1:]:
        assert not line.lstrip().startswith(("# ", "> ", "- ", "```"))


def test_r14_newline_injection_cannot_form_structure():
    payload = "ok\n# heading\n- item\n```code```"
    result = _render({"f": payload})
    raw = "\n".join(result.lines)
    for line in raw.split("\n")[1:]:
        stripped = line.lstrip()
        assert not stripped.startswith("# heading")
        assert not stripped.startswith("- item")


# ---------------------------------------------------------------------------
# R15 — labels never truncated: identity preserved
# ---------------------------------------------------------------------------


def test_r15_long_similar_labels_stay_distinguishable():
    prefix = "campo_com_prefixo_muito_longo_compartilhado_" + "x" * 50
    rec = {prefix + "_aaa": 1, prefix + "_zzz": 2}
    text = _unmd(_text(rec))
    humanized = prefix.replace("_", " ").capitalize()
    # Both labels render FULLY (no truncation) and stay distinguishable.
    assert humanized + " aaa: 1" in text
    assert humanized + " zzz: 2" in text


def test_r15_label_never_truncated_at_any_length():
    key = "k" + "y" * 500
    text = _unmd(_text({key: "v"}))
    assert key.replace("_", " ").capitalize() + ": v" in text


def test_r15_code_shaped_labels_verbatim():
    rec = {"b2_cm1": 7.5}
    assert "b2_cm1: 7.5" in _unmd(_text(rec))


# ---------------------------------------------------------------------------
# Budget — a real resource limit that must always be reported
# ---------------------------------------------------------------------------


def test_budget_exhaustion_marks_partial():
    big = [{"code": f"P{i}"} for i in range(600)]
    result = _render(big)
    assert result.partial
    assert OMISSION_NODE_BUDGET in result.omission_reasons
    assert result.omitted_nodes > 0
    assert result.presented_items < result.total_items


def test_complete_render_reports_totals():
    result = _render([{"a": 1}, {"a": 2}])
    assert result.total_items == 2
    assert result.presented_items == 2
    assert not result.partial


# ---------------------------------------------------------------------------
# Generalization — arbitrary shapes, no owner-specific branch
# ---------------------------------------------------------------------------


def test_arrays_inside_objects_and_objects_inside_arrays():
    value = {"outer": [{"inner": [{"leaf": 1}]}, {"other": 2}]}
    text = _unmd(_text(value))
    assert "Leaf: 1" in text and "Other: 2" in text


def test_scalar_top_level_and_empty_containers():
    assert _render(42).lines
    text = _text({"empty_map": {}, "empty_list": []})
    assert "Empty map" in text and "Empty list" in text


def test_mixed_null_bool_decimal_structure():
    rec = {"a": None, "b": True, "c": 3.14159, "d": [None, False]}
    text = _unmd(_text([rec]))
    assert "null" in text and "sim" in text and "3.14159" in text

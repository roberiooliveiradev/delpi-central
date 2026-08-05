"""Sanitizer de atas Transforma+ — regressão de tabelas e rich text."""

from __future__ import annotations

from tm_app.application.services.html_sanitizer import TmAtaHtmlSanitizer


def test_html_sanitizer_preserves_tables():
    cleaned = TmAtaHtmlSanitizer.sanitize(
        '<table class="delpi-ui-rich-text-table delpi-ui-rich-text-table--grid">'
        '<thead><tr><th colspan="2">Cabeçalho</th></tr></thead>'
        "<tbody><tr><td>A</td><td>B</td></tr></tbody>"
        "</table>"
    )
    assert "<table" in cleaned
    assert "<th" in cleaned
    assert 'colspan="2"' in cleaned
    assert "delpi-ui-rich-text-table" in cleaned
    assert "Cabeçalho" in cleaned
    assert "<td>A</td>" in cleaned
    assert "CabeçalhoA" not in cleaned.replace(" ", "")


def test_html_sanitizer_strips_script_but_keeps_table_cells():
    cleaned = TmAtaHtmlSanitizer.sanitize(
        "<table><tr><td>ok</td></tr></table><script>alert(1)</script>"
    )
    assert "<script" not in cleaned.lower()
    assert "<table" in cleaned
    assert "<td>ok</td>" in cleaned

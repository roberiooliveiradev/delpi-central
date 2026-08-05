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


def test_html_sanitizer_broken_style_does_not_swallow_table():
    """Regressão: style sem aspas de fechamento engolia <table> (texto colado)."""
    cleaned = TmAtaHtmlSanitizer.sanitize(
        '<p style="color:red><b>Antes</b></p>'
        '<table class="delpi-ui-rich-text-table"><tbody>'
        "<tr><th>Grupo</th><th>Informações</th></tr>"
        "<tr><td>Resultado</td><td>ROL</td></tr>"
        "</tbody></table>"
    )
    assert "<table" in cleaned
    assert "<th>Grupo</th>" in cleaned
    assert "GrupoInformações" not in cleaned.replace(" ", "").replace("\n", "")


def test_html_sanitizer_preserves_quoted_font_family_in_style():
    cleaned = TmAtaHtmlSanitizer.sanitize(
        "<p style=\"font-family: 'Arial'\">Texto</p>"
        "<span style='color: #f00'>Vermelho</span>"
    )
    assert "font-family: 'Arial'" in cleaned or "font-family: Arial" in cleaned
    assert "color: #f00" in cleaned

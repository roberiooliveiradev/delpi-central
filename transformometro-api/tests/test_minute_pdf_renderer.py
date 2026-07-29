"""Regressão do PDF de ata Transforma+ — HTML do rich-text → ReportLab."""

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

from tm_app.infrastructure.pdf.minute_pdf_renderer import (
    MinutePdfRenderer,
    html_to_reportlab_chunks,
    _paragraphs,
)


def test_html_chunks_normalize_br_and_skip_empty_para_br():
    """Editor TipTap/Quill gera <p><br></p>; ReportLab exige <br/> e rejeita <br>."""
    chunks = html_to_reportlab_chunks(
        "<p><br></p><p>Decisão aprovada.</p><p><br/></p><p>Linha com<br>quebra</p>"
    )
    assert chunks == ["Decisão aprovada.", "Linha com<br/>quebra"]


def test_html_chunks_lists_become_bullet_lines():
    chunks = html_to_reportlab_chunks(
        "<ul><li>Primeiro</li><li><strong>Segundo</strong></li></ul>"
    )
    assert chunks[0] == "• Primeiro"
    assert chunks[1] == "• <b>Segundo</b>"


def test_paragraphs_build_reportlab_flowables_for_editor_br():
    style = getSampleStyleSheet()["BodyText"]
    blocks = _paragraphs("<p><br></p><p>Texto útil <em>aqui</em>.</p>", style)
    assert len(blocks) == 1
    assert isinstance(blocks[0], Paragraph)


def test_renderer_finalize_html_with_bare_br_does_not_raise():
    """Caso que gerava 400 no POST …/finalize (Parse error </br>)."""
    raw = MinutePdfRenderer().render(
        {
            "minute_number": "2026/001",
            "validation_code": "TEST-BR",
        },
        {
            "meeting_date": "2026-07-28",
            "agenda_html": "<p><br></p>",
            "body_html": "<p>Andamento da reunião.</p><p><br></p>",
            "decisions_html": "<p>Aprovado<br>com ressalvas</p>",
            "pending_html": "<ul><li>Item A</li></ul>",
            "observations_html": "<p></p>",
            "content_hash": "hash-test",
        },
        [],
        [{"user_id": "u1", "display_name": "Maria"}],
        [],
    )
    assert raw.startswith(b"%PDF-")
    assert len(raw) > 500

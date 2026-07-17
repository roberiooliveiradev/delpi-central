from reportlab.lib.units import mm

from cipa_app.infrastructure.pdf.minute_pdf_renderer import (
    MinutePdfRenderer,
    format_date_br,
    format_date_long_pt,
    html_to_paragraphs,
    role_label,
)


def test_document_formatters_are_locale_independent():
    assert format_date_br("2026-04-28") == "28/04/2026"
    assert format_date_long_pt("2026-04-28") == "28 de abril de 2026"
    assert role_label("vice_president") == "Vice-presidente da CIPA"


def test_renderer_builds_formal_pdf_with_participants_and_signers():
    renderer = MinutePdfRenderer()
    raw = renderer.render(
        {
            "id": "minute-1",
            "unit_code": "01",
            "minute_number": "2026/001",
            "meeting_type": "extraordinária",
            "meeting_date": "2026-04-28",
            "start_time": "15:30",
            "end_time": "16:04",
            "location": "Sala da CIPA",
            "validation_code": "VALIDA-123",
        },
        {
            "version_number": 1,
            "meeting_date": "2026-04-28",
            "body_html": (
                "<p>A reunião teve como pauta <strong>segurança</strong>.</p>"
                "<ul><li>Primeira decisão</li></ul>"
            ),
            "content_hash": "abc123",
        },
        [
            {
                "user_id": "user-1",
                "display_name": "Pessoa CIPA",
                "role_in_meeting": "president",
            }
        ],
        [{"user_id": "user-1", "display_name": "Pessoa CIPA", "sign_order": 1}],
        [],
    )

    assert raw.startswith(b"%PDF-")
    assert len(raw) > 3_000


def test_pdf_preserves_rich_text_formatting():
    renderer = MinutePdfRenderer()
    styles = renderer._styles()
    blocks = html_to_paragraphs(
        '<p style="text-align:center">'
        '<span style="color:#ff0000;background-color:#ffff00;'
        'font-size:20px;font-family:Arial"><strong>A</strong></span> '
        '<em>B</em> <u>C</u> <strike>D</strike></p>'
        "<ol><li>Primeiro</li><li>Segundo</li></ol>",
        styles["body"],
        styles["bullet"],
    )

    paragraph = blocks[0]
    assert paragraph.style.alignment == 1  # TA_CENTER
    formatted = paragraph.frags[0]
    assert formatted.fontName == "Helvetica-Bold"
    assert formatted.fontSize == 15
    assert formatted.textColor.red == 1
    assert formatted.backColor.green == 1
    assert blocks[1].bulletText == "1."
    assert blocks[2].bulletText == "2."
    assert blocks[1].style.leftIndent == 5 * mm
    assert blocks[1].style.firstLineIndent == -2.5 * mm


def test_pdf_story_does_not_inject_intro_or_closing_text():
    renderer = MinutePdfRenderer()
    styles = renderer._styles()
    story = renderer._story(
        {
            "unit_code": "01",
            "meeting_number": "1",
            "meeting_date": "2026-05-16",
        },
        {
            "meeting_date": "2026-05-16",
            "body_html": "<p>Texto escrito pelo usuário.</p>",
        },
        [{"display_name": "Pessoa CIPA"}],
        [],
        [],
        styles,
    )
    texts = " ".join(str(getattr(item, "text", "")) for item in story)
    assert "Texto escrito pelo usuário." in texts
    assert "realizou-se reunião" not in texts
    assert "DELPI Conexões Elétricas, 16 de maio" not in texts

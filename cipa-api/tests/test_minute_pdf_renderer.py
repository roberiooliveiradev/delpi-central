import io

from PIL import Image as PillowImage
from reportlab.lib.units import mm
from reportlab.platypus import Table

from cipa_app.infrastructure.pdf.minute_pdf_renderer import (
    MinutePdfRenderer,
    _transparent_signature_png,
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


def test_signature_blocks_use_two_columns():
    renderer = MinutePdfRenderer()
    styles = renderer._styles()
    participants = [
        {"user_id": f"user-{index}", "display_name": f"Pessoa {index}"}
        for index in range(1, 4)
    ]
    signers = [
        {"user_id": f"user-{index}", "display_name": f"Pessoa {index}"}
        for index in range(1, 4)
    ]

    blocks = renderer._signature_blocks(participants, signers, [], styles)

    assert len(blocks) == 1
    assert isinstance(blocks[0], Table)
    assert len(blocks[0]._cellvalues) == 2
    assert all(len(row) == 2 for row in blocks[0]._cellvalues)


def test_signature_background_becomes_transparent():
    image = PillowImage.new("RGBA", (3, 1), (255, 255, 255, 255))
    image.putpixel((1, 0), (15, 23, 42, 255))
    image.putpixel((2, 0), (250, 250, 250, 255))
    raw = io.BytesIO()
    image.save(raw, format="PNG")

    normalized = PillowImage.open(
        io.BytesIO(_transparent_signature_png(raw.getvalue()))
    ).convert("RGBA")

    assert normalized.getpixel((0, 0))[3] == 0
    assert normalized.getpixel((1, 0))[3] == 255
    assert normalized.getpixel((2, 0))[3] == 0


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


def test_pdf_indents_first_line_of_prose_paragraphs_only():
    """Paridade com o espelho web: <p> de prosa com recuo; títulos, divs e listas sem."""
    renderer = MinutePdfRenderer()
    styles = renderer._styles()
    blocks = html_to_paragraphs(
        "<p>Parágrafo de prosa da ata.</p>"
        "<h2>Encaminhamentos</h2>"
        "<div>Linha avulsa.</div>"
        "<ul><li>Item de lista</li></ul>",
        styles["body"],
        styles["bullet"],
    )

    prose, heading, line, bullet = blocks
    assert prose.style.firstLineIndent == 12 * mm
    assert heading.style.firstLineIndent == 0
    assert line.style.firstLineIndent == 0
    assert bullet.style.firstLineIndent == -2.5 * mm


def test_pdf_collapses_word_nbsp_runs_in_saved_content():
    renderer = MinutePdfRenderer()
    styles = renderer._styles()
    blocks = html_to_paragraphs(
        "<p>1.<span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </span>"
        "Desenvolver ferramenta digital</p>",
        styles["body"],
        styles["bullet"],
    )
    text = blocks[0].text
    assert "\u00a0\u00a0" not in text
    assert "&nbsp;&nbsp;" not in text
    assert "Desenvolver ferramenta digital" in text


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

from cipa_app.infrastructure.pdf.minute_pdf_renderer import (
    MinutePdfRenderer,
    format_date_br,
    format_date_long_pt,
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

"""Outbound inline images must match native GLPI paste HTML shape."""

from helpdesk_app.application.services.message_html_sanitizer import (
    prepare_outbound_message_html,
)


def test_outbound_followup_wraps_img_like_native_glpi_paste():
    raw = (
        '<p>foto</p><p><img src="/apps/helpdesk-api/tickets/1588/attachments/1584" '
        'alt="Imagem de aceite" width="1440" /></p>'
    )
    out = prepare_outbound_message_html(
        raw, ticket_id=1588, allowed_document_ids={1584}
    )
    assert 'target="_blank"' in out
    assert "itemtype=Ticket" in out
    assert "items_id=1588" in out
    assert 'docid=1584&amp;itemtype=Ticket&amp;items_id=1588' in out
    assert out.count("<a href=") == 1
    assert out.count("<img") == 1
    assert 'alt="Imagem de aceite"' in out
    assert 'width="1440"' in out
    # Anchor wraps the img (native paste order).
    a_open = out.index("<a href=")
    img = out.index("<img")
    a_close = out.index("</a>")
    assert a_open < img < a_close


def test_outbound_preserves_text_order_around_native_wrap():
    raw = (
        '<p>antes</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/2" '
        'alt="logo" /></p><p>depois</p>'
    )
    out = prepare_outbound_message_html(
        raw, ticket_id=7, allowed_document_ids={2}
    )
    assert out.index("antes") < out.index("docid=2") < out.index("depois")
    assert "itemtype=Ticket" in out and "items_id=7" in out


def test_outbound_create_without_ticket_keeps_images_stripped():
    """ticket_id=0 (create) still strips every image — no native wrap path."""
    raw = (
        '<p>x</p><p><img src="/apps/helpdesk-api/tickets/7/attachments/2" '
        'alt="x" /></p>'
    )
    out = prepare_outbound_message_html(raw, ticket_id=0, allowed_document_ids={2})
    assert "img" not in out.lower()
    assert "document.send.php" not in out

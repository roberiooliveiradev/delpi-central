"""M-23 — sanitizer preserves / strips GLPI user-mention spans."""

from helpdesk_app.application.services.message_html_sanitizer import (
    prepare_outbound_message_html,
)


def test_outbound_preserves_numeric_user_mention_span():
    raw = (
        '<p>Oi <span data-user-mention="true" data-user-id="69" '
        'class="delpi-ui-mention-text__chip" contenteditable="false">@Ana</span></p>'
    )
    cleaned = prepare_outbound_message_html(raw)
    assert 'data-user-id="69"' in cleaned
    assert 'data-user-mention="true"' in cleaned
    assert "@Ana" in cleaned
    assert "contenteditable" not in cleaned.lower()


def test_outbound_strips_non_numeric_user_id():
    raw = '<p><span data-user-mention="true" data-user-id="abc">@X</span></p>'
    cleaned = prepare_outbound_message_html(raw)
    assert "data-user-id" not in cleaned


def test_sibling_mentions_keep_distinct_ids():
    raw = (
        "<p>"
        '<span data-user-mention="true" data-user-id="10">@Ana A</span> '
        '<span data-user-mention="true" data-user-id="20">@Ana B</span>'
        "</p>"
    )
    cleaned = prepare_outbound_message_html(raw)
    assert 'data-user-id="10"' in cleaned
    assert 'data-user-id="20"' in cleaned

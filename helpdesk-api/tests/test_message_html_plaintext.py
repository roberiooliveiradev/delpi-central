"""Plain-text GLPI bodies keep their line structure after sanitization."""

from helpdesk_app.application.services.message_html_sanitizer import (
    message_html_has_visible_text,
    sanitize_message_html,
)


def test_plain_text_newlines_become_paragraphs_and_breaks():
    raw = "Linha um\nLinha dois\n\nSegundo bloco"
    cleaned = sanitize_message_html(raw, ticket_id=660, allowed_document_ids=set())
    assert "<p>Linha um<br>Linha dois</p>" in cleaned or "<p>Linha um<br/>Linha dois</p>" in cleaned
    assert "<p>Segundo bloco</p>" in cleaned


def test_entity_encoded_plain_text_is_decoded_once():
    raw = "Resultado: 3 &gt; 2 &amp; ok"
    cleaned = sanitize_message_html(raw, ticket_id=660, allowed_document_ids=set())
    assert "3 &gt; 2 &amp; ok" in cleaned
    assert "&amp;gt;" not in cleaned


def test_literal_markup_in_plain_text_stays_literal():
    """Entity-encoded tags decode to text, never to live markup."""
    raw = "Digite &lt;script&gt;alert(1)&lt;/script&gt; no console"
    cleaned = sanitize_message_html(raw, ticket_id=660, allowed_document_ids=set())
    assert "<script" not in cleaned.lower()
    assert "&lt;script&gt;" in cleaned


def test_real_html_body_is_not_rewrapped():
    raw = "<p>Primeiro</p><ul><li>Um</li></ul>"
    cleaned = sanitize_message_html(raw, ticket_id=660, allowed_document_ids=set())
    assert cleaned == raw


def test_plain_text_with_angle_bracket_math_is_preserved():
    raw = "Regra: a < b e c > d"
    cleaned = sanitize_message_html(raw, ticket_id=660, allowed_document_ids=set())
    assert "a &lt; b e c &gt; d" in cleaned


def test_plain_text_result_has_visible_text():
    cleaned = sanitize_message_html("Só texto", ticket_id=1, allowed_document_ids=set())
    assert message_html_has_visible_text(cleaned) is True


def test_html_with_dangerous_block_still_stripped():
    raw = "<p>ok</p><script>alert(1)</script>"
    cleaned = sanitize_message_html(raw, ticket_id=1, allowed_document_ids=set())
    assert "script" not in cleaned.lower()
    assert "ok" in cleaned

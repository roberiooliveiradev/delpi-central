"""Plain-text GLPI bodies keep their line structure after sanitization."""

from helpdesk_app.application.services.message_html_sanitizer import (
    message_html_has_visible_text,
    message_html_to_plain_text,
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


def test_message_html_to_plain_text_paragraphs_and_breaks():
    raw = "<p>Primeiro parágrafo</p><p>Segundo<br>linha dois</p>"
    assert message_html_to_plain_text(raw) == "Primeiro parágrafo\n\nSegundo\nlinha dois"


def test_message_html_to_plain_text_lists_and_links():
    raw = '<ul><li>Um</li><li>Dois</li></ul><p>Veja <a href="https://x.dev">link</a></p>'
    plain = message_html_to_plain_text(raw)
    assert "- Um" in plain
    assert "- Dois" in plain
    assert "Veja link" in plain
    assert "<" not in plain and ">" not in plain


def test_message_html_to_plain_text_entities_and_nbsp():
    assert message_html_to_plain_text("<p>a &amp; b&nbsp;c</p>") == "a & b c"


def test_message_html_to_plain_text_empty_markup_is_empty():
    assert message_html_to_plain_text("<p></p>") == ""
    assert message_html_to_plain_text("<br>") == ""
    assert message_html_to_plain_text("   ") == ""


def test_message_html_to_plain_text_plain_passthrough():
    """Input without markup is returned untouched (plain-text clients)."""
    raw = "Linha 1\nLinha 2 com < e > literais"
    assert message_html_to_plain_text(raw) == raw

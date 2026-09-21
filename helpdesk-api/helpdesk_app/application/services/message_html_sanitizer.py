"""Allowlist HTML for helpdesk message bodies (BFF is the authority).

Contract: docs/12-roadmap-e-evolucao/helpdesk/12-conteudo-da-mensagem.md §7.
"""

from __future__ import annotations

import base64
import html as html_lib
import re
from collections.abc import Collection

import bleach

_API_PREFIX = "/apps/helpdesk-api"

# M-29 — teto do HTML na escrita (create/followup). Caracteres do payload cru.
MAX_MESSAGE_HTML_CHARS = 50_000

ALLOWED_TAGS: list[str] = [
    "p",
    "div",
    "br",
    "hr",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "strike",
    "del",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "pre",
    "code",
    "table",
    "thead",
    "tbody",
    "tfoot",
    "tr",
    "th",
    "td",
    "a",
    "img",
    "span",
]

_COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgba?\([\d\s.,%]+\)|[a-zA-Z]+)$")
_SIZE_RE = re.compile(r"^\d{1,3}(\.\d+)?(px|em|rem)$", re.IGNORECASE)
_ALIGN_RE = re.compile(r"^(left|right|center|justify)$", re.IGNORECASE)
_FONT_RE = re.compile(r"^[\w\s,\"'\-]+$")
_ALLOWED_CSS: dict[str, re.Pattern[str]] = {
    "text-align": _ALIGN_RE,
    "color": _COLOR_RE,
    "background-color": _COLOR_RE,
    "font-size": _SIZE_RE,
    "font-family": _FONT_RE,
}
_DANGEROUS_CSS = ("url(", "expression", "javascript:", "position", "/*", "*/", "<", ">", "{", "}")

_DOC_SEND_RE = re.compile(
    r"""(?ix)
    (?:https?://[^/"'\s<>]+)?
    /front/document\.send\.php
    \?
    [^"'>\s]*?
    \bdocid=(\d+)
    [^"'>\s]*
    """
)
_STYLE_ATTR_RE = re.compile(
    r"""\sstyle\s*=\s*(?:\"([^\"<>]*)\"|'([^'<>]*)')""",
    re.IGNORECASE,
)
_DSTY_ATTR_RE = re.compile(r'\sdata-dsty\s*=\s*"([A-Za-z0-9+/=]*)"')
_DANGEROUS_BLOCK_RE = re.compile(
    r"<(script|style|iframe|object|embed|form|textarea)\b[^>]*>[\s\S]*?</\1\s*>",
    re.IGNORECASE,
)
_DANGEROUS_SELF_CLOSING_RE = re.compile(
    r"<(script|style|iframe|object|embed|form|textarea|link|meta|base|svg|math|video|audio|input|button)\b[^>]*/?>",
    re.IGNORECASE,
)
_EMPTY_IMG_RE = re.compile(
    r"""(?is)<img\b(?=[^>]*\bsrc\s*=\s*(?:""|''))[^>]*/?>"""
)
_EMPTY_ANCHOR_RE = re.compile(
    r"""(?is)<a\b(?=[^>]*\bhref\s*=\s*(?:""|''))[^>]*>(.*?)</a>"""
)
_HREFLESS_ANCHOR_RE = re.compile(r"(?is)<a\b(?![^>]*\bhref\s*=)[^>]*>(.*?)</a>")
_FOREIGN_IMG_RE = re.compile(
    r"""(?is)<img\b(?![^>]*\bsrc\s*=\s*[\"']/apps/helpdesk-api/tickets/)[^>]*/?>"""
)
_FOREIGN_DOC_ANCHOR_RE = re.compile(
    r"""(?is)<a\b[^>]*\bhref\s*=\s*[\"'][^\"']*document\.send\.php[^\"']*[\"'][^>]*>(.*?)</a>"""
)


def attachment_public_path(ticket_id: int, document_id: int) -> str:
    return f"{_API_PREFIX}/tickets/{int(ticket_id)}/attachments/{int(document_id)}"


def sanitize_message_html(
    raw_html: str | None,
    *,
    ticket_id: int,
    allowed_document_ids: Collection[int],
) -> str:
    text = str(raw_html or "")
    if not text.strip():
        return ""
    allowed = {int(item) for item in allowed_document_ids}
    text = _DANGEROUS_BLOCK_RE.sub("", text)
    text = _DANGEROUS_SELF_CLOSING_RE.sub("", text)
    text = _rewrite_document_urls(text, ticket_id=ticket_id, allowed_document_ids=allowed)
    text = _FOREIGN_DOC_ANCHOR_RE.sub(r"\1", text)
    text = _FOREIGN_IMG_RE.sub("", text)
    text = _encode_styles(text)
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=_attribute_filter,
        protocols=["http", "https", "mailto"],
        strip=True,
    )
    cleaned = _decode_styles(cleaned)
    cleaned = _EMPTY_IMG_RE.sub("", cleaned)
    cleaned = _EMPTY_ANCHOR_RE.sub(r"\1", cleaned)
    cleaned = _HREFLESS_ANCHOR_RE.sub(r"\1", cleaned)
    return cleaned.strip()


_TAG_RE = re.compile(r"<[^>]+>")


def message_html_has_visible_text(html: str) -> bool:
    plain = html_lib.unescape(_TAG_RE.sub(" ", html or ""))
    return bool(plain.strip())


def prepare_outbound_message_html(raw_html: str | None) -> str:
    """Sanitize HTML for create/followup before sending to GLPI.

    Write path has no ticket attachments yet for new tickets, and follow-ups
    must not invent document links — so document_ids are empty and foreign
    imgs are stripped (no paste-image / upload in the compositor).
    """
    text = str(raw_html or "")
    if not text.strip():
        return ""
    cleaned = sanitize_message_html(text, ticket_id=0, allowed_document_ids=())
    if not message_html_has_visible_text(cleaned):
        return ""
    return cleaned


def _rewrite_document_urls(
    html: str,
    *,
    ticket_id: int,
    allowed_document_ids: set[int],
) -> str:
    def _repl(match: re.Match[str]) -> str:
        doc_id = int(match.group(1))
        if doc_id not in allowed_document_ids:
            return ""
        return attachment_public_path(ticket_id, doc_id)

    return _DOC_SEND_RE.sub(_repl, html)


def _is_dangerous_url(url: str) -> bool:
    lowered = (url or "").strip().lower()
    if not lowered:
        return True
    return lowered.startswith(("javascript:", "data:", "blob:", "vbscript:"))


def _filter_css(raw_style: str) -> str:
    kept: list[str] = []
    for chunk in raw_style.split(";"):
        if ":" not in chunk:
            continue
        name, value = chunk.split(":", 1)
        prop = name.strip().lower()
        val = value.strip()
        validator = _ALLOWED_CSS.get(prop)
        if not validator or not val:
            continue
        lowered = val.lower()
        if any(token in lowered for token in _DANGEROUS_CSS):
            continue
        if not validator.match(val):
            continue
        kept.append(f"{prop}: {val}")
    return "; ".join(kept)


def _encode_styles(html: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        raw_style = match.group(1) if match.group(1) is not None else match.group(2) or ""
        filtered = _filter_css(raw_style)
        if not filtered:
            return ""
        token = base64.b64encode(filtered.encode("utf-8")).decode("ascii")
        return f' data-dsty="{token}"'

    return _STYLE_ATTR_RE.sub(_repl, html)


def _decode_styles(html: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        token = match.group(1)
        if not token:
            return ""
        try:
            style = base64.b64decode(token).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return ""
        style = _filter_css(style)
        return f' style="{style}"' if style else ""

    return _DSTY_ATTR_RE.sub(_repl, html)


def _attribute_filter(tag: str, name: str, value: str) -> bool:
    name = name.lower()
    if name.startswith("on") or name in {"srcdoc", "formaction"}:
        return False
    if name == "style":
        return tag in ALLOWED_TAGS
    if name == "data-dsty":
        return True
    if tag == "a" and name in {"href", "rel", "target", "title"}:
        if name == "href":
            if _is_dangerous_url(value):
                return False
            if value.startswith(f"{_API_PREFIX}/tickets/") and "/attachments/" in value:
                return True
            return value.lower().startswith(("http://", "https://", "mailto:", "/"))
        if name == "target":
            return value == "_blank"
        if name == "rel":
            return "noopener" in value.lower()
        return True
    if tag == "img" and name in {"src", "alt", "width", "height"}:
        if name == "src":
            return value.startswith(f"{_API_PREFIX}/tickets/") and "/attachments/" in value
        if name in {"width", "height"}:
            return value.isdigit() and int(value) <= 4096
        return True
    if tag == "span" and name in {"data-user-mention", "data-user-id", "class"}:
        if name == "data-user-id":
            return value.isdigit()
        if name == "data-user-mention":
            return value.lower() in {"true", "1"}
        return True
    if tag in {"th", "td"} and name in {"colspan", "rowspan"}:
        return value.isdigit() and int(value) <= 50
    return False

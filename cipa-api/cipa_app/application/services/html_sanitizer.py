"""Sanitização HTML allowlist para conteúdo de atas CIPA."""

from __future__ import annotations

import re

import bleach

ALLOWED_HTML_TAGS: list[str] = [
    "h1",
    "h2",
    "h3",
    "h4",
    "p",
    "br",
    "strong",
    "em",
    "u",
    "b",
    "i",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "div",
    "span",
]

ALLOWED_HTML_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "target", "rel"],
    "div": ["class"],
    "p": ["class"],
    "h1": ["class"],
    "h2": ["class"],
    "h3": ["class"],
    "h4": ["class"],
    "span": ["class"],
}

ALLOWED_HTML_PROTOCOLS: list[str] = ["http", "https", "mailto"]

_DANGEROUS_BLOCK_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b[^>]*>[\s\S]*?</\1\s*>",
    re.IGNORECASE,
)
_DANGEROUS_SELF_CLOSING_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b[^>]*/?>",
    re.IGNORECASE,
)
_STYLE_ATTR_RE = re.compile(r"style\s*=\s*([\"']).*?\1", re.IGNORECASE | re.DOTALL)


def _strip_unsafe_styles(html: str) -> str:
    """Mantém apenas text-align em style inline."""

    def _filter_style(match: re.Match[str]) -> str:
        raw = match.group(0)
        value_match = re.search(r"style\s*=\s*[\"']([^\"']*)[\"']", raw, re.IGNORECASE)
        if not value_match:
            return ""
        parts = []
        for chunk in value_match.group(1).split(";"):
            prop = chunk.strip().lower()
            if prop.startswith("text-align:"):
                align = prop.split(":", 1)[1].strip()
                if align in {"left", "right", "center", "justify"}:
                    parts.append(f"text-align: {align}")
        if not parts:
            return ""
        return f'style="{"; ".join(parts)}"'

    return _STYLE_ATTR_RE.sub(_filter_style, html)


class CipaHtmlSanitizer:
    @classmethod
    def sanitize(cls, raw_html: str | None) -> str:
        text = raw_html or ""
        text = _DANGEROUS_BLOCK_RE.sub("", text)
        text = _DANGEROUS_SELF_CLOSING_RE.sub("", text)
        cleaned = bleach.clean(
            text,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            protocols=ALLOWED_HTML_PROTOCOLS,
            strip=True,
        )
        return _strip_unsafe_styles(cleaned)

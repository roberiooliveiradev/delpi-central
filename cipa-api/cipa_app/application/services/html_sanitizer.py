"""Sanitização HTML allowlist para conteúdo de atas CIPA.

Preserva a formatação de rich text (negrito, itálico, sublinhado, tachado,
cor, realce, tamanho e família de fonte, alinhamento, listas e links) sem
depender de `tinycss2`/`bleach[css]`: os estilos inline são filtrados por um
allowlist próprio e transportados por um atributo `data-dsty` (base64) através
do bleach, sendo restaurados como `style` logo em seguida.
"""

from __future__ import annotations

import base64
import re

import bleach

ALLOWED_HTML_TAGS: list[str] = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "br",
    "strong",
    "em",
    "u",
    "b",
    "i",
    "s",
    "strike",
    "del",
    "ins",
    "sub",
    "sup",
    "mark",
    "ul",
    "ol",
    "li",
    "blockquote",
    "a",
    "div",
    "span",
    "font",
]

ALLOWED_HTML_ATTRIBUTES: dict[str, list[str]] = {
    "*": ["class", "data-dsty"],
    "a": ["href", "title", "target", "rel", "class", "data-dsty"],
    "font": ["color", "face", "size", "data-dsty"],
    "ol": ["start", "type", "class", "data-dsty"],
    "li": ["value", "class", "data-dsty"],
}

ALLOWED_HTML_PROTOCOLS: list[str] = ["http", "https", "mailto"]

# Propriedades CSS inline preservadas (nome → validador do valor).
_COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{3,8}|rgba?\([\d\s.,%]+\)|[a-zA-Z]+)$")
_ALLOWED_CSS_PROPERTIES: dict[str, re.Pattern[str]] = {
    "text-align": re.compile(r"^(left|right|center|justify)$", re.IGNORECASE),
    "color": _COLOR_RE,
    "background-color": _COLOR_RE,
    "background": _COLOR_RE,
    "font-size": re.compile(r"^\d{1,3}(\.\d+)?(px|pt|em|rem|%)$", re.IGNORECASE),
    "font-family": re.compile(r"^[\w\s,\"'\-]+$"),
    "font-weight": re.compile(r"^(normal|bold|bolder|lighter|[1-9]00)$", re.IGNORECASE),
    "font-style": re.compile(r"^(normal|italic|oblique)$", re.IGNORECASE),
    "text-decoration": re.compile(r"^[a-zA-Z\s\-]+$"),
    "text-decoration-line": re.compile(r"^[a-zA-Z\s\-]+$"),
}
_DANGEROUS_TOKENS = ("url(", "expression", "javascript:", "/*", "*/", "<", ">", "{", "}", "@")

_DANGEROUS_BLOCK_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b[^>]*>[\s\S]*?</\1\s*>",
    re.IGNORECASE,
)
_DANGEROUS_SELF_CLOSING_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b[^>]*/?>",
    re.IGNORECASE,
)
_STYLE_ATTR_RE = re.compile(r"""\sstyle\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL)
_DSTY_ATTR_RE = re.compile(r'\sdata-dsty\s*=\s*"([A-Za-z0-9+/=]*)"')


def _filter_css(raw_style: str) -> str:
    """Mantém apenas propriedades do allowlist com valores seguros."""
    kept: list[str] = []
    for chunk in raw_style.split(";"):
        if ":" not in chunk:
            continue
        name, value = chunk.split(":", 1)
        prop = name.strip().lower()
        val = value.strip()
        validator = _ALLOWED_CSS_PROPERTIES.get(prop)
        if not validator or not val:
            continue
        lowered = val.lower()
        if any(token in lowered for token in _DANGEROUS_TOKENS):
            continue
        if not validator.match(val):
            continue
        kept.append(f"{prop}: {val}")
    return "; ".join(kept)


def _encode_styles(html: str) -> str:
    """Substitui `style` filtrado por `data-dsty` (base64) para atravessar o bleach."""

    def _repl(match: re.Match[str]) -> str:
        filtered = _filter_css(match.group(2))
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
        # Valor já filtrado (sem aspas duplas); re-filtra por segurança.
        style = _filter_css(style)
        return f' style="{style}"' if style else ""

    return _DSTY_ATTR_RE.sub(_repl, html)


class CipaHtmlSanitizer:
    @classmethod
    def sanitize(cls, raw_html: str | None) -> str:
        text = raw_html or ""
        text = _DANGEROUS_BLOCK_RE.sub("", text)
        text = _DANGEROUS_SELF_CLOSING_RE.sub("", text)
        text = _encode_styles(text)
        cleaned = bleach.clean(
            text,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            protocols=ALLOWED_HTML_PROTOCOLS,
            strip=True,
        )
        return _decode_styles(cleaned)

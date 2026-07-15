"""Sanitização HTML allowlist para artigos de Guias e Procedimentos."""

from __future__ import annotations

import re

import bleach

ALLOWED_HTML_TAGS: list[str] = [
    "h2",
    "h3",
    "h4",
    "h5",
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "ul",
    "ol",
    "li",
    "blockquote",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "a",
    "div",
    "span",
    "figure",
    "figcaption",
    "img",
    "video",
]

ALLOWED_HTML_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "target", "rel", "class"],
    "th": ["colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
    "div": ["class"],
    "span": ["class"],
    "p": ["class"],
    "figure": ["class"],
    "figcaption": ["class"],
    "img": ["src", "alt", "title", "class", "loading"],
    "video": ["src", "controls", "preload", "playsinline", "class", "title"],
}

ALLOWED_HTML_PROTOCOLS: list[str] = ["http", "https", "mailto"]

ALLOWED_HTML_CLASSES: frozenset[str] = frozenset(
    {
        "gp-callout",
        "gp-emphasis",
        "guide-media",
        "guide-media--image",
        "guide-media--video",
        "guide-media--video-external",
        "guide-media__link",
        "guide-attachment",
        "guide-attachment__link",
    }
)

# src de mídia protegida (caminho relativo do gateway / API).
_PROTECTED_MEDIA_SRC_RE = re.compile(
    r"^/(?:apps/api-delpi/)?guias-procedimentos/media/[0-9a-fA-F-]{36}/file$"
)
_PROTECTED_ATTACHMENT_HREF_RE = re.compile(
    r"^/(?:apps/api-delpi/)?guias-procedimentos/attachments/[0-9a-fA-F-]{36}/file$"
)

_DANGEROUS_BLOCK_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b[^>]*>[\s\S]*?</\1\s*>",
    re.IGNORECASE,
)
_DANGEROUS_SELF_CLOSING_RE = re.compile(
    r"<(script|style|iframe|object|embed|form)\b[^>]*/\s*>",
    re.IGNORECASE,
)


class GuideHtmlSanitizer:
    """Sanitiza HTML editorial antes da persistência (e reutilizável no admin)."""

    @classmethod
    def sanitize(cls, raw_html: str | None) -> str:
        if raw_html is None:
            return ""
        if not isinstance(raw_html, str):
            raise TypeError("content_html deve ser string")

        pre_stripped = _DANGEROUS_BLOCK_RE.sub("", raw_html)
        pre_stripped = _DANGEROUS_SELF_CLOSING_RE.sub("", pre_stripped)

        cleaned = bleach.clean(
            pre_stripped,
            tags=ALLOWED_HTML_TAGS,
            attributes=cls._attributes_filter,
            protocols=ALLOWED_HTML_PROTOCOLS,
            strip=True,
        )
        return cls._drop_media_without_protected_src(cleaned).strip()

    @staticmethod
    def _drop_media_without_protected_src(html: str) -> str:
        """Remove img/video cujo src não passou no filtro (bleach mantém a tag)."""

        def _keep(match: re.Match[str]) -> str:
            tag_html = match.group(0)
            src_match = re.search(
                r'\bsrc\s*=\s*([\'"])(.*?)\1',
                tag_html,
                flags=re.IGNORECASE,
            )
            if not src_match:
                return ""
            src = src_match.group(2).strip()
            if _PROTECTED_MEDIA_SRC_RE.match(src):
                return tag_html
            return ""

        without_img = re.sub(
            r"<img\b[^>]*/?>",
            _keep,
            html,
            flags=re.IGNORECASE,
        )
        return re.sub(
            r"<video\b[^>]*>[\s\S]*?</video\s*>|<video\b[^>]*/?>",
            _keep,
            without_img,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _attributes_filter(
        tag: str,
        name: str,
        value: str,
    ) -> bool:
        allowed = ALLOWED_HTML_ATTRIBUTES.get(tag, [])
        if name not in allowed:
            return False
        if name == "href":
            lowered = (value or "").strip().lower()
            if lowered.startswith("javascript:"):
                return False
            if tag == "a" and _PROTECTED_ATTACHMENT_HREF_RE.match((value or "").strip()):
                return True
        if name == "src":
            raw = (value or "").strip()
            lowered = raw.lower()
            if lowered.startswith("javascript:") or lowered.startswith("data:"):
                return False
            if tag == "img":
                return bool(_PROTECTED_MEDIA_SRC_RE.match(raw))
            if tag == "video":
                return bool(_PROTECTED_MEDIA_SRC_RE.match(raw))
            return False
        if name == "class":
            classes = [part.strip() for part in (value or "").split() if part.strip()]
            if not classes:
                return False
            return all(part in ALLOWED_HTML_CLASSES for part in classes)
        if name == "target":
            return value in {"_blank", "_self"}
        if name == "controls":
            return True
        if name == "playsinline":
            return True
        if name == "preload":
            return value in {"none", "metadata", "auto"}
        if name == "loading":
            return value in {"lazy", "eager"}
        return True

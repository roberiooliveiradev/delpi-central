"""Redact secrets from Protheus integration strings before logging/errors."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SENSITIVE_QUERY_KEYS = {"password", "username", "refresh_token", "access_token"}
_BEARER_RE = re.compile(r"(?i)(bearer\s+)[^\s]+")
_PASSWORD_RE = re.compile(r"(?i)(password=)[^&\s]+")
_TOKEN_JSON_RE = re.compile(
    r'(?i)("(?:access_token|refresh_token)"\s*:\s*")[^"]+(")'
)


def redact_url(url: str) -> str:
    """Strip credentials from query string; keep scheme/host/path for diagnosis."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return "[redacted-url]"
    query_pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in _SENSITIVE_QUERY_KEYS:
            query_pairs.append((key, "***"))
        else:
            query_pairs.append((key, value))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query_pairs), parts.fragment)
    )


def redact_text(text: str) -> str:
    if not text:
        return text
    result = _PASSWORD_RE.sub(r"\1***", text)
    result = _BEARER_RE.sub(r"\1***", result)
    result = _TOKEN_JSON_RE.sub(r"\1***\2", result)
    if "://" in result and ("password=" in result.lower() or "username=" in result.lower()):
        for token in result.split():
            if "://" in token:
                result = result.replace(token, redact_url(token))
    return result

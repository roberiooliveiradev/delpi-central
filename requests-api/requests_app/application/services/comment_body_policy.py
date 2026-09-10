"""Validate comment markdown bodies for conversation media."""

from __future__ import annotations

import re

_IMAGE_HREF_RE = re.compile(
    r"!\[[^\]]*]\(\s*([^\s)\"']+)",
    re.MULTILINE,
)


def assert_comment_body_media_policy(body: str) -> None:
    """Reject external/data image hrefs — only attachment: / attachment:pending:."""
    text = body or ""
    for match in _IMAGE_HREF_RE.finditer(text):
        href = (match.group(1) or "").strip().lower()
        if href.startswith("attachment:"):
            continue
        if href.startswith("http://") or href.startswith("https://") or href.startswith(
            "data:"
        ):
            from requests_app.application.errors import ApplicationError

            raise ApplicationError(
                code="comment_media_forbidden",
                status_code=422,
                detail="Imagens devem usar anexos da conversa (attachment:…).",
            )

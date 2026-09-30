from __future__ import annotations

import re
import urllib.parse

_FORBIDDEN = re.compile(r'[/\\:*?"<>|\x00-\x1f\x7f]')


def sanitize_display_name(display_name: str, fallback: str) -> str:
    cleaned = _FORBIDDEN.sub("", display_name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return (cleaned[:100] or fallback)


def export_filename(display_name: str, *, revision_number: int | None = None) -> str:
    base = sanitize_display_name(
        display_name, "revision" if revision_number is not None else "model"
    )
    if revision_number is not None:
        return f"{base}-rev-{revision_number}.bpmn"
    return f"{base}.bpmn"


def content_disposition(filename: str) -> str:
    ascii_fallback = "".join(c if ord(c) < 128 else "_" for c in filename)
    utf8 = urllib.parse.quote(filename, safe="")
    return (
        f"attachment; filename=\"{ascii_fallback}\"; "
        f"filename*=UTF-8''{utf8}"
    )

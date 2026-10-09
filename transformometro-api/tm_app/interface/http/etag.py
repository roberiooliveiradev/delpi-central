"""ETag/If-Match — mesma semântica de concorrência do BPMN Modeler (G7).

O documento BPMN nativo do processo espelha o contrato `ETag "v<n>"` +
`If-Match "v<n>"`; stale → 409 (nunca lost update).
"""

from __future__ import annotations

import re

_ETAG_RE = re.compile(r'^"v(\d+)"$')


def format_etag(version: int) -> str:
    return f'"v{version}"'


def parse_if_match(header: str | None) -> tuple[str, int | None]:
    """Parse If-Match. Returns ('missing'|'malformed'|'ok', version)."""
    if header is None:
        return "missing", None
    value = header.strip()
    match = _ETAG_RE.match(value)
    if not match:
        return "malformed", None
    return "ok", int(match.group(1))

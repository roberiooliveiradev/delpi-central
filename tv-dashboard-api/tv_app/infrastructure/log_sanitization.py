"""Redact credential-bearing query parameters from log records.

Uvicorn emits the raw request target (path + query string) on both the
HTTP access log (``uvicorn.access``) and the WebSocket handshake log
(``uvicorn.error``). The public/admin realtime endpoints and media
routes legitimately accept JWTs via the ``access_token`` query
parameter (browser WebSocket clients cannot set headers), so without
sanitization the raw request line leaks credentials into logs.

Attaching this filter to the emitting loggers rewrites ``record.msg``
and ``record.args`` before any handler formats the record, keeping
redaction ahead of every sink.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping

REDACTED_QUERY_VALUE = "<redacted>"

SENSITIVE_QUERY_PARAMS: tuple[str, ...] = (
    "access_token",
    "refresh_token",
    "id_token",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "client_secret",
    "password",
    "secret",
    "code",
)

_SENSITIVE_VALUE_PATTERN = re.compile(
    r"([?&](?:" + "|".join(SENSITIVE_QUERY_PARAMS) + r")=)[^&\s\"']*",
    re.IGNORECASE,
)

UVICORN_URL_LOGGERS: tuple[str, ...] = ("uvicorn.access", "uvicorn.error")


def _scrub(value: str) -> str:
    return _SENSITIVE_VALUE_PATTERN.sub(
        r"\g<1>" + REDACTED_QUERY_VALUE,
        value,
    )


class SensitiveQueryParamsLogFilter(logging.Filter):
    """Redact sensitive query-parameter values on any log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _scrub(record.msg)
        args = record.args
        if isinstance(args, Mapping):
            record.args = {
                key: _scrub(item) if isinstance(item, str) else item
                for key, item in args.items()
            }
        elif isinstance(args, tuple):
            record.args = tuple(
                _scrub(item) if isinstance(item, str) else item for item in args
            )
        return True


def install_sensitive_query_params_log_filter() -> SensitiveQueryParamsLogFilter:
    log_filter = SensitiveQueryParamsLogFilter()
    for logger_name in UVICORN_URL_LOGGERS:
        logging.getLogger(logger_name).addFilter(log_filter)
    return log_filter

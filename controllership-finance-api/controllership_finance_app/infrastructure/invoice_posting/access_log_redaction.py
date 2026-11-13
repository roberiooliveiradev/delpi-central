"""Redige o parâmetro token em qualquer log deste processo."""

from __future__ import annotations

import logging
import re

_TOKEN_QUERY = re.compile(r"(token=)[^&\s\"']+", re.IGNORECASE)


def redact_token(value: str) -> str:
    return _TOKEN_QUERY.sub(r"\1[REDACTED]", value)


class TokenQueryRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_token(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                redact_token(item) if isinstance(item, str) else item
                for item in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                key: redact_token(item) if isinstance(item, str) else item
                for key, item in record.args.items()
            }
        return True


def install_token_redaction_filter() -> None:
    redaction = TokenQueryRedactionFilter()
    for name in ("", "uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        if not any(isinstance(item, TokenQueryRedactionFilter) for item in logger.filters):
            logger.addFilter(redaction)

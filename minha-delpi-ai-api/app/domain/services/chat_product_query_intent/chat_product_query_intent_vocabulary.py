"""Vocabulário — intenção de consulta de produto (padrões via content loader)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)


class _LazyPattern:
    def __init__(self, key: str) -> None:
        self._key = key

    def __get__(self, _obj: Any, _owner: type | None = None) -> re.Pattern[str]:
        return ChatProductQueryIntentContentService.compile_pattern(self._key)


class ChatProductQueryIntentVocabulary:
    ZERO_RECORDS_RE = _LazyPattern("zeroRecords")
    PRODUCT_CODE_RE = _LazyPattern("productCode")
    SPECIFICATION_TOKEN_RE = _LazyPattern("specificationToken")
    DATE_TOKEN_RE = _LazyPattern("dateToken")
    CALENDAR_YEAR_RE = _LazyPattern("calendarYear")
    EXAMPLE_CODE_PREFIX_RE = _LazyPattern("exampleCodePrefix")
    DECIMAL_SCALAR_TOKEN_RE = _LazyPattern("decimalScalarToken")

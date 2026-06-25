"""Vocabulário — intenção de consulta de produto."""

from __future__ import annotations

import re

class ChatProductQueryIntentVocabulary:
    ZERO_RECORDS_RE = re.compile(r":\s*0 registro\(s\)\.?$", re.IGNORECASE)
    PRODUCT_CODE_RE = re.compile(
        r"\b(?:\d[\d.\-/]{2,}\d|\d{4,})\b",
    )
    SPECIFICATION_TOKEN_RE = re.compile(
        r"^\d+[,.]\d+[-xX]\d+[,.]\d+|\d+[,.]\d+\s*[-xX]\s*\d+[,.]\d+",
        re.IGNORECASE,
    )
    DATE_TOKEN_RE = re.compile(
        r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$",
        re.IGNORECASE,
    )
    CALENDAR_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
    EXAMPLE_CODE_PREFIX_RE = re.compile(
        r"(?:\bex\.?\s*:?|\bexemplo\s*:?|\binforme\s+(?:o\s+)?(?:c[óo]digo|codigo)|\bpor\s+exemplo)\s*$",
        re.IGNORECASE,
    )

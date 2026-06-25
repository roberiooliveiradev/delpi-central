from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "pac_evidence_tag_vocabulary.json"


class PacEvidenceTagVocabularyContentService:
    @classmethod
    @lru_cache(maxsize=1)
    def bundle(cls) -> dict[str, Any]:
        payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("pac_evidence_tag_vocabulary.json inválido")
        return payload

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        limits = cls.bundle().get("limits") or {}
        return int(limits.get(key, default))

    @classmethod
    def product_code_pattern(cls) -> re.Pattern[str]:
        patterns = cls.bundle().get("patterns") or {}
        raw = str(patterns.get("productCode") or r"\b90\d{6}\b")
        return re.compile(raw, re.IGNORECASE)

    @classmethod
    def marker_groups(cls, section: str) -> list[dict[str, Any]]:
        rows = cls.bundle().get(section) or []
        return [row for row in rows if isinstance(row, dict)]

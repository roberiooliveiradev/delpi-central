from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "pac_knowledge_graph.json"


class PacKnowledgeGraphContentService:
    @classmethod
    @lru_cache(maxsize=1)
    def bundle(cls) -> dict[str, Any]:
        payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("pac_knowledge_graph.json inválido")
        return payload

    @classmethod
    def limit_int(cls, key: str, default: int) -> int:
        limits = cls.bundle().get("limits") or {}
        return int(limits.get(key, default))
